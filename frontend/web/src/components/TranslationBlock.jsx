import React, { useState } from 'react';

export default function TranslationBlock({ translation }) {
  const [copied, setCopied] = useState(false);

  const handleCopy = () => {
    if (!translation) return;
    navigator.clipboard.writeText(translation);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <div className="textbook-chapter-section translation-section">
      <div className="section-heading-row">
        <h3 className="textbook-subheading">
          <span className="heading-num">१.</span> आङ्ग्लानुवादः (English Translation)
        </h3>
        <button
          type="button"
          className="ink-copy-btn"
          onClick={handleCopy}
          aria-label="Copy English translation"
          title="Copy English translation"
        >
          {copied ? '✓ Copied' : '📋 Copy translation'}
        </button>
      </div>

      <div className="translation-quote-wrapper">
        <blockquote className="textbook-blockquote">
          <p className="translation-text">“{translation}”</p>
        </blockquote>
        <aside className="margin-annotation-note" aria-label="Translation margin note">
          <span className="handwritten-arrow" aria-hidden="true">✎</span>
          <span className="handwritten-text">Natural English sentence reading</span>
        </aside>
      </div>
    </div>
  );
}
