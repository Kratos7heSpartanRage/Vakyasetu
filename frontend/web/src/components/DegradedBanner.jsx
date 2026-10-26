import React, { useState } from 'react';

export default function DegradedBanner({ warnings }) {
  const [open, setOpen] = useState(false);

  return (
    <div className="degraded-notice-banner" role="alert">
      <div className="banner-main">
        <span className="banner-icon" aria-hidden="true">⚠️</span>
        <div className="banner-text">
          <strong>Sandhi checker is offline:</strong> results below are unverified heuristic estimates.
        </div>
        {warnings && warnings.length > 0 && (
          <button
            type="button"
            className="banner-toggle-btn"
            onClick={() => setOpen(!open)}
            aria-expanded={open}
          >
            {open ? 'Hide notes ▲' : `View notes (${warnings.length}) ▼`}
          </button>
        )}
      </div>

      {open && warnings && warnings.length > 0 && (
        <ul className="banner-notes-list">
          {warnings.map((w, idx) => (
            <li key={idx}>{w}</li>
          ))}
        </ul>
      )}
    </div>
  );
}
