# -*- coding: utf-8 -*-
"""
Tests for the VākyaSetu sandhi engine (Mayank's module).

Three layers:
  1. phonetics / rule classification  - pure Python, always runs
  2. engine behaviour on sentences    - needs sanskrit_parser (skipped, loudly, if it is not installed)
  3. failure behaviour                - degraded backend must say so, never guess silently

Principles: no test mentions a sentence only because the engine was written to pass it, and every
"no phantom rule" property is tested explicitly (that was the old module's biggest lie).
"""
import pytest

from app.services.sandhi_engine import phonetics as ph
from app.services.sandhi_engine.engine import SandhiEngine, LexiconBackend, segment_sanskrit


# ----------------------------------------------------------------------------- 1. phonetics
def test_pausa_forms():
    assert ph.pausa("rAmas") == "rAmaH"
    assert ph.pausa("punar") == "punaH"
    assert ph.pausa("etad") == "etat"


def test_tokenisation_keeps_avagraha_and_strips_punctuation():
    assert ph.split_tokens("भोः प्रतिहार! राजपुत्रोऽस्मि, गच्छति।") == ["भोः", "प्रतिहार", "राजपुत्रोऽस्मि", "गच्छति"]


@pytest.mark.parametrize("left,right,name", [
    ("rAmas", "vanam", "उत्वम्"),                    # aH + voiced -> o
    ("na", "etat", "वृद्धि"),                         # a + e -> ai
    ("yadi", "api", "यण्"),                           # i + a -> ya
    ("deva", "Alayam", "दीर्घ"),                      # a + A -> A
    ("sUrya", "udayas", "गुण"),                       # a + u -> o
    ("tasmAt", "naya", "अनुनासिक"),                   # t + n -> n n
    ("kasmAt", "api", "जश्त्व"),                      # t + vowel -> d
    ("guruH", "viSNuH", "रुत्वम्"),                   # uH + voiced -> r
])
def test_rule_classification(left, right, name):
    rule = ph.classify_junction(left, right)
    assert rule is not None and name in rule.rule_name


def test_no_rule_when_nothing_fuses():
    assert ph.classify_junction("rAmas", "pustakam") is None          # visarga stays before p
    assert ph.classify_junction("vfttyarTam", "Agatas") is None       # m + vowel just joined in writing


def test_surface_variants_only_when_context_allows():
    assert [v.text for v in ph.surface_variants("rAmo", "v")] == ["rAmo", "rAmaH"]
    assert [v.text for v in ph.surface_variants("rAmo", None)] == ["rAmo"]     # last word: nothing to undo
    assert [v.text for v in ph.surface_variants("rAmo", "p")] == ["rAmo"]      # unvoiced next sound: o is not from aH


# ----------------------------------------------------------------------------- 2. engine
@pytest.fixture(scope="module")
def engine():
    pytest.importorskip("sanskrit_parser", reason="pip install sanskrit_parser gensim sentencepiece")
    eng = SandhiEngine(LexiconBackend.shared())
    if eng.degraded:
        pytest.skip(f"backend unavailable: {eng.backend.error}")
    return eng


def words(engine, text):
    return engine.split(text).split_words


def test_schema_contract():
    pytest.importorskip("sanskrit_parser")
    res = segment_sanskrit("रामो वनं गच्छति।")
    for key in ("input", "normalized", "status", "words", "tokens", "candidates", "rules",
                "validation", "warnings", "engine"):
        assert key in res
    assert res["status"] in ("resolved", "ambiguous", "unsplit")
    cand = res["candidates"][0]
    for key in ("words", "surface_tokens", "reconstructed_words", "confidence", "rules"):
        assert key in cand
    assert res["words"] == cand["words"]
    tok = res["tokens"][0]
    for key in ("surface", "words", "status", "confidence", "evidence", "junctions", "alternatives", "warnings"):
        assert key in tok


def test_no_phantom_rules_when_words_are_already_separate(engine):
    res = engine.split("रामः गच्छति")
    assert res.split_words == ["रामः", "गच्छति"]
    assert res.rules == []                       # nothing was fused, so no sandhi rule may be reported


