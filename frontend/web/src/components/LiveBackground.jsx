import React, { useEffect, useRef } from 'react';

// Handwritten Hindi and Sanskrit letters & sacred words for school notebook background
const HANDWRITTEN_GLYPHS = [
  { id: 1, char: 'अ', x: 6, y: 12, size: 1.8, rot: -8, delay: 0, dx: 10, dy: -14 },
  { id: 2, char: 'क', x: 22, y: 6, size: 1.5, rot: 6, delay: 1.4, dx: -8, dy: 10 },
  { id: 3, char: 'ॐ', x: 88, y: 10, size: 2.2, rot: -4, delay: 2.1, dx: 12, dy: -8 },
  { id: 4, char: 'इ', x: 74, y: 18, size: 1.4, rot: 5, delay: 0.7, dx: -10, dy: 12 },
  { id: 5, char: 'म', x: 12, y: 28, size: 1.6, rot: -7, delay: 3.2, dx: 8, dy: -12 },
  { id: 6, char: 'त', x: 92, y: 32, size: 1.5, rot: 7, delay: 1.8, dx: -12, dy: 10 },
  { id: 7, char: 'ज्ञ', x: 5, y: 46, size: 1.8, rot: -9, delay: 2.6, dx: 10, dy: -10 },
  { id: 8, char: 'र', x: 84, y: 45, size: 1.5, rot: 6, delay: 0.9, dx: -8, dy: 14 },
  { id: 9, char: 'स', x: 16, y: 62, size: 1.6, rot: -5, delay: 3.5, dx: 12, dy: -8 },
  { id: 10, char: 'श्री', x: 86, y: 60, size: 2.0, rot: 4, delay: 1.6, dx: -10, dy: 12 },
  { id: 11, char: 'ह', x: 8, y: 78, size: 1.5, rot: -8, delay: 2.3, dx: 8, dy: -14 },
  { id: 12, char: 'न', x: 80, y: 76, size: 1.5, rot: 8, delay: 3.7, dx: -12, dy: 10 },
  { id: 13, char: 'ख', x: 28, y: 90, size: 1.4, rot: -4, delay: 1.1, dx: 10, dy: -10 },
  { id: 14, char: 'प', x: 68, y: 86, size: 1.5, rot: 7, delay: 2.8, dx: -8, dy: 12 },
  { id: 15, char: 'च', x: 38, y: 12, size: 1.4, rot: 5, delay: 1.5, dx: 12, dy: -8 },
  { id: 16, char: 'य', x: 62, y: 10, size: 1.5, rot: -6, delay: 3.1, dx: -10, dy: 10 },
  { id: 17, char: 'द', x: 24, y: 46, size: 1.4, rot: 6, delay: 0.8, dx: 8, dy: -12 },
  { id: 18, char: 'भ', x: 72, y: 38, size: 1.5, rot: -8, delay: 2.0, dx: -12, dy: 8 },
  { id: 19, char: 'ग', x: 32, y: 74, size: 1.5, rot: 4, delay: 3.4, dx: 10, dy: -12 },
  { id: 20, char: 'ल', x: 64, y: 68, size: 1.5, rot: -5, delay: 1.3, dx: -8, dy: 10 },
  { id: 21, char: 'व', x: 48, y: 90, size: 1.4, rot: 6, delay: 2.5, dx: 12, dy: -10 },
  { id: 22, char: 'श', x: 48, y: 6, size: 1.5, rot: -4, delay: 0.6, dx: -10, dy: 8 },
  { id: 23, char: 'विद्या', x: 90, y: 88, size: 1.8, rot: 5, delay: 2.9, dx: 10, dy: -12 },
  { id: 24, char: 'सत्यम्', x: 10, y: 92, size: 1.8, rot: -6, delay: 1.7, dx: -12, dy: 10 }
];

export default function LiveBackground({ calmMode }) {
  const notebookRef = useRef(null);
  const lettersLayerRef = useRef(null);

  // Parallax Pointer & Scroll Physics
  useEffect(() => {
    if (calmMode) return;

    let rafId = null;
    let targetX = 0;
    let targetY = 0;
    let currentX = 0;
    let currentY = 0;
    let scrollY = window.scrollY;

    const handlePointerMove = (e) => {
      const nx = (e.clientX / window.innerWidth) * 2 - 1;
      const ny = (e.clientY / window.innerHeight) * 2 - 1;
      targetX = nx * 14; // Subtle 14px tilt
      targetY = ny * 10;
    };

    const handleScroll = () => {
      scrollY = window.scrollY;
    };

    const animate = () => {
      if (!document.hidden) {
        currentX += (targetX - currentX) * 0.05;
        currentY += (targetY - currentY) * 0.05;

        // Ruled notebook sheet subtly responds to scroll
        if (notebookRef.current) {
          notebookRef.current.style.transform = `translate3d(0, ${(scrollY * 0.04).toFixed(1)}px, 0)`;
        }

        // Floating handwritten letters respond to mouse tilt and scroll parallax
        if (lettersLayerRef.current) {
          lettersLayerRef.current.style.transform = `translate3d(${currentX.toFixed(1)}px, ${(currentY - scrollY * 0.06).toFixed(1)}px, 0)`;
        }
      }

      rafId = requestAnimationFrame(animate);
    };

    window.addEventListener('pointermove', handlePointerMove, { passive: true });
    window.addEventListener('scroll', handleScroll, { passive: true });
    rafId = requestAnimationFrame(animate);

    return () => {
      window.removeEventListener('pointermove', handlePointerMove);
      window.removeEventListener('scroll', handleScroll);
      cancelAnimationFrame(rafId);
    };
  }, [calmMode]);

  return (
    <div className={`living-background ${calmMode ? 'is-calm' : ''}`} aria-hidden="true">
      {/* 1. Hindi Notebook Ruled Sheet (Horizontal lines only, like school copy) */}
      <div className="bg-notebook-sheet" ref={notebookRef} />

      {/* 2. Red Student Notebook Margins (Classic double margin down left, plus top header rule) */}
      <div className="bg-notebook-margin-double" />
      <div className="bg-notebook-top-margin" />

      {/* 3. Floating Handwritten Hindi & Sanskrit Letters */}
      <div className="bg-handwritten-layer" ref={lettersLayerRef}>
        {HANDWRITTEN_GLYPHS.map((g) => (
          <span
            key={g.id}
            className="handwritten-floating-letter"
            style={{
              left: `${g.x}%`,
              top: `${g.y}%`,
              fontSize: `${g.size}rem`,
              '--base-rot': `${g.rot}deg`,
              '--float-x': `${g.dx}px`,
              '--float-y': `${g.dy}px`,
              animationDelay: `-${g.delay}s`
            }}
          >
            {g.char}
          </span>
        ))}
      </div>

      {/* 4. Subtle Ambient Warmth Gradient */}
      <div className="bg-paper-warmth-glow" />
    </div>
  );
}
