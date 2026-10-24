import React from 'react';
import ThemeToggle from './ThemeToggle';
import TextSizeControl from './TextSizeControl';

export default function Header({
  theme,
  onToggleTheme,
  fontScale,
  onScaleChange,
  calmMode,
  onToggleCalmMode,
  activeTab,
  onSelectTab,
  onOpenAboutModal
}) {
  const tabs = [
    { id: 'analyse', label: 'विश्लेषणम् (Analyse)' },
    { id: 'practice', label: 'अभ्यासः (Practice)' },
    { id: 'library', label: 'ग्रन्थालयः (NCERT Library)' },
    { id: 'guide', label: 'सन्धि-निर्देशिका (Sandhi Guide)' },
    { id: 'about', label: 'परिचयः (About Us)' }
  ];

  return (
    <header className="site-header">
      <div className="header-top-bar">
        {/* Brand Lockup with Bridge Motif */}
        <div className="brand-lockup">
          <div className="brand-bridge-motif" aria-hidden="true">
            <svg viewBox="0 0 48 24" width="38" height="20" fill="none" stroke="currentColor">
              <path
                d="M4,20 C14,6 34,6 44,20 M14,14 L14,20 M24,10 L24,20 M34,14 L34,20"
                strokeWidth="2.2"
                strokeLinecap="round"
              />
            </svg>
          </div>
          <div className="brand-text-group">
            <h1 className="brand-wordmark" lang="sa">वाक्यसेतु</h1>
            <span className="brand-latin">VākyaSetu</span>
          </div>
          <div className="textbook-badge">
            <span className="badge-tag">NCERT / CBSE</span>
            <span className="badge-sub">Classes 6–10</span>
          </div>
        </div>

        {/* Global Controls: About Project, Calm Mode, Text Size, Day/Night */}
        <div className="header-actions">
          {/* About Project Button */}
          <button
            type="button"
            className="about-project-btn"
            onClick={onOpenAboutModal}
            title="About VākyaSetu Project & Team"
            aria-label="About VākyaSetu Project & Team"
          >
            <span className="about-btn-icon" aria-hidden="true">ℹ️</span>
            <span className="about-btn-text">प्रकल्प-परिचयः (About)</span>
          </button>

          {/* Calm Mode Toggle Button */}
          <button
            type="button"
            className={`calm-mode-btn ${calmMode ? 'is-calm' : ''}`}
            onClick={onToggleCalmMode}
            title={calmMode ? 'Enable dynamic motion' : 'Enable calm mode (no motion)'}
            aria-pressed={calmMode}
          >
            <span className="calm-icon" aria-hidden="true">🍃</span>
            <span className="calm-text">शालीनम् (Calm)</span>
          </button>

          {/* Text Size (A- / A+) */}
          <TextSizeControl fontScale={fontScale} onScaleChange={onScaleChange} />

          {/* Day / Night Theme Switch */}
          <ThemeToggle theme={theme} onToggle={onToggleTheme} />
        </div>
      </div>

      {/* Navigation Tabs Bar */}
      <nav className="header-nav-tabs" aria-label="Main navigation">
        <ul className="tabs-list" role="tablist">
          {tabs.map((t) => {
            const isActive = activeTab === t.id;
            return (
              <li key={t.id} role="presentation">
                <button
                  type="button"
                  role="tab"
                  id={`tab-${t.id}`}
                  aria-selected={isActive}
                  aria-controls={`panel-${t.id}`}
                  className={`tab-btn ${isActive ? 'active' : ''}`}
                  onClick={() => onSelectTab(t.id)}
                >
                  <span className="tab-label">{t.label}</span>
                  {isActive && <span className="tab-ink-indicator" aria-hidden="true" />}
                </button>
              </li>
            );
          })}
        </ul>
      </nav>
    </header>
  );
}
