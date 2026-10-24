# -*- coding: utf-8 -*-
"""
Builds ml/data/sandhi_gold.jsonl (token-aligned gold). Edit the tables below, re-run, commit the JSONL.

Annotation guideline v1  (write this in the report)
---------------------------------------------------
* A written token (whitespace-delimited, edge punctuation removed) maps to one or more WORDS in
  citation (pausa) form:  रामो -> रामः,  वनं -> वनम्,  देशाद् -> देशात्.
* SPLIT a token only where sandhi really changed the letters, or where two words are written together
  (अर्थम् + आगतः).  This includes sandhi inside compounds:  सूर्योदयः -> सूर्य + उदयः.
* Do NOT split plain compounds with no sandhi (महापराक्रमी, राजपुत्रः, महीपतिः) or an upasarga + finite verb
  (प्रणमति, उपागच्छत्): keep them whole.
* `type` is the main phenomenon in the token: none | normalize | visarga | vowel | consonant | multi |
  boundary | plain-compound | prefix-verb.
* split: "bench" = the original 15 sentences (used while developing; do not quote as held-out),
         "dev"   = extra examples written for tuning,
         "test"  = HELD-OUT. Annotate >= 50 real NCERT sentences with page numbers, never tune on them.
"""
import json, os, sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "backend", "app", "services"))
from sandhi_engine.phonetics import split_tokens

N, NORM, VIS, VOW, CON, MULTI, BND, PC, PV = ("none", "normalize", "visarga", "vowel", "consonant",
                                              "multi", "boundary", "plain-compound", "prefix-verb")
def t(words, typ=N): return (words.split("+"), typ)

BENCH = [  # (id, sentence, source, tokens, note)
 ("NCERT-01", "रामो वनं गच्छति।", "CBSE Class 6 Ruchira", [t("रामः", VIS), t("वनम्", NORM), t("गच्छति")], ""),
 ("NCERT-02", "आसीत् शोभावती नाम काचन नगरी।", "Hitopadesha / NCERT Shemushi", [t("आसीत्"), t("शोभावती"), t("नाम"), t("काचन"), t("नगरी")], ""),
 ("NCERT-03", "तत्र शूद्रको नाम महापराक्रमी नानाशास्त्रवित् पूतचरित्रः महीपतिः प्रतिवसति स्म।", "Hitopadesha / NCERT Shemushi",
  [t("तत्र"), t("शूद्रकः", VIS), t("नाम"), t("महापराक्रमी", PC), t("नानाशास्त्रवित्", PC), t("पूतचरित्रः", PC), t("महीपतिः", PC), t("प्रतिवसति", PV), t("स्म")], ""),
 ("NCERT-04", "अथैकदा वीरवरनामा राजपुत्रः वृत्त्यर्थं कस्मादपि देशाद् राजद्वारमुपागच्छत्।", "Hitopadesha / NCERT Shemushi",
  [t("अथ+एकदा", VOW), t("वीरवरनामा", PC), t("राजपुत्रः", PC), t("वृत्ति+अर्थम्", VOW), t("कस्मात्+अपि", CON), t("देशात्", NORM), t("राजद्वारम्+उपागच्छत्", BND)],
  "GOLD CHANGED vs original file: वृत्त्यर्थं was kept whole; guideline v1 splits it (same rule the file already applied to देवालयं/सूर्योदयः)."),
 ("NCERT-05", "भोः प्रतिहार! वृत्त्यर्थमागतो राजपुत्रोऽस्मि, तस्मान्नय मां स्वामिनः समीपम्।", "Hitopadesha / NCERT Shemushi",
  [t("भोः"), t("प्रतिहार"), t("वृत्ति+अर्थम्+आगतः", MULTI), t("राजपुत्रः+अस्मि", VIS), t("तस्मात्+नय", CON), t("माम्", NORM), t("स्वामिनः"), t("समीपम्")],
  "GOLD CHANGED: वृत्त्यर्थमागतो -> वृत्ति+अर्थम्+आगतः (guideline v1)."),
 ("NCERT-06", "इमौ बाहू, एष खड्गश्च।", "Hitopadesha / NCERT Shemushi", [t("इमौ"), t("बाहू"), t("एष"), t("खड्गः+च", VIS)], ""),
 ("NCERT-07", "नैतच्छक्यम्!", "Hitopadesha / NCERT Shemushi", [t("न+एतत्+शक्यम्", MULTI)], ""),
 ("NCERT-08", "यद्यपि सः सदा सत्यं वदति।", "CBSE Class 7 Ruchira (unverified)", [t("यदि+अपि", VOW), t("सः"), t("सदा"), t("सत्यम्", NORM), t("वदति")], ""),
 ("NCERT-09", "देवालयं गत्वा सः गुरुं प्रणमति।", "CBSE Class 7 Ruchira (unverified)", [t("देव+आलयम्", VOW), t("गत्वा"), t("सः"), t("गुरुम्", NORM), t("प्रणमति", PV)], ""),
 ("NCERT-10", "सूर्योदयः प्रभाते भवति।", "CBSE Class 6 Ruchira (unverified)", [t("सूर्य+उदयः", VOW), t("प्रभाते"), t("भवति")], ""),
 ("NCERT-11", "बालकः विद्यालयं गच्छति।", "CBSE Class 6 Ruchira (unverified)", [t("बालकः"), t("विद्यालयम्", NORM), t("गच्छति")], ""),
 ("NCERT-12", "सा पुस्तकं पठति।", "CBSE Class 6 Ruchira (unverified)", [t("सा"), t("पुस्तकम्", NORM), t("पठति")], ""),
 ("NCERT-13", "अहं जलं पिबामि।", "CBSE Class 6 Ruchira (unverified)", [t("अहम्", NORM), t("जलम्", NORM), t("पिबामि")], ""),
 ("NCERT-14", "सोऽवदत् यत् तत्र कोऽपि नास्ति।", "Panchatantra / NCERT (unverified)",
  [t("सः+अवदत्", VIS), t("यत्"), t("तत्र"), t("कः+अपि", VIS), t("न+अस्ति", VOW)], ""),
 ("NCERT-15", "सदाचारः एव परमो धर्मः।", "Subhashitani / NCERT (unverified)", [t("सत्+आचारः", CON), t("एव"), t("परमः", VIS), t("धर्मः")], ""),
]

