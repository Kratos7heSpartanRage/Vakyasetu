import React, { useRef } from 'react';

export default function InputPaper({
  inputText,
  setInputText,
  onAnalyze,
  onClear,
  loading
}) {
  const textareaRef = useRef(null);

  const handleKeyDown = (e) => {
    // Submit on Ctrl+Enter or Cmd+Enter
    if ((e.ctrlKey || e.metaKey) && e.key === 'Enter') {
      e.preventDefault();
      onAnalyze();
    }
  };

  return (
    <section className="hero-input-section" aria-label="Sanskrit sentence input">
      <div className="ruled-paper-container">
        {/* Notebook header banner */}
        <div className="paper-top-strip">
          <span className="strip-title" lang="sa">संस्कृतवाक्यम् (Enter Sentence)</span>
          <span className="strip-hint">Ctrl + Enter to analyse</span>
        </div>

        {/* Ruled Notebook Writing Surface */}
        <div className="paper-writing-surface">
          <div className="paper-margin-rule" aria-hidden="true" />
          <textarea
            ref={textareaRef}
            id="sanskrit-sentence-input"
            className="ruled-textarea"
            lang="sa"
            rows={3}
            value={inputText}
            onChange={(e) => setInputText(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="अत्र देवनागरी-संस्कृतवाक्यं लिखतु... (उदा. बालकः विद्यालयं गच्छति।)"
            aria-label="Enter Sanskrit Sentence in Devanagari"
            disabled={loading}
          />
        </div>

        {/* Action Controls Toolbar */}
        <div className="paper-actions-bar">
          <div className="actions-left-note">
            <span className="pencil-note">✏️ Devanagari Unicode</span>
          </div>
          <div className="actions-right-buttons">
            <button
              type="button"
              className="paper-btn btn-secondary"
              onClick={onClear}
              disabled={loading || (!inputText && true)}
            >
              साफ करें (Clear)
            </button>
            <button
              type="button"
              id="analyze-sentence-btn"
              className="paper-btn btn-primary"
              onClick={() => onAnalyze()}
              disabled={loading || !inputText.trim()}
            >
              {loading ? (
                <>
                  <span className="ink-quill-loader" aria-hidden="true" />
                  <span>विश्लेषणं भवति...</span>
                </>
              ) : (
                <>
                  <span>विश्लेषणम् (Analyse)</span>
                  <span className="btn-arrow" aria-hidden="true">→</span>
                </>
              )}
            </button>
          </div>
        </div>
      </div>
    </section>
  );
}
