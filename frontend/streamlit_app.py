# -*- coding: utf-8 -*-
"""
VākyaSetu (वाक्यसेतु) — Interactive Sanskrit Learning Assistant
CBSE / NCERT Classes 6–10 (Ruchira, Shemushi, Manika, Hitopadesha)

Designed & Developed by:
- Mayank: Sandhi-Splitting & Student Web Interface
- Shrinivas: Morphological Analysis & Backend Orchestration
- Satyam: IndicTrans2 Machine Translation Track
"""

import json
import os
import sys
import time
from typing import Dict, Any, List, Optional
import requests
import streamlit as st

# Ensure backend modules can be imported directly when running embedded
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
BACKEND_DIR = os.path.join(BASE_DIR, "backend")
if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)

# Streamlit Page Configuration
st.set_page_config(
    page_title="VākyaSetu | Sanskrit Learning Assistant",
    page_icon="🕉️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Custom Styling (Theme, Typography, Cards, Badges)
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=Noto+Sans+Devanagari:wght@400;600;700&display=swap');

    html, body, [class*="css"] {
        font-family: 'Inter', 'Noto Sans Devanagari', sans-serif;
    }

    .main-header {
        background: linear-gradient(135deg, #1e1b4b 0%, #312e81 50%, #4338ca 100%);
        padding: 2.2rem 2.5rem;
        border-radius: 16px;
        color: #ffffff;
        margin-bottom: 2rem;
        box-shadow: 0 10px 25px -5px rgba(67, 56, 202, 0.25);
    }
    
    .main-header h1 {
        font-family: 'Noto Sans Devanagari', 'Inter', sans-serif;
        font-size: 2.4rem;
        font-weight: 700;
        margin: 0;
        letter-spacing: -0.5px;
    }
    
    .main-header p {
        color: #c7d2fe;
        font-size: 1.05rem;
        margin-top: 0.5rem;
        margin-bottom: 0;
    }
    
    .card {
        background-color: #ffffff;
        border-radius: 14px;
        padding: 1.5rem 1.8rem;
        margin-bottom: 1.5rem;
        border: 1px solid #e2e8f0;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05), 0 2px 4px -1px rgba(0, 0, 0, 0.03);
    }
    
    .card-title {
        font-size: 1.25rem;
        font-weight: 600;
        color: #0f172a;
        margin-bottom: 1rem;
        display: flex;
        align-items: center;
        gap: 0.5rem;
    }

    .chip-container {
        display: flex;
        flex-wrap: wrap;
        gap: 0.75rem;
        margin-top: 0.75rem;
    }

    .word-chip {
        background: linear-gradient(135deg, #e0e7ff 0%, #c7d2fe 100%);
        color: #312e81;
        padding: 0.55rem 1.1rem;
        border-radius: 24px;
        font-size: 1.15rem;
        font-weight: 600;
        border: 1px solid #a5b4fc;
        display: inline-flex;
        align-items: center;
        box-shadow: 0 2px 4px rgba(67, 56, 202, 0.08);
    }

    .rule-box {
        background-color: #f8fafc;
        border-left: 4px solid #6366f1;
        padding: 0.85rem 1.1rem;
        border-radius: 0 8px 8px 0;
        margin-top: 0.6rem;
        font-size: 0.95rem;
    }

    .grammar-card {
        background-color: #f8fafc;
        border: 1px solid #e2e8f0;
        border-radius: 12px;
        padding: 1rem;
        margin-bottom: 0.8rem;
        transition: transform 0.15s ease, box-shadow 0.15s ease;
    }

    .grammar-card:hover {
        transform: translateY(-2px);
        box-shadow: 0 6px 12px -2px rgba(0, 0, 0, 0.08);
    }

    .badge {
        display: inline-block;
        padding: 0.2rem 0.6rem;
        font-size: 0.8rem;
        font-weight: 600;
        border-radius: 6px;
        margin-right: 0.4rem;
        margin-bottom: 0.3rem;
    }

    .badge-primary { background-color: #e0e7ff; color: #3730a3; }
    .badge-success { background-color: #dcfce7; color: #166534; }
    .badge-warning { background-color: #fef3c7; color: #92400e; }
    .badge-purple  { background-color: #f3e8ff; color: #6b21a8; }
    .badge-cyan    { background-color: #cffafe; color: #155e75; }

    .translation-text {
        font-size: 1.35rem;
        color: #1e293b;
        font-weight: 500;
        line-height: 1.6;
        padding: 0.5rem 0;
    }
</style>
""", unsafe_allow_html=True)

# Curated NCERT Textbook Presets
NCERT_PRESETS = {
    "Select an NCERT textbook example...": "",
    "Class 6: Ruchira — रामो वनं गच्छति। (Visarga Utva & Anusvara)": "रामो वनं गच्छति।",
    "Class 6: Ruchira — बालकः विद्यालयं गच्छति। (School visit)": "बालकः विद्यालयं गच्छति।",
    "Class 6: Ruchira — सा पुस्तकं पठति। (Reading books)": "सा पुस्तकं पठति।",
    "Class 6: Ruchira — सूर्योदयः प्रभाते भवति। (Guna Sandhi)": "सूर्योदयः प्रभाते भवति।",
    "Class 7: Ruchira — देवालयं गत्वा सः गुरुं प्रणमति। (Dirgha & Upasarga)": "देवालयं गत्वा सः गुरुं प्रणमति।",
    "Class 7: Ruchira — वृक्षात् पत्राणि पतन्ति। (Ablative 5th Case)": "वृक्षात् पत्राणि पतन्ति।",
    "Class 7: Ruchira — यद्यपि सः सदा सत्यं वदति। (Yan Sandhi & Avyaya)": "यद्यपि सः सदा सत्यं वदति।",
    "Class 8: Ruchira — सोऽवदत् यत् तत्र कोऽपि नास्ति। (Avagraha & Purvarupa)": "सोऽवदत् यत् तत्र कोऽपि नास्ति।",
    "Class 9: Shemushi — आसीत् शोभावती नाम काचन नगरी। (Story narrative)": "आसीत् शोभावती नाम काचन नगरी।",
    "Class 9: Shemushi — तत्र शूद्रको नाम महापराक्रमी महीपतिः प्रतिवसति स्म।": "तत्र शूद्रको नाम महापराक्रमी महीपतिः प्रतिवसति स्म।",
    "Class 10: Shemushi — अथैकदा वीरवरनामा राजपुत्रः वृत्त्यर्थं कस्मादपि देशाद् राजद्वारमुपागच्छत्।": "अथैकदा वीरवरनामा राजपुत्रः वृत्त्यर्थं कस्मादपि देशाद् राजद्वारमुपागच्छत्।",
    "Class 10: Shemushi — भोः प्रतिहार! वृत्त्यर्थमागतो राजपुत्रोऽस्मि, तस्मान्नय मां स्वामिनः समीपम्।": "भोः प्रतिहार! वृत्त्यर्थमागतो राजपुत्रोऽस्मि, तस्मान्नय मां स्वामिनः समीपम्।",
    "Class 10: Shemushi — इमौ बाहू, एष खड्गश्च। (Enclitic Cha)": "इमौ बाहू, एष खड्गश्च।",
    "Class 10: Shemushi — नैतच्छक्यम्! (Ch-tva & Vriddhi)": "नैतच्छक्यम्!",
    "Subhashitani — सदाचारः एव परमो धर्मः। (Moral aphorism)": "सदाचारः एव परमो धर्मः।",
}

# Sidebar Controls
with st.sidebar:
    st.image("https://img.icons8.com/color/96/om.png", width=64)
    st.title("VākyaSetu Settings")
    st.caption("CBSE / NCERT Classes 6–10 Sanskrit Assistant")
    
    st.subheader("📚 Textbook Sentences")
    selected_preset = st.selectbox(
        "Choose a sample sentence:",
        options=list(NCERT_PRESETS.keys()),
        index=0,
    )
    
    st.divider()
    
    st.subheader("⚙️ Execution Engine")
    api_url = st.text_input(
        "Backend API Base URL",
        value="http://localhost:8000/api/v1",
        help="FastAPI orchestrator endpoint. If offline, the app runs the embedded linguistic engine automatically."
    )
    
    bypass_cache = st.checkbox("Bypass Cache (Force re-compute)", value=False)
    
    st.divider()
    st.subheader("👥 Project Team")
    st.markdown("""
    - **Mayank** — *Sandhi & UI Track*
    - **Shrinivas** — *Morphology & Backend*
    - **Satyam** — *IndicTrans2 ML Track*
    """)
    st.caption("Sem 5 NLP Course Project")

# Header
st.markdown("""
<div class="main-header">
    <h1>वाक्यसेतु (VākyaSetu)</h1>
    <p>A Pedagogical Computational Sanskrit Assistant for School Students (CBSE / NCERT Classes 6–10)</p>
</div>
""", unsafe_allow_html=True)

# Input Box
preset_val = NCERT_PRESETS[selected_preset]
sentence_input = st.text_area(
    "Enter a Sanskrit Sentence in Devanagari (संस्कृतवाक्यम्):",
    value=preset_val if preset_val else "अथैकदा वीरवरनामा राजपुत्रः वृत्त्यर्थं कस्मादपि देशाद् राजद्वारमुपागच्छत्।",
    height=100,
    help="Type or paste any Sanskrit prose sentence from NCERT Ruchira or Shemushi textbooks."
)

col_btn1, col_btn2, _ = st.columns([1.5, 1, 4])
with col_btn1:
    analyze_btn = st.button("🔍 Analyze Sentence (विश्लेषणम्)", type="primary", use_container_width=True)
with col_btn2:
    clear_btn = st.button("🗑️ Clear", use_container_width=True)

if clear_btn:
    sentence_input = ""
    st.rerun()

def run_analysis(text: str, api_base: str, bypass: bool) -> Dict[str, Any]:
    """Attempts backend API call, falling back gracefully to embedded orchestrator."""
    # 1. Try remote FastAPI backend
    endpoint = f"{api_base.rstrip('/')}/analyze"
    try:
        resp = requests.post(
            endpoint,
            json={"text": text},
            params={"bypass_cache": bypass},
            timeout=4.0
        )
        if resp.status_code == 200:
            data = resp.json()
            data["_engine"] = "FastAPI Backend (Live Service)"
            return data
    except Exception:
        pass

    # 2. Seamless local fallback
    try:
        from app.services.orchestrator import get_orchestrator_service
        orch = get_orchestrator_service()
        res = orch.analyze(text, bypass_cache=bypass)
        data = res.model_dump()
        data["_engine"] = "Embedded Python Linguistic Pipeline (Offline Mode)"
        return data
    except Exception as e:
        st.error(f"Analysis engine error: {e}")
        return {}

# Main Results Rendering
if analyze_btn or sentence_input:
    clean_in = sentence_input.strip()
    if not clean_in:
        st.warning("Please enter a Sanskrit sentence above.")
    else:
        with st.spinner("Analyzing Sanskrit phonetics, sandhi boundaries, and morphology..."):
            t0 = time.perf_counter()
            result = run_analysis(clean_in, api_url, bypass_cache)
            elapsed_ms = round((time.perf_counter() - t0) * 1000.0, 2)

        if result:
            # Metadata bar
            meta_col1, meta_col2, meta_col3 = st.columns([2, 1.5, 1.5])
            with meta_col1:
                st.caption(f"⚡ Engine: **{result.get('_engine', 'Local')}**")
            with meta_col2:
                cached_badge = "🟢 Cached" if result.get("cached") else "🔵 Computed"
                st.caption(f"Status: **{cached_badge}**")
            with meta_col3:
                st.caption(f"⏱️ Latency: **{result.get('processing_time_ms', elapsed_ms)} ms**")

            # -----------------------------------------------------------------
            # CARD 1: ENGLISH TRANSLATION
            # -----------------------------------------------------------------
            st.markdown("""
            <div class="card">
                <div class="card-title">📖 English Translation (आङ्ग्लानुवादः)</div>
            """, unsafe_allow_html=True)
            translation_val = result.get("translation", "No translation available.")
            st.markdown(f'<div class="translation-text">"{translation_val}"</div>', unsafe_allow_html=True)
            st.caption("Translation powered by IndicTrans2 / Generative Kāraka Semantic Synthesizer.")
            st.markdown("</div>", unsafe_allow_html=True)

            # -----------------------------------------------------------------
            # CARD 2: SANDHI-SPLIT WORDS & PANINIAN RULES (Mayank's Spotlight)
            # -----------------------------------------------------------------
            st.markdown("""
            <div class="card">
                <div class="card-title">🔗 Sandhi Breakdown & Word Segmentation (सन्धि-विच्छेदः)</div>
            """, unsafe_allow_html=True)
            
            splits = result.get("sandhi_splits", [])
            if splits:
                chips_html = "".join([f'<span class="word-chip">{w}</span>' for w in splits])
                st.markdown(f'<div class="chip-container">{chips_html}</div>', unsafe_allow_html=True)
            else:
                st.info("No sandhi boundary detected or word is already in base form.")

            # Paninian Sandhi Rules
            rules = result.get("sandhi_rules", [])
            if rules:
                st.markdown("<br><b>📜 Identified Pāṇinian Sandhi Rules (सूत्र-निर्देशः):</b>", unsafe_allow_html=True)
                for r in rules:
                    st.markdown(f"""
                    <div class="rule-box">
                        <b>{r.get('rule_name')}</b> | <code>{r.get('sutra')}</code><br>
                        <span style="color: #475569;">सन्धि-प्रकारः: <b>{r.get('sandhi_type')}</b> | सन्धि-स्थानम्: <b>{r.get('junction')}</b></span><br>
                        <span style="font-size: 0.9rem; color: #1e293b;">{r.get('explanation')}</span>
                    </div>
                    """, unsafe_allow_html=True)
            
            st.markdown("</div>", unsafe_allow_html=True)

            # -----------------------------------------------------------------
            # CARD 3: WORD-BY-WORD MORPHOLOGY & GRAMMAR CARDS
            # -----------------------------------------------------------------
            st.markdown("""
            <div class="card">
                <div class="card-title">🏷️ Word-by-Word Grammatical Analysis (पद-परिचयः)</div>
            """, unsafe_allow_html=True)
            
            morph_list = result.get("morphology", [])
            if morph_list:
                cols = st.columns(min(len(morph_list), 3) if len(morph_list) > 0 else 1)
                for idx, m in enumerate(morph_list):
                    col_target = cols[idx % len(cols)]
                    with col_target:
                        word_str = m.get("word", "")
                        gloss = m.get("primary_gloss", {})
                        root = gloss.get("root", "N/A")
                        pos = gloss.get("pos", "Noun")
                        case_tense = gloss.get("case") or gloss.get("tense") or "Indeclinable (अव्ययम्)"
                        gender = gloss.get("gender")
                        number = gloss.get("number")
                        karaka = m.get("karaka_role")
                        
                        st.markdown(f"""
                        <div class="grammar-card">
                            <h4 style="margin: 0 0 0.4rem 0; color: #1e1b4b; font-family: 'Noto Sans Devanagari';">{word_str}</h4>
                            <div>
                                <span class="badge badge-primary">मूलम्: {root}</span>
                                <span class="badge badge-purple">{pos.split('(')[0].strip()}</span>
                            </div>
                            <div style="margin-top: 0.3rem;">
                                <span class="badge badge-success">{case_tense}</span>
                                {f'<span class="badge badge-cyan">{gender}</span>' if gender else ''}
                                {f'<span class="badge badge-warning">{number}</span>' if number else ''}
                            </div>
                            {f'<div style="margin-top: 0.3rem; font-size: 0.85rem; color: #0284c7;"><b>कारकम्:</b> {karaka}</div>' if karaka else ''}
                            <div style="font-size: 0.85rem; color: #475569; margin-top: 0.5rem; border-top: 1px dashed #cbd5e1; padding-top: 0.4rem;">
                                {gloss.get('english_explanation', '')}
                            </div>
                        </div>
                        """, unsafe_allow_html=True)
            st.markdown("</div>", unsafe_allow_html=True)

            # -----------------------------------------------------------------
            # CARD 4: SAMĀSA (COMPOUNDS) & ANVAYA
            # -----------------------------------------------------------------
            compounds = result.get("compounds", [])
            anvaya = result.get("anvaya", [])
            if compounds or anvaya:
                st.markdown("""
                <div class="card">
                    <div class="card-title">🧩 Compound Breakdown & Prose Order (समासः तथा अन्वयः)</div>
                """, unsafe_allow_html=True)
                
                col_c1, col_c2 = st.columns([1, 1])
                with col_c1:
                    st.markdown("<b>समस्तपदम् / विग्रहवाक्यम् (Samāsa):</b>", unsafe_allow_html=True)
                    if compounds:
                        for comp in compounds:
                            st.markdown(f"""
                            - **समस्तपदम्:** `{comp.get('compound_word')}`
                            - **समास-भेदः:** {comp.get('samasa_type')}
                            - **विग्रहवाक्यम्:** *{comp.get('vigraha_vakya')}*
                            - **अर्थः:** {comp.get('explanation')}
                            """)
                    else:
                        st.caption("No nominal compounds (समस्तपदानि) in this sentence.")

                with col_c2:
                    st.markdown("<b>अन्वय-क्रमः (Syntactic Prose Order):</b>", unsafe_allow_html=True)
                    if anvaya:
                        anvaya_str = " ➔ ".join([f"<b>{w}</b>" for w in anvaya])
                        st.markdown(f'<div style="font-size: 1.15rem; color: #1e1b4b; padding: 0.8rem 0;">{anvaya_str}</div>', unsafe_allow_html=True)
                        st.caption("Subject-Object-Verb syntactic rearrangement for school learners.")
                    else:
                        st.caption("Standard sentence order already matches prose reading sequence.")
                        
                st.markdown("</div>", unsafe_allow_html=True)

            # -----------------------------------------------------------------
            # CARD 5: GRAMMAR VALIDATOR WARNINGS (If Any)
            # -----------------------------------------------------------------
            warnings = result.get("grammar_warnings", [])
            if warnings:
                st.markdown("""
                <div class="card" style="border-left: 4px solid #f59e0b;">
                    <div class="card-title" style="color: #b45309;">⚠️ Pedagogical Grammar Notices (व्याकरण-परामर्शः)</div>
                """, unsafe_allow_html=True)
                for w in warnings:
                    st.warning(f"**{w.get('issue_type')}** ({w.get('erroneous_token')}): {w.get('english_explanation')}")
                st.markdown("</div>", unsafe_allow_html=True)

# Footer
st.divider()
st.markdown("""
<div style="text-align: center; color: #64748b; font-size: 0.9rem; padding: 1rem 0;">
    <b>VākyaSetu (वाक्यसेतु)</b> — Semester 5 Natural Language Processing Project<br>
    Built with FastAPI, Streamlit, and Pāṇinian Computational NLP for CBSE/NCERT Sanskrit.
</div>
""", unsafe_allow_html=True)
