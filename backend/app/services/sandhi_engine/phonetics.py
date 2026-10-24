# -*- coding: utf-8 -*-
"""
Phonetic helpers + sandhi-rule classification for the VākyaSetu sandhi engine.

Everything here works on SLP1 (a one-character-per-phoneme transliteration), which makes
phonological tests trivial:  'a'=अ 'A'=आ 'H'=visarga 'M'=anusvāra 'S'=श 'z'=ष 'C'=छ ...

Design rule: a sandhi *rule* is only ever reported for a junction that really exists
(a place where the engine actually undid a fusion). Nothing in this module is applied
to word pairs that are simply written next to each other.
"""
from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass
from typing import List, Optional, Tuple

from indic_transliteration import sanscript

SLP1 = sanscript.SLP1
DEVA = sanscript.DEVANAGARI

VOWELS = set("aAiIuUfFxXeEoO")
# voiced consonants incl. nasals, semivowels and h  (the 'haś' set of Pāṇini)
VOICED = set("gGNjJYqQRdDnbBmyrlvh")
SHORT_VOWELS = set("aiufx")

_EDGE_PUNCT = " \t\r\n,.;:!?()[]{}\"'“”‘’।॥-–—|…"
_ZERO_WIDTH = dict.fromkeys(map(ord, "\u200b\u200c\u200d\ufeff\u2060"), None)


# --------------------------------------------------------------------------- #
# normalisation / transliteration
# --------------------------------------------------------------------------- #
def normalize_text(text: str) -> str:
    """NFC, drop zero-width characters, unify whitespace. Keeps avagraha (ऽ)."""
    text = unicodedata.normalize("NFC", text or "").translate(_ZERO_WIDTH)
    return re.sub(r"\s+", " ", text).strip()


def split_tokens(text: str) -> List[str]:
    """Whitespace tokens with edge punctuation removed (internal avagraha kept)."""
    out = []
    for tok in normalize_text(text).split(" "):
        tok = tok.strip(_EDGE_PUNCT)
        if tok:
            out.append(tok)
    return out


def to_slp1(dev: str) -> str:
    return sanscript.transliterate(dev, DEVA, SLP1)


def to_devanagari(slp1: str) -> str:
    return sanscript.transliterate(slp1, SLP1, DEVA)


def first_sound(slp1: str) -> Optional[str]:
    slp1 = slp1.lstrip("'")
    return slp1[0] if slp1 else None


# --------------------------------------------------------------------------- #
# pausa (citation) form of a word that sits inside a sandhi graph
# --------------------------------------------------------------------------- #
_PAUSA = {"s": "H", "r": "H", "d": "t", "g": "k", "b": "p", "q": "w"}


def pausa(piece: str) -> str:
    """
    Word-final form a student would see in a dictionary/citation:
    rAmas -> rAmaH, punar -> punaH, etad -> etat, vAg -> vAk, ...
    (sanskrit_parser works with 's' / voiced finals internally.)
    """
    if not piece:
        return piece
    return piece[:-1] + _PAUSA.get(piece[-1], piece[-1])


def to_piece_form(slp1: str) -> str:
    """Inverse direction used for lexicon lookups: final visarga -> 's'."""
    return slp1[:-1] + "s" if slp1.endswith("H") else slp1


# --------------------------------------------------------------------------- #
# word-final alternations that happen across a space ("rAmo vanam")
# --------------------------------------------------------------------------- #
@dataclass(frozen=True)
class SurfaceVariant:
    text: str                 # SLP1 string to analyse (what the word was *before* sandhi)
    alternation: Optional[str]  # None = surface as written; otherwise a label


def surface_variants(token: str, next_initial: Optional[str]) -> List[SurfaceVariant]:
    """
    Undo *external* final-sandhi so that the lexicon can recognise the word.

        rAmo   (+ voiced)       -> rAmaH
        devA   (+ voiced/vowel) -> devAH       (only considered when 'devA' is not a word)
        gurur  (+ voiced/vowel) -> guruH
        vanaM                   -> vanam       (always; not a sandhi change, a spelling norm)

    The caller decides which variant wins; this function only proposes them.
    """
    out: List[SurfaceVariant] = []
    base = token
    if base.endswith("M"):                       # spelling normalisation, not an alternation
        base = base[:-1] + "m"
    out.append(SurfaceVariant(base, None))

    if next_initial is None or len(base) < 3:
        return out
    voiced_next = next_initial in VOICED
    vowel_next = next_initial in VOWELS

    if base.endswith("o") and voiced_next:                     # aH + voiced -> o
        out.append(SurfaceVariant(base[:-1] + "aH", "visarga_u"))
    if base.endswith("A") and (voiced_next or vowel_next):     # AH + voiced/vowel -> A
        out.append(SurfaceVariant(base + "H", "visarga_drop"))
    if base[-2:] in ("ir", "ur", "er", "or") and (voiced_next or vowel_next):   # iH/uH -> ir/ur
        out.append(SurfaceVariant(base[:-1] + "H", "visarga_r"))
    return out


