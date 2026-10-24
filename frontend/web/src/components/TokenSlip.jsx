import React from 'react';
import WordChip from './WordChip';

export default function TokenSlip({
  token,
  tokenIndex,
  selectedWord,
  onSelectWord,
  onSelectJunction,
  onSelectAlternative,
  highlightedRule
}) {
  const { surface, words = [], status, junctions = [] } = token;
  const isSplit = words.length > 1;

  // Check if any junction matches highlighted rule
  const isRuleActive = highlightedRule && junctions.some(j => 
    j.rule && (j.rule.rule_name === highlightedRule || j.rule.sutra === highlightedRule)
  );

  return (
    <div
      className={`token-slip-card ${isSplit ? 'is-split-token' : 'is-intact-token'} ${isRuleActive ? 'rule-cross-highlight' : ''}`}
      id={`token-slip-${tokenIndex}`}
    >
      {/* Written Surface Form on Top */}
      <div className="token-surface-wrapper">
        <span className="surface-text" lang="sa">{surface}</span>
        <span className="token-index-tag">#{tokenIndex + 1}</span>
      </div>

      {/* Downward Un-fusing Separation Indicator */}
      {isSplit && (
        <div className="unfusing-flow-line" aria-hidden="true">
          <svg viewBox="0 0 24 12" width="18" height="8" fill="none" stroke="currentColor">
            <path d="M12,0 L12,8 M8,5 L12,9 L16,5" strokeWidth="1.5" />
          </svg>
        </div>
      )}

      {/* Resulting Word Chips Underneath */}
      <div className={`resulting-words-row ${isSplit ? 'unfusing-animated' : ''}`}>
        {words.map((w, wIdx) => {
          const junction = junctions[wIdx];
          const isSelected = selectedWord === w;

          return (
            <React.Fragment key={wIdx}>
              <WordChip
                word={w}
                token={token}
                isSelected={isSelected}
                onSelectWord={onSelectWord}
                onSelectAlternative={onSelectAlternative}
              />

              {/* Junction Trigger between adjacent words */}
              {wIdx < words.length - 1 && (
                <button
                  type="button"
                  className={`junction-marker-btn ${junction ? 'has-rule' : ''}`}
                  onClick={() => onSelectJunction(junction || { left: w, right: words[wIdx + 1], changed: false })}
                  title={junction && junction.rule ? `Inspect rule: ${junction.rule.rule_name}` : "Word boundary"}
                  aria-label={`Inspect sandhi boundary between ${w} and ${words[wIdx + 1]}`}
                >
                  <span className="junction-plus">+</span>
                </button>
              )}
            </React.Fragment>
          );
        })}
      </div>

      {/* Unattested Margin Note */}
      {status === 'unattested' && (
        <div className="unattested-margin-flag" role="note">
          <span className="flag-pencil">✎</span>
          <span className="flag-text">not found in the dictionary, kept as one word</span>
        </div>
      )}
    </div>
  );
}
