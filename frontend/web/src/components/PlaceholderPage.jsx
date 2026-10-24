import React from 'react';

const TAB_METADATA = {
  practice: {
    sanskritTitle: 'अभ्यास-कक्षा (Interactive Practice)',
    latinSubtitle: 'Self-Testing & Sandhi Exercises',
    description: 'Interactive Sandhi reconstruction puzzles, compound identification drills, and fill-in-the-blank exercises from NCERT Ruchira and Shemushi textbooks are being prepared for you.'
  },
  library: {
    sanskritTitle: 'एनसीईआरटी-ग्रन्थालयः (NCERT Library)',
    latinSubtitle: 'Class 6–10 Textbook Repository',
    description: 'Complete verified chapters from Ruchira (Classes 6-8) and Shemushi (Classes 9-10) with verified word-by-word sandhi annotations and glossary links.'
  },
  guide: {
    sanskritTitle: 'पाणिनीय-सन्धि-निर्देशिका (Pāṇinian Sandhi Guide)',
    latinSubtitle: 'Sūtra Rules, Phonetic Shifts & Tables',
    description: 'Comprehensive pedagogical charts detailing Swara-Sandhi (दीर्घ, गुण, वृद्धि, यण्, अयादि, पूर्वरूप), Vyanjana-Sandhi (श्चुत्व, ष्टुत्व, जश्त्व, अनुनासिक), and Visarga-Sandhi (उत्व, रुत्व, सत्व, लोप).'
  }
};

export default function PlaceholderPage({ tabId, onOpenAboutModal }) {
  if (tabId === 'about') {
    return (
      <div className="about-tab-page">
        {/* Full rich textbook about section */}
        <div className="about-page-paper-card">
          <div className="about-page-header">
            <span className="about-icon-large" aria-hidden="true">📜</span>
            <h2 className="about-page-title" lang="sa">वाक्यसेतु (VākyaSetu) • विस्तृत-परिचयः</h2>
            <p className="about-page-subtitle">Pedagogical Sanskrit Sandhi Segmentation & NCERT Learning Assistant</p>
          </div>

          <div className="about-content-body">
            <div className="about-box mission-box">
              <h3 className="box-title">🏛️ Project Mission & Academic Context</h3>
              <p>
                <strong>VākyaSetu (वाक्यसेतु)</strong> is a <strong>Semester 5 Natural Language Processing</strong> academic project. Its goal is to bridge classical Sanskrit computational grammar (rooted in Pāṇini’s <em>Aṣṭādhyāyī</em>) with state-of-the-art Neural Machine Translation (NMT) for students of <strong>CBSE/NCERT Classes 6–10</strong>.
              </p>
            </div>

            <div className="about-box team-box">
              <h3 className="box-title">👥 Project Team &amp; Track Breakdown</h3>
              <div className="team-grid">
                <div className="team-card mayank-card">
                  <div className="member-header">
                    <span className="member-avatar">👨‍💻</span>
                    <div>
                      <h4 className="member-name">Mayank Kumar</h4>
                      <span className="member-role">Sandhi Engine, Evaluation &amp; Web UI</span>
                    </div>
                  </div>
                  <ul className="member-duties">
                    <li>Pāṇinian Sandhi Segmentation &amp; Junction Classifier</li>
                    <li>Over-segmentation prevention layer (0.0% false split rate)</li>
                    <li>Aṣṭādhyāyī Sūtra rule attribution with bilingual explanations</li>
                    <li>Curated 50-sentence unseen held-out NCERT test set (92.2% acc)</li>
                    <li>Nostalgic NCERT school textbook React 19 UI &amp; living wallpaper</li>
                  </ul>
                </div>

                <div className="team-card satyam-card">
                  <div className="member-header">
                    <span className="member-avatar">🤖</span>
                    <div>
                      <h4 className="member-name">Satyam</h4>
                      <span className="member-role">Neural Machine Translation (NMT)</span>
                    </div>
                  </div>
                  <ul className="member-duties">
                    <li>IndicTrans2 model adaptation (ai4bharat/indictrans2-indic-en-dist-200M)</li>
                    <li>LoRA parameter-efficient fine-tuning on Sanskrit-English parallel corpora</li>
                    <li>Samayik corpus curation and automated style evaluation</li>
                    <li>Translation latency optimization and server deployment</li>
                  </ul>
                </div>

                <div className="team-card shrinivas-card">
                  <div className="member-header">
                    <span className="member-avatar">📚</span>
                    <div>
                      <h4 className="member-name">Shrinivas</h4>
                      <span className="member-role">Morphology, Compounds &amp; Syntax</span>
                    </div>
                  </div>
                  <ul className="member-duties">
                    <li>NCERT Pada-Parichaya morphological feature disambiguation</li>
                    <li>Samāsa compound classification (Tatpuruṣa, Karmadhāraya, Bahuvrīhi)</li>
                    <li>Kāraka dependency role extraction (Kartā, Karma, Karaṇam)</li>
                    <li>Grammar issue and subject-verb agreement diagnostics</li>
                  </ul>
                </div>
              </div>
            </div>

            <div className="about-box metrics-box">
              <h3 className="box-title">📊 Key Empirical Milestones</h3>
              <div className="metrics-summary-grid">
                <div className="metric-box">
                  <span className="metric-number">98.5%</span>
                  <span className="metric-label">NCERT Benchmark Token Accuracy</span>
                </div>
                <div className="metric-box">
                  <span className="metric-number">0.0%</span>
                  <span className="metric-label">Over-Segmentation Rate</span>
                </div>
                <div className="metric-box">
                  <span className="metric-number">92.2%</span>
                  <span className="metric-label">Held-Out Test Token Accuracy (50 sents)</span>
                </div>
                <div className="metric-box">
                  <span className="metric-number">56 / 56</span>
                  <span className="metric-label">Sandhi Engine Unit Tests Passing</span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    );
  }

  const meta = TAB_METADATA[tabId] || {
    sanskritTitle: 'आगामी-विभागः (Coming Soon)',
    latinSubtitle: 'Feature Under Construction',
    description: 'This section of VākyaSetu is currently being curated for the NCERT curriculum.'
  };

  return (
    <div className="placeholder-page-wrapper">
      <div className="placeholder-paper-slip">
        <div className="slip-tape" aria-hidden="true" />
        <span className="slip-bookmark-icon">🔖</span>
        <h2 className="slip-sanskrit-title" lang="sa">{meta.sanskritTitle}</h2>
        <h3 className="slip-latin-subtitle">{meta.latinSubtitle}</h3>
        <p className="slip-description">{meta.description}</p>
        <div className="slip-margin-annotation">
          <span className="pencil-hand">✍️</span>
          <span>शीघ्रमेव आगमिष्यति (Coming Soon)</span>
        </div>
      </div>
    </div>
  );
}
