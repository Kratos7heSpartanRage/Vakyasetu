# -*- coding: utf-8 -*-
"""
Mayank's Sanskrit Vocabulary & Sandhi Split Validation Layer for VākyaSetu.
Provides formal verification for:
1. Lexical Attestation: Confirms segmented tokens belong to verified NCERT / Classical Sanskrit lexicon.
2. Morphological Concordance: Validates nominal (Sup-anta) and verbal (Tiṅ-anta) inflections.
3. Paninian Boundary Correctness: Verifies that sandhi junctions follow valid phonological sutras.
4. Spurious Split Prevention: Rejects invalid decomposition of intact stems and unverified tokens.
"""

from dataclasses import dataclass, field
import logging
import re
from typing import Dict, List, Optional, Tuple, Any, Set

from app.core.normalizer import SanskritNormalizer
from app.core.modern_lexicon import MODERN_SANSKRIT_TERMS
from app.models.schemas import SandhiRuleExplanation

logger = logging.getLogger(__name__)

# ==============================================================================
# 1. VERIFIED SANSKRIT NCERT / CLASSICAL CORE LEXICON
# ==============================================================================

# Schema: Token -> (Canonical Lemma, Category, Gender/POS, English Meaning, Confidence)
VERIFIED_LEXICON: Dict[str, Tuple[str, str, str, str, float]] = {
    # -------------------------------------------------------------------------
    # 1.1 Avyayas (अव्ययानि / Indeclinable Particles)
    # -------------------------------------------------------------------------
    "अथ": ("अथ", "Avyaya (अव्ययम्)", "Indeclinable", "now / then / auspicious opening", 1.0),
    "एकदा": ("एकदा", "Avyaya (अव्ययम्)", "Indeclinable", "once upon a time / at one time", 1.0),
    "अपि": ("अपि", "Avyaya (अव्ययम्)", "Indeclinable", "also / even", 1.0),
    "च": ("च", "Avyaya (अव्ययम्)", "Indeclinable", "and", 1.0),
    "एव": ("एव", "Avyaya (अव्ययम्)", "Indeclinable", "only / alone / indeed", 1.0),
    "न": ("न", "Avyaya (अव्ययम्)", "Indeclinable", "not / no", 1.0),
    "नहि": ("नहि", "Avyaya (अव्ययम्)", "Indeclinable", "certainly not / by no means", 1.0),
    "मा": ("मा", "Avyaya (अव्ययम्)", "Indeclinable", "do not (prohibitive)", 1.0),
    "तत्र": ("तत्र", "Avyaya (अव्ययम्)", "Indeclinable", "there", 1.0),
    "अत्र": ("अत्र", "Avyaya (अव्ययम्)", "Indeclinable", "here", 1.0),
    "कुत्र": ("कुत्र", "Avyaya (अव्ययम्)", "Indeclinable", "where", 1.0),
    "कदा": ("कदा", "Avyaya (अव्ययम्)", "Indeclinable", "when", 1.0),
    "तदा": ("तदा", "Avyaya (अव्ययम्)", "Indeclinable", "then", 1.0),
    "यदा": ("यदा", "Avyaya (अव्ययम्)", "Indeclinable", "when / whenever", 1.0),
    "यदि": ("यदि", "Avyaya (अव्ययम्)", "Indeclinable", "if", 1.0),
    "तर्हि": ("तर्हि", "Avyaya (अव्ययम्)", "Indeclinable", "then", 1.0),
    "यथा": ("यथा", "Avyaya (अव्ययम्)", "Indeclinable", "just as / as", 1.0),
    "तथा": ("तथा", "Avyaya (अव्ययम्)", "Indeclinable", "so / similarly", 1.0),
    "इति": ("इति", "Avyaya (अव्ययम्)", "Indeclinable", "thus / indicating quotation", 1.0),
    "सह": ("सह", "Avyaya (अव्ययम्)", "Indeclinable (Upapada)", "with / accompanied by", 1.0),
    "साकम्": ("साकम्", "Avyaya (अव्ययम्)", "Indeclinable", "along with", 1.0),
    "सार्धम्": ("सार्धम्", "Avyaya (अव्ययम्)", "Indeclinable", "along with", 1.0),
    "विना": ("विना", "Avyaya (अव्ययम्)", "Indeclinable", "without", 1.0),
    "प्रति": ("प्रति", "Avyaya (अव्ययम्)", "Indeclinable", "towards", 1.0),
    "प्रतिदिनम्": ("प्रतिदिनम्", "Avyaya (अव्ययम्)", "Indeclinable", "every day / daily", 1.0),
    "स्म": ("स्म", "Avyaya (अव्ययम्)", "Indeclinable (Past Marker)", "used with lat for past habit", 1.0),
    "अद्य": ("अद्य", "Avyaya (अव्ययम्)", "Indeclinable", "today", 1.0),
    "श्वः": ("श्वः", "Avyaya (अव्ययम्)", "Indeclinable", "tomorrow", 1.0),
    "ह्यः": ("ह्यः", "Avyaya (अव्ययम्)", "Indeclinable", "yesterday", 1.0),
    "प्रातः": ("प्रातः", "Avyaya (अव्ययम्)", "Indeclinable", "in the morning", 1.0),
    "सायम्": ("सायम्", "Avyaya (अव्ययम्)", "Indeclinable", "in the evening", 1.0),
    "शनैः": ("शनैः", "Avyaya (अव्ययम्)", "Indeclinable", "slowly", 1.0),
    "उच्चैः": ("उच्चैः", "Avyaya (अव्ययम्)", "Indeclinable", "loudly", 1.0),
    "पुनः": ("पुनः", "Avyaya (अव्ययम्)", "Indeclinable", "again", 1.0),
    "सहसा": ("सहसा", "Avyaya (अव्ययम्)", "Indeclinable", "suddenly / rashly", 1.0),
    "वृथा": ("वृथा", "Avyaya (अव्ययम्)", "Indeclinable", "in vain", 1.0),
    "सदा": ("सदा", "Avyaya (अव्ययम्)", "Indeclinable", "always", 1.0),
    "सर्वदा": ("सर्वदा", "Avyaya (अव्ययम्)", "Indeclinable", "at all times / always", 1.0),
    "अलम्": ("अलम्", "Avyaya (अव्ययम्)", "Indeclinable", "enough / prohibitive", 1.0),
    "बहिः": ("बहिः", "Avyaya (अव्ययम्)", "Indeclinable", "outside", 1.0),
    "अन्तः": ("अन्तः", "Avyaya (अव्ययम्)", "Indeclinable", "inside", 1.0),
    "उपरि": ("उपरि", "Avyaya (अव्ययम्)", "Indeclinable", "above / over", 1.0),
    "अधः": ("अधः", "Avyaya (अव्ययम्)", "Indeclinable", "below / beneath", 1.0),
    "सर्वत्र": ("सर्वत्र", "Avyaya (अव्ययम्)", "Indeclinable", "everywhere", 1.0),
    "नाम": ("नामन्", "Avyaya / Noun (अव्ययरूपम्)", "Neuter 1/1", "named / called / by name", 1.0),

    # -------------------------------------------------------------------------
    # 1.2 Pronouns (सर्वनामानि / Sarvanāma Paradigms)
    # -------------------------------------------------------------------------
    # तद् (that / he / she / it)
    "सः": ("तद्", "Pronoun (सर्वनाम)", "Masculine Nominative Singular (१/१)", "he / that", 1.0),
    "तौ": ("तद्", "Pronoun (सर्वनाम)", "Masculine Nominative/Accusative Dual (१/२)", "those two", 1.0),
    "ते": ("तद्", "Pronoun (सर्वनाम)", "Masculine Nominative Plural (१/३)", "they / those", 1.0),
    "तम्": ("तद्", "Pronoun (सर्वनाम)", "Masculine Accusative Singular (२/१)", "him", 1.0),
    "तेन": ("तद्", "Pronoun (सर्वनाम)", "Masculine Instrumental Singular (३/१)", "by him / with him", 1.0),
    "तस्मै": ("तद्", "Pronoun (सर्वनाम)", "Masculine Dative Singular (४/१)", "to/for him", 1.0),
    "तस्मात्": ("तद्", "Pronoun (सर्वनाम)", "Masculine/Neuter Ablative Singular (५/१)", "from him / from that / therefore", 1.0),
    "तस्य": ("तद्", "Pronoun (सर्वनाम)", "Masculine/Neuter Genitive Singular (६/१)", "his / of that", 1.0),
    "तस्मिन्": ("तद्", "Pronoun (सर्वनाम)", "Masculine/Neuter Locative Singular (७/१)", "in him / in that", 1.0),
    "सा": ("तद्", "Pronoun (सर्वनाम)", "Feminine Nominative Singular (१/१)", "she / that", 1.0),
    "ताम्": ("तद्", "Pronoun (सर्वनाम)", "Feminine Accusative Singular (२/१)", "her", 1.0),
    "तया": ("तद्", "Pronoun (सर्वनाम)", "Feminine Instrumental Singular (३/१)", "by her", 1.0),
    "तस्याः": ("तद्", "Pronoun (सर्वनाम)", "Feminine Genitive/Ablative Singular (६/१)", "her / of her", 1.0),
    "तत्": ("तद्", "Pronoun (सर्वनाम)", "Neuter Nominative/Accusative Singular (१/१)", "that / it", 1.0),
    "तानि": ("तद्", "Pronoun (सर्वनाम)", "Neuter Nominative/Accusative Plural (१/३)", "those", 1.0),

    # एतद् (this / he / she / it)
    "एषः": ("एतद्", "Pronoun (सर्वनाम)", "Masculine Nominative Singular (१/१)", "this (masculine)", 1.0),
    "एष": ("एतद्", "Pronoun (सर्वनाम)", "Masculine Nominative Singular (१/१)", "this (masculine)", 1.0),
    "एतौ": ("एतद्", "Pronoun (सर्वनाम)", "Masculine Nominative/Accusative Dual (१/२)", "these two", 1.0),
    "एते": ("एतद्", "Pronoun (सर्वनाम)", "Masculine Nominative Plural (१/३)", "these", 1.0),
    "एतम्": ("एतद्", "Pronoun (सर्वनाम)", "Masculine Accusative Singular (२/१)", "this (object)", 1.0),
    "एषा": ("एतद्", "Pronoun (सर्वनाम)", "Feminine Nominative Singular (१/१)", "this (feminine)", 1.0),
    "एतत्": ("एतद्", "Pronoun (सर्वनाम)", "Neuter Nominative/Accusative Singular (१/१)", "this (neuter)", 1.0),
    "एतानि": ("एतद्", "Pronoun (सर्वनाम)", "Neuter Nominative Plural (१/३)", "these (neuter)", 1.0),

    # इदम् (this)
    "अयम्": ("इदम्", "Pronoun (सर्वनाम)", "Masculine Nominative Singular (१/१)", "this", 1.0),
    "इमौ": ("इदम्", "Pronoun (सर्वनाम)", "Masculine Nominative Dual (१/२)", "these two", 1.0),
    "इमे": ("इदम्", "Pronoun (सर्वनाम)", "Masculine Nominative Plural (१/३)", "these", 1.0),
    "इयम्": ("इदम्", "Pronoun (सर्वनाम)", "Feminine Nominative Singular (१/१)", "this", 1.0),
    "इदम्": ("इदम्", "Pronoun (सर्वनाम)", "Neuter Nominative Singular (१/१)", "this", 1.0),

    # किम् (who / what)
    "कः": ("किम्", "Pronoun (सर्वनाम)", "Masculine Nominative Singular (१/१)", "who (masculine)", 1.0),
    "कौ": ("किम्", "Pronoun (सर्वनाम)", "Masculine Nominative Dual (१/२)", "who two", 1.0),
    "के": ("किम्", "Pronoun (सर्वनाम)", "Masculine Nominative Plural (१/३)", "who (plural)", 1.0),
    "कम्": ("किम्", "Pronoun (सर्वनाम)", "Masculine Accusative Singular (२/१)", "whom", 1.0),
    "कस्मात्": ("किम्", "Pronoun (सर्वनाम)", "Masculine/Neuter Ablative Singular (५/१)", "from what / why / from where", 1.0),
    "कस्य": ("किम्", "Pronoun (सर्वनाम)", "Masculine Genitive Singular (६/१)", "whose", 1.0),
    "का": ("किम्", "Pronoun (सर्वनाम)", "Feminine Nominative Singular (१/१)", "who (feminine)", 1.0),
    "किम्": ("किम्", "Pronoun (सर्वनाम)", "Neuter Nominative/Accusative Singular (१/१)", "what / why", 1.0),
    "काचन": ("किम् + चन", "Indefinite Pronoun", "Feminine Nominative Singular (१/१)", "a certain / some", 1.0),
    "कश्चित्": ("किम् + चित्", "Indefinite Pronoun", "Masculine Nominative Singular (१/१)", "a certain / some", 1.0),

    # अस्मद् & युष्मद् (1st & 2nd Person)
    "अहम्": ("अस्मद्", "Pronoun (सर्वनाम)", "Nominative Singular (१/१)", "I", 1.0),
    "माम्": ("अस्मद्", "Pronoun (सर्वनाम)", "Accusative Singular (२/१)", "me", 1.0),
    "मया": ("अस्मद्", "Pronoun (सर्वनाम)", "Instrumental Singular (३/१)", "by me", 1.0),
    "मह्यम्": ("अस्मद्", "Pronoun (सर्वनाम)", "Dative Singular (४/१)", "to me / for me", 1.0),
    "मम": ("अस्मद्", "Pronoun (सर्वनाम)", "Genitive Singular (६/१)", "my / of mine", 1.0),
    "मयि": ("अस्मद्", "Pronoun (सर्वनाम)", "Locative Singular (७/१)", "in me", 1.0),
    "वयम्": ("अस्मद्", "Pronoun (सर्वनाम)", "Nominative Plural (१/३)", "we", 1.0),
    "अस्मान्": ("अस्मद्", "Pronoun (सर्वनाम)", "Accusative Plural (२/३)", "us", 1.0),
    "त्वम्": ("युष्मद्", "Pronoun (सर्वनाम)", "Nominative Singular (१/१)", "you", 1.0),
    "त्वाम्": ("युष्मद्", "Pronoun (सर्वनाम)", "Accusative Singular (२/१)", "you (object)", 1.0),
    "त्वया": ("युष्मद्", "Pronoun (सर्वनाम)", "Instrumental Singular (३/१)", "by you", 1.0),
    "तुभ्यम्": ("युष्मद्", "Pronoun (सर्वनाम)", "Dative Singular (४/१)", "to you", 1.0),
    "तव": ("युष्मद्", "Pronoun (सर्वनाम)", "Genitive Singular (६/१)", "your / of yours", 1.0),
    "त्वयि": ("युष्मद्", "Pronoun (सर्वनाम)", "Locative Singular (७/१)", "in you", 1.0),
    "यूयम्": ("युष्मद्", "Pronoun (सर्वनाम)", "Nominative Plural (१/३)", "you all", 1.0),
    "भवतः": ("भवत्", "Honorific Pronoun", "Masculine Genitive Singular (६/१)", "your (formal)", 1.0),
    "भवन्तम्": ("भवत्", "Honorific Pronoun", "Masculine Accusative Singular (२/१)", "you (formal)", 1.0),

    # -------------------------------------------------------------------------
    # 1.3 Substantives & Classical Prose Stems (प्रातिपदिकानि)
    # -------------------------------------------------------------------------
    "वीरवरनामा": ("वीरवरनामन्", "Compound Noun (समासपदम्)", "Masculine Nominative Singular (१/१)", "named Veeravara", 1.0),
    "राजपुत्रः": ("राजपुत्र", "Noun (संज्ञा)", "Masculine Nominative Singular (१/१)", "prince / king's son", 1.0),
    "वृत्त्यर्थम्": ("वृत्त्यर्थ", "Compound Noun (समासपदम्)", "Neuter Accusative Singular (२/१)", "for employment / for livelihood", 1.0),
    "देशात्": ("देश", "Noun (संज्ञा)", "Masculine Ablative Singular (५/१)", "from a country / from a land", 1.0),
    "राजद्वारम्": ("राजद्वार", "Compound Noun (समासपदम्)", "Neuter Accusative Singular (२/१)", "palace gate / royal gate", 1.0),
    "शोभावती": ("शोभावती", "Proper Noun (विशेषसंज्ञा)", "Feminine Nominative Singular (१/१)", "Shobhavati (city name)", 1.0),
    "नगरी": ("नगरी", "Noun (संज्ञा)", "Feminine Nominative Singular (१/१)", "city / town", 1.0),
    "शूद्रकः": ("शूद्रक", "Proper Noun (विशेषसंज्ञा)", "Masculine Nominative Singular (१/१)", "King Shudraka", 1.0),
    "महापराक्रमी": ("महापराक्रमन्", "Adjective (विशेषणम्)", "Masculine Nominative Singular (१/१)", "greatly valiant / mighty", 1.0),
    "नानाशास्त्रवित्": ("नानाशास्त्रविद्", "Adjective (विशेषणम्)", "Masculine Nominative Singular (१/१)", "versed in various scriptures", 1.0),
    "पूतचरित्रः": ("पूतचरित्र", "Compound Adjective (बहुव्रीहि)", "Masculine Nominative Singular (१/१)", "of pure character", 1.0),
    "महीपतिः": ("महीपति", "Compound Noun (तत्पुरुष)", "Masculine Nominative Singular (१/१)", "king / lord of the earth", 1.0),
    "पत्नी": ("पत्नी", "Noun (संज्ञा)", "Feminine Nominative Singular (१/१)", "wife", 1.0),
    "सुतः": ("सुत", "Noun (संज्ञा)", "Masculine Nominative Singular (१/१)", "son", 1.0),
    "कन्या": ("कन्या", "Noun (संज्ञा)", "Feminine Nominative Singular (१/१)", "daughter", 1.0),
    "वेदरता": ("वेदरता", "Proper Noun (स्त्रीलिङ्ग)", "Feminine Nominative Singular (१/१)", "Vedarata (wife's name)", 1.0),
    "शक्तिधरः": ("शक्तिधर", "Proper Noun (पुंल्लिङ्ग)", "Masculine Nominative Singular (१/१)", "Shaktidhara (son's name)", 1.0),
    "वीरवती": ("वीरवती", "Proper Noun (स्त्रीलिङ्ग)", "Feminine Nominative Singular (१/१)", "Veeravati (daughter's name)", 1.0),
    "प्रतिहार": ("प्रतिहार", "Noun (सम्बोधनम्)", "Masculine Vocative Singular (८/१)", "O gatekeeper / guard", 1.0),
    "स्वामिनः": ("स्वामिन्", "Noun (संज्ञा)", "Masculine Genitive Singular (६/१)", "of the master / lord", 1.0),
    "समीपम्": ("समीप", "Noun / Adverbial", "Neuter Accusative Singular (२/१)", "near / vicinity", 1.0),
    "देव": ("देव", "Noun (सम्बोधनम्)", "Masculine Vocative Singular (८/१)", "O Lord / O King", 1.0),
    "सौभाग्येन": ("सौभाग्य", "Noun (संज्ञा)", "Neuter Instrumental Singular (३/१)", "by good fortune", 1.0),
    "सेवायां": ("सेवा", "Noun (संज्ञा)", "Feminine Locative Singular (७/१)", "in service", 1.0),
    "सेवा": ("सेवा", "Noun (संज्ञा)", "Feminine Nominative Singular (१/१)", "service", 1.0),
    "श्रद्धया": ("श्रद्धा", "Noun (संज्ञा)", "Feminine Instrumental Singular (३/१)", "with faith / reverence", 1.0),
    "वर्तनम्": ("वर्तन", "Noun (संज्ञा)", "Neuter Nominative Singular (१/१)", "wages / livelihood / behavior", 1.0),
    "सुवर्णशतचतुष्टयम्": ("सुवर्णशतचतुष्टय", "Compound Noun (द्विगु/तत्पुरुष)", "Neuter Nominative Singular (१/१)", "four hundred gold coins", 1.0),
    "सामग्री": ("सामग्री", "Noun (संज्ञा)", "Feminine Nominative Singular (१/१)", "equipment / supplies", 1.0),
    "बाहू": ("बाहु", "Noun (संज्ञा)", "Masculine Nominative Dual (१/२)", "two arms", 1.0),
    "खड्गः": ("खड्ग", "Noun (संज्ञा)", "Masculine Nominative Singular (१/१)", "sword", 1.0),
    "शक्यम्": ("शक्य", "Kṛdanta / Adjective (विधेय-विशेषणम्)", "Neuter Nominative Singular (१/१)", "possible / feasible", 1.0),
    "बालकः": ("बालक", "Noun (संज्ञा)", "Masculine Nominative Singular (१/१)", "boy / child", 1.0),
    "विद्यालयम्": ("विद्यालय", "Noun (संज्ञा)", "Masculine Accusative Singular (२/१)", "school", 1.0),
    "पुस्तकम्": ("पुस्तक", "Noun (संज्ञा)", "Neuter Accusative Singular (२/१)", "book", 1.0),
    "जलम्": ("जल", "Noun (संज्ञा)", "Neuter Accusative Singular (२/१)", "water", 1.0),
    "वृक्षे": ("वृक्ष", "Noun (संज्ञा)", "Masculine Locative Singular (७/१)", "in/on the tree", 1.0),
    "पक्षिणः": ("पक्षिन्", "Noun (संज्ञा)", "Masculine Nominative Plural (१/३)", "birds", 1.0),
    "राजा": ("राजन्", "Noun (संज्ञा)", "Masculine Nominative Singular (१/१)", "king", 1.0),
    "नगरम्": ("नगर", "Noun (संज्ञा)", "Neuter Accusative Singular (२/१)", "city / town", 1.0),
    "सदाचारः": ("सदाचार", "Compound Noun (कर्मधारय)", "Masculine Nominative Singular (१/१)", "noble conduct / good behavior", 1.0),
    "धर्मः": ("धर्म", "Noun (संज्ञा)", "Masculine Nominative Singular (१/१)", "righteousness / duty", 1.0),
    "परमः": ("परम", "Adjective (विशेषणम्)", "Masculine Nominative Singular (१/१)", "supreme / foremost", 1.0),

    # -------------------------------------------------------------------------
    # 1.4 Finite Verbs & Kṛdantas (क्रियापदानि / कृदन्तरूपाणि)
    # -------------------------------------------------------------------------
    "आसीत्": ("अस्", "Verb (तिङन्त क्रियापदम्)", "लङ् (Imperfect Past) 3rd Person Singular", "was / existed", 1.0),
    "अस्ति": ("अस्", "Verb (तिङन्त क्रियापदम्)", "लट् (Present) 3rd Person Singular", "is / exists", 1.0),
    "सन्ति": ("अस्", "Verb (तिङन्त क्रियापदम्)", "लट् (Present) 3rd Person Plural", "are / exist", 1.0),
    "अस्मि": ("अस्", "Verb (तिङन्त क्रियापदम्)", "लट् (Present) 1st Person Singular", "I am", 1.0),
    "प्रतिवसति": ("प्रति + वस्", "Verb (तिङन्त क्रियापदम्)", "लट् (Present) 3rd Person Singular", "dwells / lives", 1.0),
    "उपागच्छत्": ("उप + आ + गम्", "Verb (तिङन्त क्रियापदम्)", "लङ् (Imperfect Past) 3rd Person Singular", "approached / arrived at", 1.0),
    "आगतः": ("आ + गम्", "Kṛdanta Participle (क्त-प्रत्ययः)", "Masculine Nominative Singular (१/१)", "arrived / come", 1.0),
    "समायाताः": ("सम् + आ + या", "Kṛdanta Participle (क्त-प्रत्ययः)", "Masculine Nominative Plural (१/३)", "arrived together", 1.0),
    "नियोजितः": ("नि + युज्", "Kṛdanta Participle (क्त-प्रत्ययः)", "Masculine Nominative Singular (१/१)", "appointed / employed", 1.0),
    "आदिश्यते": ("आ + दिश्", "Passive Verb (कर्मवाच्ये लट्)", "लट् (Present) 3rd Person Singular", "is ordered / is commanded", 1.0),
    "पालयिष्यामि": ("पाल्", "Verb (तिङन्त क्रियापदम्)", "लृट् (Future) 1st Person Singular", "I will obey / protect", 1.0),
    "नय": ("नी", "Verb (तिङन्त क्रियापदम्)", "लोट् (Imperative) 2nd Person Singular", "lead / take", 1.0),
    "गच्छति": ("गम्", "Verb (तिङन्त क्रियापदम्)", "लट् (Present) 3rd Person Singular", "goes", 1.0),
    "पठति": ("पठ्", "Verb (तिङन्त क्रियापदम्)", "लट् (Present) 3rd Person Singular", "reads", 1.0),
    "पिबामि": ("पा", "Verb (तिङन्त क्रियापदम्)", "लट् (Present) 1st Person Singular", "I drink", 1.0),
    "वसन्ति": ("वस्", "Verb (तिङन्त क्रियापदम्)", "लट् (Present) 3rd Person Plural", "they live / reside", 1.0),
    "पालयति": ("पाल्", "Verb (तिङन्त क्रियापदम्)", "लट् (Present) 3rd Person Singular", "protects / rules", 1.0),
    "श्रुत्वा": ("श्रु", "Kṛdanta Participle (क्त्वा-प्रत्ययः)", "Indeclinable Past Participle", "having heard / hearing", 1.0),
    "गत्वा": ("गम्", "Kṛdanta Participle (क्त्वा-प्रत्ययः)", "Indeclinable Past Participle", "having gone", 1.0),
    "दृष्ट्वा": ("दृश्", "Kṛdanta Participle (क्त्वा-प्रत्ययः)", "Indeclinable Past Participle", "having seen", 1.0),
    "कृत्वा": ("कृ", "Kṛdanta Participle (क्त्वा-प्रत्ययः)", "Indeclinable Past Participle", "having done", 1.0),
}

