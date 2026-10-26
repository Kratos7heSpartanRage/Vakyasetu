import React, { useState } from 'react';
import TokenSlip from './TokenSlip';
import RulesList from './RulesList';
import MarginNote from './MarginNote';

export default function SandhiStrip({
  tokens = [],
  rules = [],
  splitWords = [],
  selectedWord,
  onSelectWord,
  onSelectAlternative
}) {
  const [activeJunction, setActiveJunction] = useState(null);
  const [highlightedRule, setHighlightedRule] = useState(null);
  const [copiedWords, setCopiedWords] = useState(false);

  const handleCopyWords = () => {
    if (!splitWords || splitWords.length === 0) return;
    navigator.clipboard.writeText(splitWords.join(' '));
    setCopiedWords(true);
    setTimeout(() => setCopiedWords(false), 2000);
  };

  const handleToggleRuleHighlight = (ruleName) => {
    setHighlightedRule(prev => prev === ruleName ? null : ruleName);
  };

  return (
    <div className="textbook-chapter-section sandhi-centrepiece-section">
      <div className="section-heading-row">
        <h3 className="textbook-subheading">
          <span className="heading-num">२.</span> सन्धि-विच्छेदः (Sandhi Segmentation &amp; Reconstructions)
        </h3>
        <button
          type="button"
          className="ink-copy-btn"
          onClick={handleCopyWords}
          aria-label="Copy separated words"
          title="Copy segmented words list"
        >
          {copiedWords ? '✓ Copied words' : '📋 Copy words (पदानि)'}
        </button>
      </div>

      <p className="section-intro-note">
        Each slip of paper represents one written token from your sentence. Click any separated word to inspect its morphology below, or click <span className="inline-plus">+</span> to view the Pāṇinian sūtra.
      </p>

      {/* Main Sentence Strip Container */}
      <div className="sentence-strip-scroll-wrapper" role="region" aria-label="Sentence token strip">
        <div className="sentence-strip-flex-row">
          {tokens.map((token, idx) => (
            <TokenSlip
              key={idx}
              token={token}
              tokenIndex={idx}
              selectedWord={selectedWord}
              onSelectWord={onSelectWord}
              onSelectJunction={(j) => setActiveJunction(j)}
              onSelectAlternative={onSelectAlternative}
              highlightedRule={highlightedRule}
            />
          ))}
        </div>
      </div>

      {/* Rules Found List */}
      <RulesList
        rules={rules}
        highlightedRule={highlightedRule}
        onToggleRuleHighlight={handleToggleRuleHighlight}
        onSelectRuleDetail={(j) => setActiveJunction(j)}
      />

      {/* Slide-out / Bottom-sheet Margin Note */}
      {activeJunction && (
        <MarginNote
          junctionData={activeJunction}
          onClose={() => setActiveJunction(null)}
        />
      )}
    </div>
  );
}
