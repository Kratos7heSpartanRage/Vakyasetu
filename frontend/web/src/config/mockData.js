/**
 * VākyaSetu Mock Data Suite
 * Provides verified data structures for all 5 Sandhi statuses:
 * 1. Resolved (Standard Pāṇinian split & intact tokens)
 * 2. Ambiguous (Multiple valid segmentations with selectable alternatives)
 * 3. Compound (Samāsa kept whole with constituent members shown)
 * 4. Unattested (Highlighter-yellow margin note: not in dictionary)
 * 5. Degraded (Sandhi checker offline banner + warnings)
 */

export const MOCK_RESOLVED = {
  original_text: "छात्राः विद्यालये ध्यानपूर्वकं पठन्ति।",
  normalized_text: "छात्राः विद्यालये ध्यानपूर्वकं पठन्ति।",
  translation: "Students study attentively in the school.",
  cached: true,
  processing_time_ms: 184.2,
  sandhi_status: "resolved",
  sandhi_degraded: false,
  sandhi_warnings: [],
  sandhi_splits: ["छात्राः", "विद्या", "आलये", "ध्यानपूर्वकम्", "पठन्ति"],
  sandhi_rules: [
    {
      junction: "विद्या + आलये",
      rule_name: "दीर्घसन्धिः",
      sutra: "अकः सवर्णे दीर्घः ६.१.१०१",
      sandhi_type: "स्वरसन्धिः",
      explanation: "सवर्ण स्वर परे होने पर दोनों मिलकर दीर्घ स्वर (आ) हो जाते हैं।",
      explanation_en: "Two similar simple vowels merge into one corresponding long vowel (a + ā → ā)."
    }
  ],
  sandhi_tokens: [
    {
      surface: "छात्राः",
      words: ["छात्राः"],
      status: "resolved",
      confidence: 0.95,
      evidence: ["Attested nominal stem: छात्र / छात्त्र", "Intact nominative plural"],
      junctions: [],
      alternatives: [],
      compound_members: [],
      warnings: []
    },
    {
      surface: "विद्यालये",
      words: ["विद्या", "आलये"],
      status: "resolved",
      confidence: 0.92,
      evidence: [
        "Aṣṭādhyāyī 6.1.101 Dīrgha Sandhi verified",
        "Both constituent stems attested in Heritage lexicon",
        "Semantic agreement: विद्या (learning) + आलये (in the abode)"
      ],
      junctions: [
        {
          left: "विद्या",
          right: "आलये",
          changed: true,
          rule: {
            junction: "विद्या + आलये",
            rule_name: "दीर्घसन्धिः",
            sutra: "अकः सवर्णे दीर्घः ६.१.१०१",
            sandhi_type: "स्वरसन्धिः",
            explanation: "सवर्ण स्वर परे होने पर दोनों मिलकर दीर्घ स्वर (आ) हो जाते हैं।",
            explanation_en: "Two similar simple vowels merge into one corresponding long vowel (a + ā → ā)."
          }
        }
      ],
      alternatives: [],
      compound_members: ["विद्या", "आलय"],
      warnings: []
    },
    {
      surface: "ध्यानपूर्वकं",
      words: ["ध्यानपूर्वकम्"],
      status: "resolved",
      confidence: 0.88,
      evidence: ["Regular anusvāra to pausa 'म्' normalization", "Neuter accusative singular adverbial"],
      junctions: [],
      alternatives: [],
      compound_members: [],
      warnings: []
    },
    {
      surface: "पठन्ति",
      words: ["पठन्ति"],
      status: "resolved",
      confidence: 0.98,
      evidence: ["Primary dhātu: पठ् (to read/study)", "Laṭ lakāra, prathama puruṣa, bahuvacana"],
      junctions: [],
      alternatives: [],
      compound_members: [],
      warnings: []
    }
  ],
  morphology: [
    {
      word: "छात्राः",
      primary_gloss: {
        root: "छात्त्र / छात्र",
        pos: "नामपदम् (Noun)",
        gender: "पुंल्लिङ्गम् (Masculine)",
        case: "प्रथमा (Nominative)",
        number: "बहुवचनम् (Plural)",
        sanskrit_explanation: "अकारान्त-पुंल्लिङ्ग-छात्र-शब्दस्य प्रथमा-विभक्तौ बहुवचनम्।",
        english_explanation: "Noun declined in Nominative Plural (Students / disciples)."
      },
      karaka_role: "कर्ता (Subject)",
      confidence: 0.95
    },
    {
      word: "विद्या",
      primary_gloss: {
        root: "विद्या",
        pos: "नामपदम् (Noun)",
        gender: "स्त्रीलिङ्गम् (Feminine)",
        case: "प्रथमा (Nominative)",
        number: "एकवचनम् (Singular)",
        sanskrit_explanation: "आकारान्त-स्त्रीलिङ्ग-विद्या-शब्दः।",
        english_explanation: "Noun: Knowledge / sacred learning."
      },
      karaka_role: "उपपदम् (Constituent)",
      confidence: 0.92
    },
    {
      word: "आलये",
      primary_gloss: {
        root: "आलय",
        pos: "नामपदम् (Noun)",
        gender: "पुंल्लिङ्गम् / नपुंसकलिङ्गम्",
        case: "सप्तमी (Locative)",
        number: "एकवचनम् (Singular)",
        sanskrit_explanation: "अकारान्त-आलय-शब्दस्य सप्तमी-विभक्तौ एकवचनम्।",
        english_explanation: "Noun declined in Locative Singular (In the abode / house)."
      },
      karaka_role: "अधिकरणम् (Location)",
      confidence: 0.92
    },
    {
      word: "ध्यानपूर्वकम्",
      primary_gloss: {
        root: "ध्यानपूर्वक",
        pos: "क्रियाविशेषणम् (Adverb)",
        gender: "नपुंसकलिङ्गम्",
        case: "द्वितीया (Accusative)",
        number: "एकवचनम् (Singular)",
        sanskrit_explanation: "क्रियाविशेषणपदम् (ध्यानपूर्वकम् = अवधानेन)।",
        english_explanation: "Adverbial usage: Attentively / with concentration."
      },
      karaka_role: "क्रियाविशेषणम् (Manner)",
      confidence: 0.88
    },
    {
      word: "पठन्ति",
      primary_gloss: {
        root: "पठ्",
        pos: "क्रियापदम् (Finite Verb)",
        tense: "लट् (Present)",
        person: "प्रथमपुरुषः (Third Person)",
        number: "बहुवचनम् (Plural)",
        voice: "कर्तरि प्रयोगः (Active)",
        sanskrit_explanation: "पठ्-धातोः लट्लकारे प्रथमपुरुषे बहुवचनम्।",
        english_explanation: "Finite verb in Present Tense (Laṭ), 3rd Person Plural (They read/study)."
      },
      karaka_role: "क्रियापदम् (Predicate)",
      confidence: 0.98
    }
  ]
};

