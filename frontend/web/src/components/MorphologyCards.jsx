import React from 'react';

export default function MorphologyCards({
  morphology = [],
  selectedWord,
  onSelectWord
}) {
  if (!morphology || morphology.length === 0) {
    return null;
  }

  return (
    <div className="textbook-chapter-section morphology-section">
      <div className="section-heading-row">
        <h3 className="textbook-subheading">
          <span className="heading-num">३.</span> पद-परिचयः (NCERT Morphological Breakdown)
        </h3>
        <span className="section-badge-hint">CBSE Classes 6–10 Syllabus</span>
      </div>

      <p className="section-intro-note">
        Morphological parsing of each separated citation word in grammatical context. Click a card to cross-highlight its token above.
      </p>

      <div className="morphology-cards-grid">
        {morphology.map((item, idx) => {
          const gloss = item.primary_gloss || {};
          const cleanWord = item.word ? item.word.replace(/[।,॥.?!;:\"'()]/g, "").trim() : "";
          const isSelected = selectedWord && (
            selectedWord.replace(/[।,॥.?!;:\"'()]/g, "").trim() === cleanWord
          );

          return (
            <div
              key={idx}
              id={`morph-card-${cleanWord}`}
              className={`morph-textbook-card ${isSelected ? 'is-selected-card' : ''}`}
              onClick={() => onSelectWord(cleanWord)}
              role="button"
              tabIndex={0}
              onKeyDown={(e) => {
                if (e.key === 'Enter' || e.key === ' ') {
                  onSelectWord(cleanWord);
                }
              }}
            >
              {/* Card Top: Word & POS Tag */}
              <div className="card-top-row">
                <span className="morph-word-title" lang="sa">{item.word}</span>
                <span className="morph-pos-badge">{gloss.pos || 'पदम्'}</span>
              </div>

              {/* Compact Grammatical Features Table */}
              <dl className="morph-props-dl">
                {gloss.root && (
                  <div className="prop-row">
                    <dt className="prop-term">मूलम् (Root/Stem):</dt>
                    <dd className="prop-def" lang="sa">{gloss.root}</dd>
                  </div>
                )}
                {gloss.gender && (
                  <div className="prop-row">
                    <dt className="prop-term">लिङ्गम् (Gender):</dt>
                    <dd className="prop-def">{gloss.gender}</dd>
                  </div>
                )}
                {gloss.case && (
                  <div className="prop-row">
                    <dt className="prop-term">विभक्तिः (Case):</dt>
                    <dd className="prop-def">{gloss.case}</dd>
                  </div>
                )}
                {gloss.number && (
                  <div className="prop-row">
                    <dt className="prop-term">वचनम् (Number):</dt>
                    <dd className="prop-def">{gloss.number}</dd>
                  </div>
                )}
                {gloss.tense && (
                  <div className="prop-row">
                    <dt className="prop-term">लकारः (Tense):</dt>
                    <dd className="prop-def">{gloss.tense}</dd>
                  </div>
                )}
                {item.karaka_role && (
                  <div className="prop-row karaka-highlight">
                    <dt className="prop-term">कारकम् (Kāraka):</dt>
                    <dd className="prop-def">{item.karaka_role}</dd>
                  </div>
                )}
              </dl>

              {/* Explanations */}
              <div className="card-explanation-footer">
                <p className="sanskrit-gloss-note" lang="sa">
                  {gloss.sanskrit_explanation || ''}
                </p>
                {gloss.english_explanation && (
                  <p className="english-gloss-note">
                    {gloss.english_explanation}
                  </p>
                )}
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
