import React, { useState } from 'react';

export default function WordChip({
  word,
  token,
  isSelected,
  onSelectWord,
  onSelectAlternative
}) {
  const [showAmbiguousMenu, setShowAmbiguousMenu] = useState(false);
  const [showTooltip, setShowTooltip] = useState(false);

  const status = token.status || 'resolved';
  const confidence = token.confidence || 0.9;
  const evidence = token.evidence || [];
  const alternatives = token.alternatives || [];
  const compoundMembers = token.compound_members || [];

  // Confidence Level (heuristic, NOT probability)
  const getConfidenceLevel = () => {
    if (confidence >= 0.8) return { label: 'Strong evidence', level: 'strong' };
    if (confidence >= 0.5) return { label: 'Fair evidence', level: 'fair' };
    return { label: 'Weak evidence', level: 'weak' };
  };

  const conf = getConfidenceLevel();

  const handleChipClick = (e) => {
    if (status === 'ambiguous' && alternatives.length > 0) {
      e.stopPropagation();
      setShowAmbiguousMenu(!showAmbiguousMenu);
    }
    onSelectWord(word);
  };

  const handleSelectAlt = (altWords, e) => {
    e.stopPropagation();
    setShowAmbiguousMenu(false);
    if (onSelectAlternative) {
      onSelectAlternative(token.surface, altWords);
    }
  };

  return (
    <div
      className={`word-chip-container status-${status} ${isSelected ? 'is-selected' : ''}`}
      onMouseEnter={() => setShowTooltip(true)}
      onMouseLeave={() => setShowTooltip(false)}
    >
      <button
        type="button"
        className="word-chip-btn"
        onClick={handleChipClick}
        aria-selected={isSelected}
        aria-label={`${word}, status: ${status}, evidence: ${conf.label}`}
      >
        <span className="chip-text" lang="sa">{word}</span>

        {/* Status Indicators (icon + text, never colour alone) */}
        {status === 'resolved' && (
          <span className="status-badge badge-resolved" title="Resolved citation word" aria-hidden="true">
            ✓
          </span>
        )}

        {status === 'ambiguous' && (
          <span className="status-badge badge-ambiguous" title="Multiple interpretations available">
            ?
          </span>
        )}

        {status === 'compound' && (
          <span className="status-badge badge-compound" title="Compound constituent">
            समास
          </span>
        )}

        {status === 'unattested' && (
          <span className="status-badge badge-unattested" title="Not found in standard dictionary">
            अकोश
          </span>
        )}
      </button>

      {/* Ambiguous Alternatives Popover Menu */}
      {showAmbiguousMenu && alternatives.length > 0 && (
        <div className="alternatives-popover" role="menu">
          <div className="popover-header">Select Alternative:</div>
          <div className="popover-options">
            {alternatives.map((alt, idx) => (
              <button
                key={idx}
                type="button"
                className="alt-option-btn"
                onClick={(e) => handleSelectAlt(alt, e)}
              >
                {alt.join(' + ')}
              </button>
            ))}
          </div>
        </div>
      )}

      {/* Tooltip on Hover showing Evidence & Compound Members */}
      {showTooltip && (
        <div className="chip-hover-tooltip" role="tooltip">
          <div className="tooltip-row evidence-level">
            <span className={`level-dot dot-${conf.level}`} />
            <span>{conf.label}</span>
          </div>
          {compoundMembers.length > 0 && (
            <div className="tooltip-row compound-detail">
              <span className="detail-tag">Compound parts:</span>
              <span className="detail-val">{compoundMembers.join(' + ')}</span>
            </div>
          )}
          {evidence.length > 0 && (
            <ul className="tooltip-evidence-list">
              {evidence.map((ev, i) => (
                <li key={i}>{ev}</li>
              ))}
            </ul>
          )}
        </div>
      )}
    </div>
  );
}