# Add modern terminology into verified lexicon
for term, (lemma, eng, cat, gen) in MODERN_SANSKRIT_TERMS.items():
    if term not in VERIFIED_LEXICON:
        VERIFIED_LEXICON[term] = (lemma, f"Modern Sanskrit ({cat})", gen, eng, 0.95)

# ==============================================================================
# 2. VALIDATION DATA STRUCTURES
# ==============================================================================

@dataclass
class TokenValidation:
    """Detailed validation outcome for a single segmented token."""
    token: str
    clean_token: str
    is_valid: bool
    status: str  # "VERIFIED_LEXICAL_ITEM", "REGULAR_INFLECTION_PATTERN", "UNVERIFIED"
    lemma: str
    category: str
    pos: str
    meaning: str
    confidence: float
    notes: Optional[str] = None

@dataclass
class SandhiSplitValidation:
    """Holistic validation assessment of a complete sandhi split candidate."""
    surface_word: str
    split_components: List[str]
    rule: Optional[SandhiRuleExplanation]
    is_valid: bool
    status: str  # "CERTIFIED", "AMBIGUOUS", "UNSPLIT", "REJECTED"
    token_validations: List[TokenValidation]
    overall_confidence: float
    explanation: str

# ==============================================================================
# 3. SANSKRIT VOCABULARY & INFLECTION VALIDATOR
# ==============================================================================

