# VākyaSetu Front-End (React 19 + Vite)

Nostalgic NCERT school textbook interface for computational Sanskrit Sandhi segmentation, Pāṇinian sūtra verification, and morphological parsing.

---

## 1. Quick Start (Running Locally)

```bash
# Navigate to the web frontend directory
cd frontend/web

# Install dependencies
npm install

# Start the Vite development server (proxies /api to FastAPI on port 8000)
npm run dev
```

Visit **`http://localhost:3000`** in your browser.

---

## 2. Architecture & File Structure

```text
frontend/web/
├── index.html                   # Pre-paint theme hydration script & Google Fonts
├── vite.config.js               # Dev server port 3000 & /api reverse proxy
└── src/
    ├── config/
    │   ├── examples.js          # School textbook bookmark presets
    │   └── mockData.js          # Offline mock data covering all 5 Sandhi statuses
    ├── components/
    │   ├── Header.jsx           # Brand lockup, bridge motif, tabs, controls
    │   ├── ThemeToggle.jsx      # Animated Day/Night switch (Sun sets / Moon rises)
    │   ├── TextSizeControl.jsx  # Dynamic font scaler (A- / A+)
    │   ├── LiveBackground.jsx   # Parallax ruled grid, drifting Devanagari letters
    │   ├── InputPaper.jsx       # Ruled-paper textarea with pencil feel (Ctrl+Enter)
    │   ├── ExampleChips.jsx     # Bookmark ribbon example chips
    │   ├── ResultChapter.jsx    # Chapter container with numbered textbook sections
    │   ├── TranslationBlock.jsx # Section 1: English translation & margin note
    │   ├── SandhiStrip.jsx      # Section 2: Interactive sentence strip centrepiece
    │   ├── TokenSlip.jsx        # Individual paper slip per written token
    │   ├── WordChip.jsx         # Segmented word chip with status & evidence tooltip
    │   ├── MarginNote.jsx       # Side/bottom sheet for Pāṇinian sūtra breakdown
    │   ├── RulesList.jsx        # Applied rules list with cross-highlighting
    │   ├── MorphologyCards.jsx  # Section 3: NCERT Pada-Parichaya cards
    │   ├── DegradedBanner.jsx   # Offline/heuristic alert banner
    │   ├── EmptyState.jsx       # Loading ink quill & ready states
    │   ├── ErrorState.jsx       # Zero code-leak error card with retry button
    │   └── PlaceholderPage.jsx  # Coming soon paper notes for inactive tabs
    ├── styles/
    │   ├── tokens.css           # All color, radius, spacing, and typography tokens
    │   ├── background.css       # Living wallpaper layers and drift animations
    │   ├── components.css       # Component layout and textbook nostalgia styling
    │   └── responsive.css       # Mobile-first overrides (360px up) and bottom sheets
    ├── App.jsx                  # Main orchestration, state, and cross-highlighting
    └── index.css                # Base resets, Google font mappings, and token imports
```

---

## 3. How to Customise or Change Theme Tokens

All design tokens live in **`src/styles/tokens.css`**:

* **Day ("Paper")**: Edit variables under `:root` (e.g. `--bg-paper`, `--text-ink`, `--color-accent`, `--line-ruled`).
* **Night ("Lamp")**: Edit variables under `[data-theme="night"]` (e.g. `--bg-paper: #12141C`, `--color-accent: #E5B25D`).
* **Spacing Scale**: Defined via `--space-4`, `--space-8`, `--space-12`, `--space-16`, `--space-24`, `--space-32`, `--space-48`.
* **Radii**: Defined via `--radius-sm` (3px), `--radius-md` (6px), `--radius-lg` (10px).

Every component in `src/styles/components.css` strictly consumes these tokens.

---

## 4. How to Add a New Tab

1. Open `src/components/Header.jsx`.
2. Add your tab to the `tabs` array:
   ```javascript
   { id: 'quiz', label: 'प्रश्नोत्तरी (Quiz)' }
   ```
3. Open `src/components/PlaceholderPage.jsx` to define its title and description in `TAB_METADATA`:
   ```javascript
   quiz: {
     sanskritTitle: 'प्रश्नोत्तरी-कक्ष्या (Sanskrit Quiz)',
     latinSubtitle: 'Interactive Multiple-Choice Questions',
     description: 'Test your Sandhi identification and Sanskrit vocabulary skills.'
   }
   ```
4. In `src/App.jsx`, render your custom page when `activeTab === 'quiz'` inside `notebook-page-viewport`.
