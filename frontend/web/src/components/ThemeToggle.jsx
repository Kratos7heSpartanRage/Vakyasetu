import React from 'react';

export default function ThemeToggle({ theme, onToggle }) {
  const isNight = theme === 'night';

  return (
    <button
      type="button"
      className="theme-toggle-btn"
      onClick={onToggle}
      aria-label={`Switch to ${isNight ? 'Day ("Paper")' : 'Night ("Lamp")'} theme`}
      title={`Switch to ${isNight ? 'Paper (Day)' : 'Lamp (Night)'} mode`}
    >
      <div className={`theme-toggle-track ${isNight ? 'is-night' : 'is-day'}`}>
        <div className="theme-toggle-thumb">
          {isNight ? (
            /* Crescent Moon Icon */
            <svg viewBox="0 0 24 24" width="13" height="13" fill="currentColor">
              <path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z" />
            </svg>
          ) : (
            /* Warm Sun Icon */
            <svg viewBox="0 0 24 24" width="13" height="13" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round">
              <circle cx="12" cy="12" r="5" fill="currentColor" />
              <line x1="12" y1="1" x2="12" y2="3" />
              <line x1="12" y1="21" x2="12" y2="23" />
              <line x1="4.22" y1="4.22" x2="5.64" y2="5.64" />
              <line x1="18.36" y1="18.36" x2="19.78" y2="19.78" />
              <line x1="1" y1="12" x2="3" y2="12" />
              <line x1="21" y1="12" x2="23" y2="12" />
              <line x1="4.22" y1="19.78" x2="5.64" y2="18.36" />
              <line x1="18.36" y1="5.64" x2="19.78" y2="4.22" />
            </svg>
          )}
        </div>
      </div>
      <span className="theme-label-text">
        {isNight ? 'दीपः' : 'पत्रम्'}
      </span>
    </button>
  );
}
