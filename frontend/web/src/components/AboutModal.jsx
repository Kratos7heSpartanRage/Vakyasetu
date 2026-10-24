import React, { useEffect } from 'react';

export default function AboutModal({ isOpen, onClose }) {
  useEffect(() => {
    const handleKeyDown = (e) => {
      if (e.key === 'Escape') onClose();
    };
    if (isOpen) {
      window.addEventListener('keydown', handleKeyDown);
      document.body.style.overflow = 'hidden';
    }
    return () => {
      window.removeEventListener('keydown', handleKeyDown);
      document.body.style.overflow = 'unset';
    };
  }, [isOpen, onClose]);

  if (!isOpen) return null;

  return (
    <div className="about-modal-backdrop" onClick={onClose} role="dialog" aria-modal="true" aria-labelledby="about-modal-title">
      <div className="about-modal-sheet" onClick={(e) => e.stopPropagation()}>
        {/* Header */}
        <div className="about-sheet-header">
          <div className="about-brand-group">
            <span className="about-quill-icon" aria-hidden="true">📜</span>
            <div>
              <h2 id="about-modal-title" className="about-title" lang="sa">वाक्यसेतु (VākyaSetu) • प्रकल्प-परिचयः</h2>
              <span className="about-subtitle">Pedagogical Sanskrit Sandhi Segmentation & Learning Assistant</span>
            </div>
          </div>
          <button type="button" className="about-close-btn" onClick={onClose} aria-label="Close About Dialog" title="Close (Esc)">
            ✕
          </button>
        </div>

        {/* Modal Scrollable Body */}
        <div className="about-sheet-body">
          {/* 1. Overview */}
          <section className="about-section">
            <h3 className="section-title">
              <span className="title-icon">🏛️</span>
              <span>Project Mission & Academic Context</span>
            </h3>
            <p className="about-paragraph">
              <strong>VākyaSetu (वाक्यसेतु)</strong> is a semester-long <strong>Natural Language Processing (Semester 5)</strong> academic project. Its mission is to build a reliable, pedagogical bridge for school students (CBSE/NCERT Classes 6–10) learning Sanskrit, connecting ancient computational grammar principles from Pāṇini’s <em>Aṣṭādhyāyī</em> with modern deep-learning Neural Machine Translation.
            </p>
          </section>

          {/* 2. Team & Tracks */}
          <section className="about-section">
            <h3 className="section-title">
              <span className="title-icon">👥</span>
              <span>Project Team & Research Tracks</span>
            </h3>
            <div className="team-grid">
              {/* Mayank */}
              <div className="team-card mayank-card">
                <div className="member-header">
                  <span className="member-avatar">👨‍💻</span>
                  <div>
                    <h4 className="member-name">Mayank Kumar</h4>
                    <span className="member-role">Sandhi Engine, Evaluation &amp; Frontend</span>
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

              {/* Satyam */}
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

              {/* Shrinivas */}
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
          </section>

          {/* 3. System Architecture */}
          <section className="about-section">
            <h3 className="section-title">
              <span className="title-icon">⚙️</span>
              <span>Computational Pipeline</span>
            </h3>
            <div className="pipeline-flow">
              <div className="pipeline-step">
                <span className="step-num">1</span>
                <span className="step-name">Input Sentence</span>
                <span className="step-desc">Unicode NFC Normalizer</span>
              </div>
              <div className="pipeline-arrow">→</div>
              <div className="pipeline-step active-step">
                <span className="step-num">2</span>
                <span className="step-name">Pāṇinian Sandhi</span>
                <span className="step-desc">Aṣṭādhyāyī Sūtra Matcher</span>
              </div>
              <div className="pipeline-arrow">→</div>
              <div className="pipeline-step">
                <span className="step-num">3</span>
                <span className="step-name">IndicTrans2 NMT</span>
                <span className="step-desc">Neural English Translation</span>
              </div>
              <div className="pipeline-arrow">→</div>
              <div className="pipeline-step">
                <span className="step-num">4</span>
                <span className="step-name">Pada-Parichaya</span>
                <span className="step-desc">Morphology &amp; Kāraka Analysis</span>
              </div>
            </div>
          </section>

          {/* 4. Empirical Highlights */}
          <section className="about-section">
            <h3 className="section-title">
              <span className="title-icon">📊</span>
              <span>Empirical Benchmarks</span>
            </h3>
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
          </section>
        </div>

        {/* Footer */}
        <div className="about-sheet-footer">
          <span className="footer-scope">Semester 5 Natural Language Processing • Academic Research Project</span>
          <button type="button" className="paper-btn btn-primary" onClick={onClose}>
            धन्यवादः (Got it)
          </button>
        </div>
      </div>
    </div>
  );
}
