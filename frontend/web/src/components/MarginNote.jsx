import React, { useEffect } from 'react';

export default function MarginNote({ junctionData, onClose }) {
  useEffect(() => {
    const handleKeyDown = (e) => {
      if (e.key === 'Escape') {
        onClose();
      }
    };
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [onClose]);

  if (!junctionData) return null;

  const { left, right, changed, rule } = junctionData;

  // Tiny sketch generation helper
  const getPhoneticSketch = () => {
    if (!rule) return null;
    if (rule.rule_name && rule.rule_name.includes('दीर्घ')) {
      return 'अ / आ + अ / आ → आ';
    }
    if (rule.rule_name && rule.rule_name.includes('गुण')) {
      return 'अ / आ + इ / ई → ए';
    }
    if (rule.rule_name && rule.rule_name.includes('वृद्धि')) {
      return 'अ / आ + ए / ऐ → ऐ';
    }
    if (rule.rule_name && rule.rule_name.includes('यण्')) {
      return 'इ / उ / ऋ + स्वर → य् / व् / र्';
    }
    if (rule.rule_name && rule.rule_name.includes('विसर्ग')) {
      return 'ः + स्वर / व्यञ्जन → सन्धि-रूपांतरणम्';
    }
    return `${left} + ${right}`;
  };

  return (
    <aside
      className="margin-note-sheet"
      role="dialog"
      aria-labelledby="margin-note-title"
      aria-modal="false"
    >
      <div className="sheet-header">
        <div className="sheet-badge">
          <span className="ink-quill-icon" aria-hidden="true">📜</span>
          <span className="badge-caption">सूत्र-निर्देशिका (Pāṇinian Rule)</span>
        </div>
        <button
          type="button"
          className="sheet-close-btn"
          onClick={onClose}
          aria-label="Close rule note"
          title="Close (Esc)"
        >
          ✕
        </button>
      </div>

      <div className="sheet-body">
        {rule ? (
          <>
            <div className="rule-title-group">
              <h4 id="margin-note-title" className="rule-name-devanagari" lang="sa">
                {rule.rule_name}
              </h4>
              <div className="ashtadhyayi-sutra-tag" lang="sa">
                {rule.sutra}
              </div>
            </div>

            {/* Tiny Before/After Sketch */}
            <div className="phonetic-sketch-box" aria-label="Phonetic transformation sketch">
              <span className="sketch-label">Phonetic Process:</span>
              <code className="sketch-code">{getPhoneticSketch()}</code>
            </div>

            {/* Hindi Explanation (सूत्रार्थः) */}
            <div className="explanation-block hindi-block">
              <span className="block-label">सूत्रार्थः (Hindi):</span>
              <p className="block-text" lang="hi">{rule.explanation}</p>
            </div>

            {/* English Explanation */}
            {rule.explanation_en && (
              <div className="explanation-block english-block">
                <span className="block-label">Explanation (English):</span>
                <p className="block-text">{rule.explanation_en}</p>
              </div>
            )}
          </>
        ) : (
          <div className="unchanged-boundary-note">
            <h4 id="margin-note-title" className="unchanged-title">पद-सन्निधिः (Word Boundary)</h4>
            <div className="phonetic-sketch-box">
              <code className="sketch-code">{left} + {right}</code>
            </div>
            <p className="block-text">
              {changed === false 
                ? "Written together as continuous text; no phonetic letter alteration took place at this boundary."
                : "Word boundary segmented according to citation lexicon form."}
            </p>
          </div>
        )}
      </div>

      <div className="sheet-footer">
        <span className="sheet-footer-hint">Press Esc or click ✕ to dismiss</span>
      </div>
    </aside>
  );
}
