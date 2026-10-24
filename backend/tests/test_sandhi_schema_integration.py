# -*- coding: utf-8 -*-
"""The sandhi engine's output must always be a valid AnalyzeResponse payload (even when degraded)."""
import pytest

pytest.importorskip("sanskrit_parser", reason="pip install sanskrit_parser gensim sentencepiece")

from app.models.schemas import AnalyzeResponse
from app.services.sandhi import as_legacy_schema, get_sandhi_service, health, to_analyze_fields
from app.services.sandhi_engine.engine import SandhiEngine


def build(fields):
    return AnalyzeResponse(original_text="x", normalized_text="x", translation="", morphology=[],
                           processing_time_ms=0.0, **fields)


@pytest.mark.parametrize("text", [
    "रामो वनं गच्छति।", "तत्र शूद्रको नाम महापराक्रमी प्रतिवसति स्म।", "नैतच्छक्यम्!", "", "।॥",
])
def test_result_validates_as_analyze_response(text):
    res = get_sandhi_service().split(text)
    resp = build(to_analyze_fields(res))
    assert resp.sandhi_splits == res.split_words
    assert all(0.0 <= o.confidence <= 1.0 for o in resp.all_sandhi_options)


def test_rules_and_token_details_survive_the_conversion():
    resp = build(to_analyze_fields(get_sandhi_service().split("अथैकदा राजा")))
    assert [r.rule_name for r in resp.sandhi_rules] == ["वृद्धिसन्धिः"]
    assert resp.sandhi_rules[0].explanation_en
    tok = resp.sandhi_tokens[0]
    assert tok.words == ["अथ", "एकदा"] and tok.junctions[0].rule.sutra.startswith("वृद्धिरेचि")


def test_compound_members_exposed_for_the_compound_module():
    resp = build(to_analyze_fields(get_sandhi_service().split("महापराक्रमी")))
    tok = resp.sandhi_tokens[0]
    assert tok.status == "compound" and tok.words == ["महापराक्रमी"] and tok.compound_members


def test_legacy_adapter():
    words, options, rules = as_legacy_schema(get_sandhi_service().split("सैव बालिका"))
    assert words == ["सा", "एव", "बालिका"] and options and rules


class _Dead:
    ok = False
    error = "simulated outage"
    lm_ranking = False


def test_degraded_result_still_validates_and_is_flagged():
    resp = build(to_analyze_fields(SandhiEngine(_Dead()).split("रामो वनं")))
    assert resp.sandhi_degraded is True
    assert resp.sandhi_warnings and "DEGRADED" in resp.sandhi_warnings[0]
    assert all(t.confidence == 0.0 and t.status == "unavailable" for t in resp.sandhi_tokens)


def test_overlong_token_is_not_searched():
    import time
    t0 = time.time()
    res = get_sandhi_service().split("महापराक्रमीनानाशास्त्रवित्पूतचरित्रमहीपतिप्रतिवसतिस्मराजद्वारमुपागच्छत्")
    assert time.time() - t0 < 2.0                         # no multi-second search
    assert res.tokens[0].status == "unattested" and res.tokens[0].warnings


def test_health_entry():
    assert health()["sandhi"].startswith("ok")
