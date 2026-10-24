import React from 'react';
import TranslationBlock from './TranslationBlock';
import SandhiStrip from './SandhiStrip';
import MorphologyCards from './MorphologyCards';
import DegradedBanner from './DegradedBanner';

export default function ResultChapter({
  analysis,
  selectedWord,
  onSelectWord,
  onSelectAlternative
}) {
  if (!analysis) return null;

  const {
    translation,
    sandhi_tokens = [],
    sandhi_rules = [],
    sandhi_splits = [],
    sandhi_degraded,
    sandhi_warnings = [],
    morphology = [],
    cached,
    processing_time_ms
  } = analysis;

  return (
    <article className="result-chapter-container" aria-live="polite">
      {/* Chapter Title & Provenance Strip */}
      <div className="chapter-header-bar">
        <div className="chapter-title-group">
          <span className="chapter-rubric" lang="sa">अध्यायः १</span>
          <h2 className="chapter-main-title">वाक्य-विश्लेषण-परिणामः (Analysis Results)</h2>
        </div>

        {/* Real latency & cache indicator (No marketing claims) */}
        <div className="chapter-meta-pills">
          {processing_time_ms !== undefined && (
            <span className="meta-pill latency-pill">
              ⏱ Analysed in {Math.round(processing_time_ms)} ms
            </span>
          )}
          {cached && (
            <span className="meta-pill cache-pill">
              💾 from cache
            </span>
          )}
        </div>
      </div>

      {/* Degraded offline banner if applicable */}
      {sandhi_degraded && (
        <DegradedBanner warnings={sandhi_warnings} />
      )}

      {/* Section 1: English Translation */}
      <TranslationBlock translation={translation} />

      <hr className="textbook-divider-rule" aria-hidden="true" />

      {/* Section 2: Sandhi-viccheda (Centrepiece) */}
      <SandhiStrip
        tokens={sandhi_tokens}
        rules={sandhi_rules}
        splitWords={sandhi_splits}
        selectedWord={selectedWord}
        onSelectWord={onSelectWord}
        onSelectAlternative={onSelectAlternative}
      />

      <hr className="textbook-divider-rule" aria-hidden="true" />

      {/* Section 3: Morphology Breakdown */}
      <MorphologyCards
        morphology={morphology}
        selectedWord={selectedWord}
        onSelectWord={onSelectWord}
      />

      {/* Chapter Footer: Honest Scope Note */}
      <footer className="chapter-footer-note">
        <div className="footer-scope-box">
          <span className="quill-tag" aria-hidden="true">✎</span>
          <p className="scope-text">
            <strong>Honest Scope Note:</strong> Text only. Computational Sandhi splitting is a non-trivial phonetic disambiguation problem; unsure results are explicitly flagged with evidence heuristics, not hidden. Designed for CBSE/NCERT Sanskrit students.
          </p>
        </div>
      </footer>
    </article>
  );
}