def test_no_phantom_rules_on_long_unfused_sentence(engine):
    res = engine.split("तत्र शूद्रकः नाम महीपतिः प्रतिवसति स्म")
    assert res.rules == []


@pytest.mark.parametrize("text,expected", [
    ("रामो वनं गच्छति", ["रामः", "वनम्", "गच्छति"]),               # visarga-u across a space + anusvara spelling
    ("बालकस्तत्र गच्छति", ["बालकः", "तत्र", "गच्छति"]),             # visarga -> s
    ("गुरुर्ब्रह्मा", ["गुरुः", "ब्रह्मा"]),                          # visarga -> r
    ("सैव बालिका", ["सा", "एव", "बालिका"]),                          # vowel (vṛddhi)
    ("इत्यब्रवीत्", ["इति", "अब्रवीत्"]),                             # yaṇ
    ("तन्नास्ति", ["तत्", "न", "अस्ति"]),                             # consonant + vowel in one token
    ("नैतच्छक्यम्", ["न", "एतत्", "शक्यम्"]),                         # three words in one token
])
def test_fused_tokens_are_split(engine, text, expected):
    assert words(engine, text) == expected


@pytest.mark.parametrize("text", [
    "बालः पठति", "सा गृहं गच्छति", "छात्राः पठन्ति", "महापराक्रमी राजपुत्रः", "गच्छति", "नगरम् आगच्छति",
])
def test_intact_words_are_not_over_segmented(engine, text):
    out = words(engine, text)
    assert len(out) == len(text.split())                  # one word per written token, no invented splits


def test_prefixed_verb_and_plain_compound_stay_whole(engine):
    res = engine.split("राजा प्रणमति महापराक्रमी")
    assert res.split_words == ["राजा", "प्रणमति", "महापराक्रमी"]
    comp = {t.surface: t for t in res.tokens}
    assert comp["प्रणमति"].status == "compound" and comp["प्रणमति"].members          # parts available for the UI
    assert comp["महापराक्रमी"].status == "compound"


def test_rules_are_attached_to_real_junctions_only(engine):
    res = engine.split("अथैकदा")
    assert res.split_words == ["अथ", "एकदा"]
    assert [r["rule_name"] for r in res.rules] == ["वृद्धिसन्धिः"]
    assert res.rules[0]["sutra"].startswith("वृद्धिरेचि")


def test_unknown_word_is_flagged_not_guessed(engine):
    res = engine.split("क्षृक्षप्त")
    tok = res.tokens[0]
    assert tok.status in ("unattested", "resolved")       # never a confident invented split
    if tok.status == "unattested":
        assert tok.warnings and tok.confidence <= 0.3


def test_empty_and_punctuation_only(engine):
    for text in ("", "   ", "।॥,"):
        res = engine.split(text)
        assert res.split_words == [] and res.status == "unsplit"


def test_non_devanagari_is_passed_through(engine):
    res = engine.split("रामः 2026 gacchati")
    assert res.split_words[1:] == ["2026", "gacchati"]


def test_alternatives_are_exposed_for_lexicalised_words(engine):
    tok = engine.analyze_token("देवालयं")
    assert tok.words == ["देव", "आलयम्"]
    assert any(alt == ["देवालयम्"] for alt in tok.alternatives)        # student can see the 'single word' reading


# ----------------------------------------------------------------------------- 3. failure behaviour
class _DeadBackend:
    ok = False
    error = "ImportError: simulated"
    lm_ranking = False


def test_degraded_backend_is_reported_loudly():
    eng = SandhiEngine(_DeadBackend())
    res = eng.split("रामो वनं गच्छति")
    assert res.degraded is True
    assert any("DEGRADED" in w for w in res.warnings)
    assert all(t.status == "unavailable" for t in res.tokens)
    assert all(t.confidence == 0.0 for t in res.tokens)           # no fake confidence
    assert res.rules == []                                          # and no invented rules