export const MOCK_AMBIGUOUS = {
  original_text: "तन्नास्ति",
  normalized_text: "तन्नास्ति",
  translation: "That does not exist.",
  cached: false,
  processing_time_ms: 215.0,
  sandhi_status: "ambiguous",
  sandhi_degraded: false,
  sandhi_warnings: [],
  sandhi_splits: ["तत्", "न", "अस्ति"],
  sandhi_rules: [
    {
      junction: "तत् + न",
      rule_name: "अनुनासिकसन्धिः / श्चुत्वम्",
      sutra: "यरोऽनुनासिकेऽनुनासिको वा ८.४.४५",
      sandhi_type: "व्यञ्जनसन्धिः",
      explanation: "पदांत त् के बाद न होने पर त् का न् हो जाता है।",
      explanation_en: "Final dental stop 't' changes to nasal 'n' before nasal 'n'."
    },
    {
      junction: "न + अस्ति",
      rule_name: "दीर्घसन्धिः",
      sutra: "अकः सवर्णे दीर्घः ६.१.१०१",
      sandhi_type: "स्वरसन्धिः",
      explanation: "अ + अ मिलकर आ बन जाते हैं।",
      explanation_en: "Short vowels a + a merge into long ā."
    }
  ],
  sandhi_tokens: [
    {
      surface: "तन्नास्ति",
      words: ["तत्", "न", "अस्ति"],
      status: "ambiguous",
      confidence: 0.62,
      evidence: [
        "Survives lexicon attestation across 2 candidates",
        "Multi-junction consonant + vowel fusion",
        "Alternative candidate also valid syntactically"
      ],
      junctions: [
        {
          left: "तत्",
          right: "न",
          changed: true,
          rule: {
            junction: "तत् + न",
            rule_name: "अनुनासिकसन्धिः",
            sutra: "यरोऽनुनासिकेऽनुनासिको वा ८.४.४५",
            sandhi_type: "व्यञ्जनसन्धिः",
            explanation: "त् के बाद न होने पर त् का न् हो जाता है।",
            explanation_en: "Dental stop 't' assimilates to nasal 'n'."
          }
        },
        {
          left: "न",
          right: "अस्ति",
          changed: true,
          rule: {
            junction: "न + अस्ति",
            rule_name: "दीर्घसन्धिः",
            sutra: "अकः सवर्णे दीर्घः ६.१.१०१",
            sandhi_type: "स्वरसन्धिः",
            explanation: "अ + अ मिलकर आ बन जाते हैं।",
            explanation_en: "Vowels a + a merge into long ā."
          }
        }
      ],
      alternatives: [
        ["तत्", "न", "अस्ति"],
        ["तं", "न", "अस्ति"],
        ["तत्", "नास्ति"]
      ],
      compound_members: [],
      warnings: []
    }
  ],
  morphology: [
    {
      word: "तत्",
      primary_gloss: {
        root: "तद्",
        pos: "सर्वनाम (Pronoun)",
        gender: "नपुंसकलिङ्गम्",
        case: "प्रथमा (Nominative)",
        number: "एकवचनम्",
        sanskrit_explanation: "तद्-सर्वनाम-शब्दः।",
        english_explanation: "Pronoun: That / It."
      },
      karaka_role: "कर्ता (Subject)",
      confidence: 0.9
    },
    {
      word: "न",
      primary_gloss: {
        root: "न",
        pos: "अव्ययम् (Indeclinable)",
        sanskrit_explanation: "निषेधार्थकम् अव्ययपदम्।",
        english_explanation: "Particle of negation: Not / no."
      },
      karaka_role: "निषेधवाचकम्",
      confidence: 0.99
    },
    {
      word: "अस्ति",
      primary_gloss: {
        root: "अस्",
        pos: "क्रियापदम् (Verb)",
        tense: "लट् (Present)",
        person: "प्रथमपुरुषः",
        number: "एकवचनम्",
        sanskrit_explanation: "अस्-धातोः लट्लकारे प्रथमपुरुषे एकवचनम्।",
        english_explanation: "Verb: Exists / is."
      },
      karaka_role: "क्रियापदम्",
      confidence: 0.98
    }
  ]
};

