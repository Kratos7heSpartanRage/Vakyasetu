import React from 'react';

export default function EmptyState({ loading }) {
  if (loading) {
    return (
      <div className="empty-state-card is-loading-state" aria-live="polite">
        <div className="ink-quill-animation">
          <svg viewBox="0 0 64 64" width="48" height="48" fill="none" stroke="currentColor">
            <path
              className="quill-stroke"
              d="M12,52 C24,46 42,28 52,12 C44,14 36,20 30,26 C26,30 20,40 12,52 Z"
              strokeWidth="2.5"
              strokeLinejoin="round"
            />
            <path
              className="ink-line-stroke"
              d="M10,54 Q24,50 48,54"
              strokeWidth="2"
              strokeLinecap="round"
            />
          </svg>
        </div>
        <h3 className="loading-state-title">लेखनी प्रचलति (Analyzing Sanskrit sentence)...</h3>
        <p className="loading-state-sub">Consulting Pāṇinian sūtras and vocabulary lexicons</p>

        {/* Skeleton paper slips */}
        <div className="skeleton-slips-row" aria-hidden="true">
          <div className="skeleton-slip slip-1" />
          <div className="skeleton-slip slip-2" />
          <div className="skeleton-slip slip-3" />
        </div>
      </div>
    );
  }

  return (
    <div className="empty-state-card is-idle-state">
      <div className="idle-quill-icon" aria-hidden="true">📖</div>
      <h3 className="idle-state-title">आरभताम् (Ready to Begin)</h3>
      <p className="idle-state-sub">
        Enter a Sanskrit sentence above in Devanagari or pick an example bookmark to begin.
      </p>
    </div>
  );
}
