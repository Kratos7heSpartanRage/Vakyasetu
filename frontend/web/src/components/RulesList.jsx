import React from 'react';

export default function RulesList({
  rules = [],
  highlightedRule,
  onToggleRuleHighlight,
  onSelectRuleDetail
}) {
  if (!rules || rules.length === 0) {
    return (
      <div className="rules-empty-note">
        <span className="pencil-check">✓</span>
        <span>अस्मिन् वाक्ये अतिरिक्त-सन्धि-नियमाः न प्राप्ताः (All words already in citation form).</span>
      </div>
    );
  }

  return (
    <div className="rules-found-section" aria-label="Identified Sandhi rules">
      <div className="rules-heading-row">
        <h4 className="rules-title">
          <span className="rules-icon" aria-hidden="true">📜</span>
          <span>प्रयुक्ताः सन्धि-नियमाः (Rules Applied):</span>
        </h4>
        <span className="rules-count-pill">{rules.length} Rule{rules.length > 1 ? 's' : ''}</span>
      </div>

      <div className="rules-cards-grid">
        {rules.map((rule, idx) => {
          const isHighlighted = highlightedRule === rule.rule_name || highlightedRule === rule.sutra;
          return (
            <div
              key={idx}
              className={`rule-card-item ${isHighlighted ? 'is-rule-active' : ''}`}
              onClick={() => onToggleRuleHighlight(rule.rule_name)}
              role="button"
              tabIndex={0}
              onKeyDown={(e) => {
                if (e.key === 'Enter' || e.key === ' ') {
                  onToggleRuleHighlight(rule.rule_name);
                }
              }}
              title="Click to cross-highlight tokens where this rule applied"
            >
              <div className="rule-card-top">
                <span className="rule-category-badge">{rule.sandhi_type || 'स्वरसन्धिः'}</span>
                <span className="rule-junction-cite" lang="sa">{rule.junction}</span>
              </div>

              <div className="rule-card-main">
                <span className="rule-name-text" lang="sa">{rule.rule_name}</span>
                <span className="rule-sutra-text" lang="sa">{rule.sutra}</span>
              </div>

              <p className="rule-snippet-text">{rule.explanation_en || rule.explanation}</p>

              <div className="rule-card-action">
                <button
                  type="button"
                  className="inspect-rule-btn"
                  onClick={(e) => {
                    e.stopPropagation();
                    onSelectRuleDetail({ rule, left: '', right: '', changed: true });
                  }}
                >
                  Inspect details →
                </button>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