export const MOCK_COMPOUND = {
  original_text: "महापराक्रमी राजपुत्रः आगच्छति।",
  normalized_text: "महापराक्रमी राजपुत्रः आगच्छति।",
  translation: "The valiant prince arrives.",
  cached: false,
  processing_time_ms: 198.5,
  sandhi_status: "resolved",
  sandhi_degraded: false,
  sandhi_warnings: [],
  sandhi_splits: ["महापराक्रमी", "राजपुत्रः", "आगच्छति"],
  sandhi_rules: [],
  sandhi_tokens: [
    {
      surface: "महापराक्रमी",
      words: ["महापराक्रमी"],
      status: "compound",
      confidence: 0.88,
      evidence: [
        "Karmadhāraya/Bahuvrīhi compound",
        "Kept whole in accordance with NCERT standard (no internal phonetic sandhi alteration)"
      ],
      junctions: [],
      alternatives: [],
      compound_members: ["महत्", "पराक्रमिन्"],
      warnings: []
    },
    {
      surface: "राजपुत्रः",
      words: ["राजपुत्रः"],
      status: "compound",
      confidence: 0.91,
      evidence: [
        "Ṣaṣṭhī Tatpuruṣa compound: राज्ञः पुत्रः",
        "Unfused boundary, kept intact as per guideline"
      ],
      junctions: [],
      alternatives: [],
      compound_members: ["राजन्", "पुत्रः"],
      warnings: []
    },
    {
      surface: "आगच्छति",
      words: ["आगच्छति"],
      status: "resolved",
      confidence: 0.95,
      evidence: ["Upasarga 'आङ्' prefixed to verb 'गच्छति'; lexicalised finite verb"],
      junctions: [],
      alternatives: [],
      compound_members: [],
      warnings: []
    }
  ],
  morphology: [
    {
      word: "महापराक्रमी",
      primary_gloss: {
        root: "महापराक्रमिन्",
        pos: "विशेषणम् (Adjective)",
        gender: "पुंल्लिङ्गम्",
        case: "प्रथमा",
        number: "एकवचनम्",
        sanskrit_explanation: "महान् पराक्रमः यस्य सः (बहुव्रीहिः)।",
        english_explanation: "Adjective: Highly valiant / courageous."
      },
      karaka_role: "विशेषणम् (Subject Modifier)",
      confidence: 0.88
    },
    {
      word: "राजपुत्रः",
      primary_gloss: {
        root: "राजपुत्र",
        pos: "नामपदम् (Noun)",
        gender: "पुंल्लिङ्गम्",
        case: "प्रथमा",
        number: "एकवचनम्",
        sanskrit_explanation: "राज्ञः पुत्रः राजपुत्रः (षष्ठी-तत्पुरुषः)।",
        english_explanation: "Noun: Prince (King's son)."
      },
      karaka_role: "कर्ता (Subject)",
      confidence: 0.91
    },
    {
      word: "आगच्छति",
      primary_gloss: {
        root: "आ + गम्",
        pos: "क्रियापदम् (Verb)",
        tense: "लट् (Present)",
        person: "प्रथमपुरुषः",
        number: "एकवचनम्",
        sanskrit_explanation: "आङ्-पूर्वक-गम्-धातोः लट्लकारे प्रथमपुरुषे एकवचनम्।",
        english_explanation: "Verb: Arrives / comes."
      },
      karaka_role: "क्रियापदम् (Predicate)",
      confidence: 0.95
    }
  ]
};