DEV = [  # written for tuning; unseen by the engine's design (no rule mentions them)
 ("DEV-01", "बालकस्तत्र गच्छति", [t("बालकः+तत्र", VIS), t("गच्छति")]),
 ("DEV-02", "रामश्च लक्ष्मणश्च वनं गतौ", [t("रामः+च", VIS), t("लक्ष्मणः+च", VIS), t("वनम्", NORM), t("गतौ")]),
 ("DEV-03", "गुरुर्ब्रह्मा गुरुर्विष्णुः", [t("गुरुः+ब्रह्मा", VIS), t("गुरुः+विष्णुः", VIS)]),
 ("DEV-04", "नरो वदति", [t("नरः", VIS), t("वदति")]),
 ("DEV-05", "सैव बालिका", [t("सा+एव", VOW), t("बालिका")]),
 ("DEV-06", "तथैव सः गच्छति", [t("तथा+एव", VOW), t("सः"), t("गच्छति")]),
 ("DEV-07", "इत्यब्रवीत्", [t("इति+अब्रवीत्", VOW)]),
 ("DEV-08", "अत्रैव तिष्ठति", [t("अत्र+एव", VOW), t("तिष्ठति")]),
 ("DEV-09", "सोऽपि पठति", [t("सः+अपि", VIS), t("पठति")]),
 ("DEV-10", "तन्नास्ति", [t("तत्+न+अस्ति", MULTI)]),
 ("DEV-11", "कुतोऽपि जलं नास्ति", [t("कुतः+अपि", VIS), t("जलम्", NORM), t("न+अस्ति", VOW)]),
 ("DEV-12", "पुनरपि गच्छति", [t("पुनः+अपि", VIS), t("गच्छति")]),
 ("DEV-13", "छात्रोऽपठत्", [t("छात्रः+अपठत्", VIS)]),
 ("DEV-14", "मुनिरपि पठति", [t("मुनिः+अपि", VIS), t("पठति")]),
 ("DEV-15", "सत्यमेव जयते", [t("सत्यम्+एव", BND), t("जयते")]),
 ("DEV-16", "हिमालयः पर्वतः", [t("हिम+आलयः", VOW), t("पर्वतः")]),
 ("DEV-17", "सूर्यास्तः भवति", [t("सूर्य+अस्तः", VOW), t("भवति")]),
 ("DEV-18", "तस्यैव गृहम्", [t("तस्य+एव", VOW), t("गृहम्")]),
 ("DEV-19", "भवत्यत्र", [t("भवति+अत्र", VOW)]),
 ("DEV-20", "वनमेव गच्छति", [t("वनम्+एव", BND), t("गच्छति")]),
 ("DEV-21", "त्वमसि", [t("त्वम्+असि", BND)]),
 ("DEV-22", "चेदस्ति", [t("चेत्+अस्ति", CON)]),
 ("DEV-23", "बालः पठति", [t("बालः"), t("पठति")]),
 ("DEV-24", "सा गृहं गच्छति", [t("सा"), t("गृहम्", NORM), t("गच्छति")]),
 ("DEV-25", "अहं विद्यालयं गच्छामि", [t("अहम्", NORM), t("विद्यालयम्", NORM), t("गच्छामि")]),
 ("DEV-26", "छात्राः पठन्ति", [t("छात्राः"), t("पठन्ति")]),
 ("DEV-27", "ईश्वरः सर्वत्र अस्ति", [t("ईश्वरः"), t("सर्वत्र"), t("अस्ति")]),
 ("DEV-28", "रामः गच्छति", [t("रामः"), t("गच्छति")]),
 ("DEV-29", "राजा नगरम् आगच्छति", [t("राजा"), t("नगरम्"), t("आगच्छति", PV)]),
 ("DEV-30", "विद्यालयं गच्छन्ति छात्राः", [t("विद्यालयम्", NORM), t("गच्छन्ति"), t("छात्राः")]),
]

def rows():
    for _id, sent, src, toks, note in BENCH:
        yield dict(id=_id, split="bench", source=src, sentence=sent, tokens=toks, note=note)
    for _id, sent, toks in DEV:
        yield dict(id=_id, split="dev", source="authored for dev", sentence=sent, tokens=toks, note="")

if __name__ == "__main__":
    out = os.path.join(os.path.dirname(__file__), "..", "data", "sandhi_gold.jsonl")
    with open(out, "w", encoding="utf-8") as f:
        for r in rows():
            surf = split_tokens(r["sentence"])
            assert len(surf) == len(r["tokens"]), (r["id"], surf, len(r["tokens"]))
            r["tokens"] = [{"surface": s, "words": w, "type": ty} for s, (w, ty) in zip(surf, r["tokens"])]
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
    print("wrote", os.path.abspath(out))
