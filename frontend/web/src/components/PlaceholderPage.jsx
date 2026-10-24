import React from 'react';

const TAB_METADATA = {
  practice: {
    sanskritTitle: 'अभ्यास-कक्षा (Interactive Practice)',
    latinSubtitle: 'Self-Testing & Sandhi Exercises',
    description: 'Interactive Sandhi reconstruction puzzles, compound identification drills, and fill-in-the-blank exercises from NCERT Ruchira and Shemushi textbooks are being prepared for you.'
  },
  library: {
    sanskritTitle: 'एनसीईआरटी-ग्रन्थालयः (NCERT Library)',
    latinSubtitle: 'Class 6–10 Textbook Repository',
    description: 'Complete verified chapters from Ruchira (Classes 6-8) and Shemushi (Classes 9-10) with verified word-by-word sandhi annotations and glossary links.'
  },
  guide: {
    sanskritTitle: 'पाणिनीय-सन्धि-निर्देशिका (Pāṇinian Sandhi Guide)',
    latinSubtitle: 'Sūtra Rules, Phonetic Shifts & Tables',
    description: 'Comprehensive pedagogical charts detailing Swara-Sandhi (दीर्घ, गुण, वृद्धि, यण्, अयादि, पूर्वरूप), Vyanjana-Sandhi (श्चुत्व, ष्टुत्व, जश्त्व, अनुनासिक), and Visarga-Sandhi (उत्व, रुत्व, सत्व, लोप).'
  },
  about: {
    sanskritTitle: 'वाक्यसेतु-परिचयः (About VākyaSetu)',
    latinSubtitle: 'Semester 5 Natural Language Processing Academic Project',
    description: 'VākyaSetu is an academic Sanskrit pedagogical assistant developed for school students. It combines computational Pāṇinian morphological disambiguation with state-of-the-art neural translation models.'
  }
};

export default function PlaceholderPage({ tabId }) {
  const meta = TAB_METADATA[tabId] || {
    sanskritTitle: 'आगामी-विभागः (Coming Soon)',
    latinSubtitle: 'Feature Under Construction',
    description: 'This section of VākyaSetu is currently being curated for the NCERT curriculum.'
  };

  return (
    <div className="placeholder-page-wrapper">
      <div className="placeholder-paper-slip">
        <div className="slip-tape" aria-hidden="true" />
        <span className="slip-bookmark-icon">🔖</span>
        <h2 className="slip-sanskrit-title" lang="sa">{meta.sanskritTitle}</h2>
        <h3 className="slip-latin-subtitle">{meta.latinSubtitle}</h3>
        <p className="slip-description">{meta.description}</p>
        <div className="slip-margin-annotation">
          <span className="pencil-hand">✍️</span>
          <span>शीघ्रमेव आगमिष्यति (Coming Soon)</span>
        </div>
      </div>
    </div>
  );
}