# --------------------------------------------------------------------------- #
# rule classification for a REAL junction  (left, right are SLP1, sandhi-form)
# --------------------------------------------------------------------------- #
@dataclass
class SandhiRule:
    rule_name: str
    sutra: str
    sandhi_type: str      # स्वरसन्धिः / विसर्गसन्धिः / व्यञ्जनसन्धिः
    explanation: str      # Hindi, for students
    explanation_en: str = ""


def _R(name, sutra, typ, hi, en):
    return SandhiRule(name, sutra, typ, hi, en)


def classify_junction(left: str, right: str) -> Optional[SandhiRule]:
    """
    Name the Pāṇinian rule responsible for fusing `left` and `right`.
    Returns None when the pair would simply be written together without change.
    `left` is in sanskrit_parser sandhi-form (visarga shown as 's'/'r').
    """
    if not left or not right:
        return None
    lc, rc = left[-1], first_sound(right)
    if rc is None:
        return None
    prev = left[-2] if len(left) > 1 else ""

    # ---- 1. vowel + vowel -------------------------------------------------- #
    if lc in VOWELS and rc in VOWELS:
        same = (lc.lower() == rc.lower() and lc in "aAiIuUfF") or (lc in "aA" and rc in "aA")
        if same or (lc in "iI" and rc in "iI") or (lc in "uU" and rc in "uU") or (lc in "fF" and rc in "fF"):
            return _R("दीर्घसन्धिः", "अकः सवर्णे दीर्घः (६.१.१०१)", "स्वरसन्धिः",
                      "सवर्ण स्वर परे होने पर दोनों मिलकर दीर्घ स्वर हो जाते हैं।",
                      "Two similar vowels merge into one long vowel.")
        if lc in "aA" and rc in "iIuUfFx":
            return _R("गुणसन्धिः", "आद्गुणः (६.१.८७)", "स्वरसन्धिः",
                      "अ/आ के बाद इ/उ/ऋ आने पर क्रमशः ए/ओ/अर् हो जाता है।",
                      "a/ā + i/u/ṛ become e/o/ar (guṇa).")
        if lc in "aA" and rc in "eEoO":
            return _R("वृद्धिसन्धिः", "वृद्धिरेचि (६.१.८८)", "स्वरसन्धिः",
                      "अ/आ के बाद ए/ऐ/ओ/औ आने पर ऐ/औ हो जाता है।",
                      "a/ā + e/o/ai/au become ai/au (vṛddhi).")
        if lc in "iIuUfF":
            return _R("यण्सन्धिः", "इको यणचि (६.१.७७)", "स्वरसन्धिः",
                      "इ/उ/ऋ के बाद असमान स्वर आने पर वे य्/व्/र् हो जाते हैं।",
                      "i/u/ṛ before a different vowel become y/v/r (yaṇ).")
        if lc in "eo" and rc == "a":
            return _R("पूर्वरूपसन्धिः", "एङः पदान्तादति (६.१.१०९)", "स्वरसन्धिः",
                      "पदान्त ए/ओ के बाद ह्रस्व अ आने पर अ का लोप होकर अवग्रह (ऽ) लगता है।",
                      "Final e/o + a: the a disappears (avagraha ऽ).")
        if lc in "eEoO":
            return _R("अयादिसन्धिः", "एचोऽयवायावः (६.१.७८)", "स्वरसन्धिः",
                      "ए/ऐ/ओ/औ के बाद स्वर आने पर क्रमशः अय्/आय्/अव्/आव् हो जाता है।",
                      "e/ai/o/au before a vowel become ay/āy/av/āv (ayādi).")

    # ---- 2. visarga family  (sanskrit_parser shows visarga as s / r) ------- #
    if lc in "sHr":
        if prev == "a" and rc == "a":
            return _R("विसर्गसन्धिः (उत्वम् + पूर्वरूपम्)", "अतो रोरप्लुतादप्लुते (६.१.११३)", "विसर्गसन्धिः",
                      "अ के बाद विसर्ग और आगे अ हो तो विसर्ग का उ होकर ओ बनता है और अ का अवग्रह (ऽ) हो जाता है।",
                      "aḥ + a → o + avagraha.")
        if prev == "a" and rc in VOICED:
            return _R("विसर्गसन्धिः (उत्वम्)", "हशि च (६.१.११४)", "विसर्गसन्धिः",
                      "ह्रस्व अ के बाद विसर्ग हो और आगे घोष व्यंजन हो, तो अः का ओ हो जाता है।",
                      "aḥ before a voiced consonant becomes o.")
        if prev in "aA" and rc in VOWELS:
            return _R("विसर्गसन्धिः (लोपः)", "भोभगोअघोअपूर्वस्य योऽशि (८.३.१७) / लोपः शाकल्यस्य (८.३.१९)", "विसर्गसन्धिः",
                      "अः/आः के बाद अ से भिन्न स्वर आने पर विसर्ग का लोप हो जाता है।",
                      "aḥ/āḥ before a vowel: the visarga drops.")
        if prev == "A" and rc in VOICED:
            return _R("विसर्गसन्धिः (लोपः)", "भोभगोअघोअपूर्वस्य योऽशि (८.३.१७)", "विसर्गसन्धिः",
                      "आः के बाद घोष वर्ण आने पर विसर्ग का लोप हो जाता है।",
                      "āḥ before a voiced sound: the visarga drops.")
        if prev and prev not in "aA" and (rc in VOWELS or rc in VOICED):
            return _R("विसर्गसन्धिः (रुत्वम्)", "ससजुषो रुः (८.२.६६)", "विसर्गसन्धिः",
                      "अ/आ से भिन्न स्वर के बाद विसर्ग हो और आगे स्वर या घोष वर्ण हो, तो विसर्ग का र् हो जाता है।",
                      "Visarga after i/u/e/o… before a vowel or voiced sound becomes r.")
        if rc in "cC":
            return _R("विसर्गसन्धिः (श्चुत्वम्)", "विसर्जनीयस्य सः (८.३.३४) + स्तोः श्चुना श्चुः (८.४.४०)", "विसर्गसन्धिः",
                      "च/छ परे होने पर विसर्ग श् हो जाता है।", "Visarga before c/ch becomes ś.")
        if rc in "wW":
            return _R("विसर्गसन्धिः (ष्टुत्वम्)", "विसर्जनीयस्य सः (८.३.३४) + ष्टुना ष्टुः (८.४.४१)", "विसर्गसन्धिः",
                      "ट/ठ परे होने पर विसर्ग ष् हो जाता है।", "Visarga before ṭ/ṭh becomes ṣ.")
        if rc in "tT":
            return _R("विसर्गसन्धिः (सत्वम्)", "विसर्जनीयस्य सः (८.३.३४)", "विसर्गसन्धिः",
                      "त/थ परे होने पर विसर्ग स् हो जाता है।", "Visarga before t/th becomes s.")
        return None  # visarga stays before k/p/ś/ṣ/s: written together, no change

    # ---- 3. consonant finals ----------------------------------------------- #
    if lc in "tdn" and rc == "S":
        return _R("श्चुत्वसन्धिः + छत्वम्", "स्तोः श्चुना श्चुः (८.४.४०) / शश्छोऽटि (८.४.६३)", "व्यञ्जनसन्धिः",
                  "त्/द्/न् के बाद श् आने पर च्/ज्/ञ् होता है और श् का छ् हो जाता है।",
                  "t/d/n before ś → c/j/ñ, and ś often becomes ch.")
    if lc in "tdn" and rc in "cCjJY":
        return _R("श्चुत्वसन्धिः", "स्तोः श्चुना श्चुः (८.४.४०)", "व्यञ्जनसन्धिः",
                  "त-वर्ग के बाद श/च-वर्ग आने पर त-वर्ग का च-वर्ग हो जाता है।", "Dental becomes palatal near palatal.")
    if lc in "tdn" and rc in "zwWqQR":
        return _R("ष्टुत्वसन्धिः", "ष्टुना ष्टुः (८.४.४१)", "व्यञ्जनसन्धिः",
                  "त-वर्ग के बाद ष/ट-वर्ग आने पर त-वर्ग का ट-वर्ग हो जाता है।", "Dental becomes retroflex near retroflex.")
    if lc in "td" and rc == "l":
        return _R("परसवर्णसन्धिः (ल्)", "तोर्लि (८.४.६०)", "व्यञ्जनसन्धिः",
                  "त्/द् के बाद ल् आने पर वह ल् हो जाता है।", "t/d before l becomes l.")
    if lc in "kcwtp" and rc in "NYRnm":
        return _R("अनुनासिकसन्धिः", "यरोऽनुनासिकेऽनुनासिको वा (८.४.४५)", "व्यञ्जनसन्धिः",
                  "पदान्त स्पर्श के बाद अनुनासिक आने पर वह अपने वर्ग का अनुनासिक हो जाता है।",
                  "Final stop before a nasal becomes that class's nasal.")
    if lc in "kcwtp" and (rc in VOWELS or rc in VOICED):
        return _R("जश्त्वसन्धिः", "झलां जशोऽन्ते (८.२.३९)", "व्यञ्जनसन्धिः",
                  "पदान्त वर्गीय प्रथम वर्ण के बाद स्वर/घोष वर्ण आने पर वह अपने वर्ग का तृतीय वर्ण हो जाता है।",
                  "Final voiceless stop becomes voiced before a vowel/voiced sound.")
    if lc in "Nn" and prev in SHORT_VOWELS and rc in VOWELS:
        return _R("ङमुडागमः", "ङमो ह्रस्वादचि ङमुण्नित्यम् (८.३.३२)", "व्यञ्जनसन्धिः",
                  "ह्रस्व स्वर के बाद पदान्त ङ्/न् और आगे स्वर हो तो ङ्/न् द्वित्व हो जाता है।",
                  "Final ṅ/n after a short vowel doubles before a vowel.")
    if lc == "m" and rc not in VOWELS and rc not in "mMH'":
        return _R("अनुस्वारसन्धिः", "मोऽनुस्वारः (८.३.२३)", "व्यञ्जनसन्धिः",
                  "पदान्त म् के बाद व्यंजन आने पर म् का अनुस्वार हो जाता है।", "Final m before a consonant becomes anusvāra.")
    return None