export const MOCK_UNATTESTED = {
  original_text: "वीरवरनामा कश्चित् राजद्वारम् उपागच्छत्।",
  normalized_text: "वीरवरनामा कश्चित् राजद्वारम् उपागच्छत्।",
  translation: "A person named Viravara approached the palace gate.",
  cached: false,
  processing_time_ms: 240.8,
  sandhi_status: "resolved",
  sandhi_degraded: false,
  sandhi_warnings: ["Token 'वीरवरनामा' not found in standard dictionary"],
  sandhi_splits: ["वीरवरनामा", "कश्चित्", "राजद्वारम्", "उपागच्छत्"],
  sandhi_rules: [],
  sandhi_tokens: [
    {
      surface: "वीरवरनामा",
      words: ["वीरवरनामा"],
      status: "unattested",
      confidence: 0.35,
      evidence: [
        "Proper noun / bahuvrīhi name not found in Heritage dictionary",
        "Kept whole to avoid destructive over-segmentation"
      ],
      junctions: [],
      alternatives: [],
      compound_members: [],
      warnings: ["Not found in dictionary, kept as one word"]
    },
    {
      surface: "कश्चित्",
      words: ["कश्चित्"],
      status: "resolved",
      confidence: 0.90,
      evidence: ["Indefinite pronoun stem: किम् + चित्"],
      junctions: [],
      alternatives: [],
      compound_members: [],
      warnings: []
    },
    {
      surface: "राजद्वारम्",
      words: ["राजद्वारम्"],
      status: "resolved",
      confidence: 0.92,
      evidence: ["Accusative singular of compound राजद्वार"],
      junctions: [],
      alternatives: [],
      compound_members: [],
      warnings: []
    },
    {
      surface: "उपागच्छत्",
      words: ["उपागच्छत्"],
      status: "resolved",
      confidence: 0.94,
      evidence: ["Past tense laṅ lakāra: उप + आ + गम्"],
      junctions: [],
      alternatives: [],
      compound_members: [],
      warnings: []
    }
  ],
  morphology: [
    {
      word: "वीरवरनामा",
      primary_gloss: {
        root: "वीरवरनामन्",
        pos: "विशेष्यम् / संज्ञा (Proper Noun)",
        gender: "पुंल्लिङ्गम्",
        case: "प्रथमा",
        number: "एकवचनम्",
        sanskrit_explanation: "वीरवरः नाम यस्य सः (व्यक्तिवाचकसंज्ञा)।",
        english_explanation: "Proper Noun: Named Viravara."
      },
      karaka_role: "विशेषणम्",
      confidence: 0.35
    }
  ]
};

export const MOCK_DEGRADED = {
  original_text: "रामः वनं गच्छति।",
  normalized_text: "रामः वनं गच्छति।",
  translation: "Rama goes to the forest.",
  cached: false,
  processing_time_ms: 12.0,
  sandhi_status: "unavailable",
  sandhi_degraded: true,
  sandhi_warnings: [
    "Sandhi checker backend is offline or running without language-model dependencies.",
    "Results below are unverified heuristic estimates."
  ],
  sandhi_splits: ["रामः", "वनम्", "गच्छति"],
  sandhi_rules: [],
  sandhi_tokens: [
    {
      surface: "रामः",
      words: ["रामः"],
      status: "unavailable",
      confidence: 0.3,
      evidence: ["Unverified offline heuristic"],
      junctions: [],
      alternatives: [],
      compound_members: [],
      warnings: ["Sandhi checker is offline"]
    },
    {
      surface: "वनं",
      words: ["वनम्"],
      status: "unavailable",
      confidence: 0.3,
      evidence: ["Unverified offline heuristic"],
      junctions: [],
      alternatives: [],
      compound_members: [],
      warnings: ["Sandhi checker is offline"]
    },
    {
      surface: "गच्छति",
      words: ["गच्छति"],
      status: "unavailable",
      confidence: 0.3,
      evidence: ["Unverified offline heuristic"],
      junctions: [],
      alternatives: [],
      compound_members: [],
      warnings: ["Sandhi checker is offline"]
    }
  ],
  morphology: [
    {
      word: "रामः",
      primary_gloss: {
        root: "राम",
        pos: "नामपदम्",
        gender: "पुंल्लिङ्गम्",
        case: "प्रथमा",
        number: "एकवचनम्",
        sanskrit_explanation: "राम-शब्दः प्रथमा-एकवचनम्।",
        english_explanation: "Rama (Nominative Singular)."
      },
      karaka_role: "कर्ता",
      confidence: 0.95
    }
  ]
};