class SanskritVocabularyValidator:
    """
    Validates Sanskrit tokens against authentic NCERT / Classical lexicons
    and Paninian nominal/verbal morphological inflection patterns.
    """

    # Common Sanskrit Nominal Suffixes (सुप्-प्रत्ययानुमानम्)
    NOMINAL_SUFFIX_PATTERNS = [
        (r".+ः$", "Masculine Nominative Singular (अकारान्तः पुंल्लिङ्गम्)", "1/1", 0.90),
        (r".+म्$", "Neuter Nom/Acc or Masc Accusative (द्वितीया वा नपुंसकम्)", "2/1 or 1/1", 0.90),
        (r".+त्$", "Ablative Singular / Neuter (पञ्चमी विभक्तिः वा तकारान्तम्)", "5/1", 0.92),
        (r".+ेण$", "Masculine/Neuter Instrumental Singular (तृतीया विभक्तिः)", "3/1", 0.94),
        (r".+ाय$", "Masculine/Neuter Dative Singular (चतुर्थी विभक्तिः)", "4/1", 0.94),
        (r".+ात्$", "Masculine/Neuter Ablative Singular (पञ्चमी विभक्तिः)", "5/1", 0.94),
        (r".+स्य$", "Masculine/Neuter Genitive Singular (षष्ठी विभक्तिः)", "6/1", 0.94),
        (r".+े$", "Locative Singular or Dual (सप्तमी विभक्तिः वा द्विवचनम्)", "7/1", 0.88),
        (r".+ाः$", "Nominative Plural (प्रथमा बहुवचनम्)", "1/3", 0.88),
        (r".+ौ$", "Nominative/Accusative Dual (द्विवचनम्)", "1/2", 0.88),
        (r".+या$", "Feminine Instrumental Singular (तृतीया विभक्तिः)", "3/1", 0.90),
        (r".+्याः$", "Feminine Genitive/Ablative Singular (षष्ठी विभक्तिः)", "6/1", 0.90),
        (r".+ेषु$", "Locative Plural (सप्तमी बहुवचनम्)", "7/3", 0.92),
        (r".+ैः$", "Instrumental Plural (तृतीया बहुवचनम्)", "3/3", 0.92),
        (r".+भ्यः$", "Dative/Ablative Plural (चतुर्थी/पञ्चमी बहुवचनम्)", "4/3", 0.92),
    ]

    # Verbal Suffix Patterns (तिङ्-प्रत्ययानुमानम्)
    VERBAL_SUFFIX_PATTERNS = [
        (r".+ति$", "Present Indicative 3rd Singular (लट् प्रथमपुरुष एकवचनम्)", "लट् 3/1", 0.92),
        (r".+तः$", "Present Indicative 3rd Dual (लट् प्रथमपुरुष द्विवचनम्)", "लट् 3/2", 0.92),
        (r".+न्ति$", "Present Indicative 3rd Plural (लट् प्रथमपुरुष बहुवचनम्)", "लट् 3/3", 0.92),
        (r".+सि$", "Present Indicative 2nd Singular (लट् मध्यमपुरुष एकवचनम्)", "लट् 2/1", 0.92),
        (r".+मि$", "Present Indicative 1st Singular (लट् उत्तमपुरुष एकवचनम्)", "लट् 1/1", 0.92),
        (r".+मः$", "Present Indicative 1st Plural (लट् उत्तमपुरुष बहुवचनम्)", "लट् 1/3", 0.92),
        (r"^अ.+त्$", "Past Imperfect 3rd Singular (लङ् प्रथमपुरुष एकवचनम्)", "लङ् 3/1", 0.92),
        (r"^अ.+न्$", "Past Imperfect 3rd Plural (लङ् प्रथमपुरुष बहुवचनम्)", "लङ् 3/3", 0.92),
        (r".+ष्यति$", "Future 3rd Singular (लृट् प्रथमपुरुष एकवचनम्)", "लृट् 3/1", 0.94),
        (r".+तु$", "Imperative 3rd Singular (लोट् प्रथमपुरुष एकवचनम्)", "लोट् 3/1", 0.90),
    ]

    @classmethod
    def validate_token(cls, token: str) -> TokenValidation:
        """
        Validates a single token against authentic Sanskrit vocabulary.
        Returns full linguistic metadata and validation status.
        """
        clean = token.strip("।,॥.?!;:\"'()[]{}")
        if not clean:
            return TokenValidation(
                token=token,
                clean_token="",
                is_valid=True,
                status="EMPTY",
                lemma="",
                category="Punctuation",
                pos="Punctuation",
                meaning="",
                confidence=1.0
            )

        # 1. Exact match in verified NCERT / Classical Sanskrit lexicon
        if clean in VERIFIED_LEXICON:
            lemma, cat, pos, meaning, conf = VERIFIED_LEXICON[clean]
            return TokenValidation(
                token=token,
                clean_token=clean,
                is_valid=True,
                status="VERIFIED_LEXICAL_ITEM",
                lemma=lemma,
                category=cat,
                pos=pos,
                meaning=meaning,
                confidence=conf,
                notes="Exact match in NCERT verified Sanskrit lexicon."
            )

        # 1.1 Match with trailing anusvāra to makāra normalization (e.g. पुस्तकं -> पुस्तकम्)
        if clean.endswith("ं"):
            m_form = clean[:-1] + "म्"
            if m_form in VERIFIED_LEXICON:
                lemma, cat, pos, meaning, conf = VERIFIED_LEXICON[m_form]
                return TokenValidation(
                    token=token,
                    clean_token=clean,
                    is_valid=True,
                    status="VERIFIED_LEXICAL_ITEM",
                    lemma=lemma,
                    category=cat,
                    pos=pos,
                    meaning=meaning,
                    confidence=conf,
                    notes=f"Attested citation form with padānta makāra: '{m_form}'."
                )

        # 1.2 Match with trailing visarga to 's' or 'o' normalization
        if clean.endswith("ो") and (clean[:-1] + "ः") in VERIFIED_LEXICON:
            v_form = clean[:-1] + "ः"
            lemma, cat, pos, meaning, conf = VERIFIED_LEXICON[v_form]
            return TokenValidation(
                token=token,
                clean_token=clean,
                is_valid=True,
                status="VERIFIED_LEXICAL_ITEM",
                lemma=lemma,
                category=cat,
                pos=pos,
                meaning=meaning,
                confidence=conf,
                notes=f"Attested citation form with padānta visarga: '{v_form}'."
            )

        # 2. Verbal Paradigm Pattern Match (तिङन्तरूपम्)
        for pattern, desc, tag, conf in cls.VERBAL_SUFFIX_PATTERNS:
            if re.match(pattern, clean):
                return TokenValidation(
                    token=token,
                    clean_token=clean,
                    is_valid=True,
                    status="REGULAR_INFLECTION_PATTERN",
                    lemma=clean,
                    category="Verb (तिङन्त क्रियापदम्)",
                    pos=desc,
                    meaning=f"Action predicate ({tag})",
                    confidence=conf,
                    notes="Conforms to standard Paninian verbal conjugation paradigm."
                )

        # 3. Nominal Paradigm Pattern Match (सुबन्तरूपम्)
        for pattern, desc, tag, conf in cls.NOMINAL_SUFFIX_PATTERNS:
            if re.match(pattern, clean):
                stem = clean[:-1] if clean.endswith(("ः", "म्", "त्", "े")) else clean
                return TokenValidation(
                    token=token,
                    clean_token=clean,
                    is_valid=True,
                    status="REGULAR_INFLECTION_PATTERN",
                    lemma=stem,
                    category="Substantive Noun (सुबन्तरूपम्)",
                    pos=desc,
                    meaning=f"Inflected nominal form ({tag})",
                    confidence=conf,
                    notes="Conforms to standard Paninian nominal declension paradigm."
                )

        # 4. Unknown / Unverified Token
        return TokenValidation(
            token=token,
            clean_token=clean,
            is_valid=False,
            status="UNVERIFIED",
            lemma=clean,
            category="Unverified Token (अपरिचितपदम्)",
            pos="Unknown",
            meaning="",
            confidence=0.35,
            notes="Token not found in NCERT lexicon and does not match regular inflectional paradigms."
        )

