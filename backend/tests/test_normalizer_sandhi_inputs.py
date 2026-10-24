# -*- coding: utf-8 -*-
"""
Extra normalizer tests that matter for sandhi. Run them against YOUR SanskritNormalizer:
if one fails, the normalizer is deleting a character the sandhi engine needs.
"""
import unicodedata

import pytest

from app.core.normalizer import SanskritNormalizer

N = SanskritNormalizer.normalize


@pytest.mark.parametrize("text", [
    "राजपुत्रोऽस्मि",        # avagraha ऽ  (U+093D) marks the dropped 'a' in aH + a -> o'
    "सोऽवदत्", "कोऽपि",
    "वनं गच्छति",            # anusvara
    "रामः गच्छति",           # visarga
    "आसीत् शोभावती नाम",      # virama at word end
    "वृत्त्यर्थमागतो",        # conjuncts
])
def test_sandhi_relevant_characters_survive(text):
    assert N(text) == text


def test_normalize_is_idempotent():
    s = "  तत्र   शूद्रको नाम\u200d महीपतिः प्रतिवसति स्म।  "
    assert N(N(s)) == N(s)


def test_nfc_really_composes_a_decomposable_devanagari_letter():
    # U+0958 (क़) decomposes to U+0915 U+093C; most Devanagari letters do NOT decompose,
    # so the original NFC test (using 'बालकः') passes even if normalize() does nothing.
    assert N("\u0958") == unicodedata.normalize("NFC", "\u0958")
    assert unicodedata.is_normalized("NFC", N("क\u093c"))


def test_engine_gives_same_words_with_or_without_prenormalisation():
    pytest.importorskip("sanskrit_parser")
    from app.services.sandhi_engine import segment_sanskrit
    raw = "  रामो   वनं\tगच्छति।  "
    assert segment_sanskrit(raw)["words"] == segment_sanskrit(N(raw))["words"] == ["रामः", "वनम्", "गच्छति"]
