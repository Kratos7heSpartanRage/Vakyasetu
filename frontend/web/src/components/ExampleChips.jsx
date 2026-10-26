import React from 'react';

export default function ExampleChips({ examples, onSelectExample, activeText }) {
  return (
    <div className="examples-section" aria-label="Sentence examples">
      <div className="examples-header">
        <span className="bookmark-icon" aria-hidden="true">🔖</span>
        <span className="examples-label">Examples (उदाहरणाणि):</span>
      </div>
      <div className="examples-scroll-row" role="list">
        {examples.map((item) => {
          const isSelected = activeText === item.text;
          return (
            <button
              key={item.id}
              type="button"
              role="listitem"
              className={`bookmark-chip ${isSelected ? 'is-selected' : ''}`}
              onClick={() => onSelectExample(item.text)}
              title={item.text}
            >
              <span className="bookmark-ribbon" aria-hidden="true" />
              <span className="bookmark-text">{item.label}</span>
            </button>
          );
        })}
      </div>
    </div>
  );
}