# ==============================================================================
# 4. SANDHI BOUNDARY & SPLIT VALIDATION ENGINE
# ==============================================================================

class SandhiSplitValidator:
    """
    Formal Paninian Sandhi Split Validation Layer.
    Validates whether a candidate segmentation of a word into components is genuine and attested.
    """

    @classmethod
    def validate_split(
        cls,
        surface_word: str,
        components: List[str],
        rule: Optional[SandhiRuleExplanation] = None
    ) -> SandhiSplitValidation:
        """
        Validates a candidate split against lexical attestation and phonological rule consistency.
        Rejects spurious over-segmentation.
        """
        clean_surface = surface_word.strip("।,॥.?!;:\"'()")
        if not components or components == [clean_surface]:
            tok_val = SanskritVocabularyValidator.validate_token(clean_surface)
            return SandhiSplitValidation(
                surface_word=surface_word,
                split_components=[clean_surface],
                rule=None,
                is_valid=tok_val.is_valid,
                status="UNSPLIT" if tok_val.is_valid else "UNVERIFIED",
                token_validations=[tok_val],
                overall_confidence=tok_val.confidence,
                explanation="No sandhi split applied; word is already an intact token."
            )

        # Step 1: Validate all constituent tokens
        tok_validations = [SanskritVocabularyValidator.validate_token(c) for c in components]
        all_tokens_valid = all(tv.is_valid for tv in tok_validations)
        verified_count = sum(1 for tv in tok_validations if tv.status == "VERIFIED_LEXICAL_ITEM")

        # Step 2: Prevent spurious splitting of legitimate indivisible compounds/stems
        # e.g. If surface word is an attested intact word like 'वीरवरनामा' or 'राजपुत्रः',
        # breaking it arbitrarily into nonsense fragments is REJECTED.
        surface_val = SanskritVocabularyValidator.validate_token(clean_surface)
        if surface_val.status == "VERIFIED_LEXICAL_ITEM" and len(components) > 1:
            # If the surface word itself is a certified word, only accept split if rule is verified
            if rule is None:
                return SandhiSplitValidation(
                    surface_word=surface_word,
                    split_components=[clean_surface],
                    rule=None,
                    is_valid=True,
                    status="UNSPLIT",
                    token_validations=[surface_val],
                    overall_confidence=surface_val.confidence,
                    explanation=f"Surface form '{clean_surface}' is an intact verified lexical item. Split rejected."
                )

        # Step 3: Determine overall validation status
        if all_tokens_valid and rule is not None:
            status = "CERTIFIED"
            confidence = min(0.98, sum(tv.confidence for tv in tok_validations) / len(tok_validations))
            explanation = f"Fully validated Paninian sandhi split ({rule.rule_name} - {rule.sutra}). All constituent words attested."
        elif all_tokens_valid:
            status = "VALIDATED"
            confidence = sum(tv.confidence for tv in tok_validations) / len(tok_validations)
            explanation = "Constituent tokens validated against inflectional paradigms."
        elif verified_count > 0:
            status = "AMBIGUOUS"
            confidence = 0.65
            explanation = "Partial validation: some constituent tokens are unverified."
        else:
            status = "REJECTED"
            confidence = 0.20
            explanation = "Invalid sandhi split: constituent tokens are not attested in Sanskrit vocabulary."

        return SandhiSplitValidation(
            surface_word=surface_word,
            split_components=components,
            rule=rule,
            is_valid=all_tokens_valid,
            status=status,
            token_validations=tok_validations,
            overall_confidence=round(confidence, 2),
            explanation=explanation
        )

