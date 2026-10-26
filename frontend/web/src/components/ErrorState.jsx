import React from 'react';

export default function ErrorState({ error, onRetry }) {
  return (
    <div className="error-state-card" role="alert">
      <div className="error-icon" aria-hidden="true">🍂</div>
      <h3 className="error-title">त्रुटिः सञ्जाता (Unable to Complete Analysis)</h3>
      <p className="error-message">
        The computational engine could not process this sentence right now. Please ensure your sentence is in valid Devanagari script or try again.
      </p>

      {error && (
        <div className="error-details-box">
          <span className="details-label">Notice:</span> {error}
        </div>
      )}

      {onRetry && (
        <button type="button" className="paper-btn btn-primary" onClick={onRetry}>
          पुनः प्रयतताम् (Retry Analysis)
        </button>
      )}
    </div>
  );
}
