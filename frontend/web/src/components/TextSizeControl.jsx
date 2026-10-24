import React from 'react';

const SCALE_STEPS = [0.88, 1.0, 1.12, 1.24];

export default function TextSizeControl({ fontScale, onScaleChange }) {
  const currentIndex = SCALE_STEPS.findIndex(s => Math.abs(s - fontScale) < 0.04);
  const safeIndex = currentIndex === -1 ? 1 : currentIndex;

  const handleDecrease = () => {
    if (safeIndex > 0) {
      onScaleChange(SCALE_STEPS[safeIndex - 1]);
    }
  };

  const handleIncrease = () => {
    if (safeIndex < SCALE_STEPS.length - 1) {
      onScaleChange(SCALE_STEPS[safeIndex + 1]);
    }
  };

  return (
    <div className="text-size-control" aria-label="Text size control" role="group">
      <button
        type="button"
        className="size-btn"
        onClick={handleDecrease}
        disabled={safeIndex === 0}
        aria-label="Decrease text size"
        title="Decrease text size (A-)"
      >
        <span className="size-symbol small">A-</span>
      </button>

      <span className="size-indicator" aria-hidden="true">
        {Math.round(fontScale * 100)}%
      </span>

      <button
        type="button"
        className="size-btn"
        onClick={handleIncrease}
        disabled={safeIndex === SCALE_STEPS.length - 1}
        aria-label="Increase text size"
        title="Increase text size (A+)"
      >
        <span className="size-symbol large">A+</span>
      </button>
    </div>
  );
}
