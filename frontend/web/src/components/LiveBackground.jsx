import React, { useEffect, useRef, useState } from 'react';

const DEVANAGARI_GLYPHS = ['अ', 'आ', 'इ', 'क', 'ख', 'ग', 'स', 'म', 'य', 'ऋ', 'त', 'व'];

export default function LiveBackground({ calmMode }) {
  const midLayerRef = useRef(null);
  const [stars, setStars] = useState([]);

  // Generate a handful of subtle stars for night theme
  useEffect(() => {
    const starList = Array.from({ length: 18 }).map((_, i) => ({
      id: i,
      left: `${(i * 5.7 + 4) % 94}%`,
      top: `${(i * 7.1 + 8) % 45}%`,
      delay: `${(i * 0.4) % 5}s`,
      duration: `${4 + (i % 4)}s`
    }));
    setStars(starList);
  }, []);

  // Parallax pointer reaction (desktop only, paused in calmMode or hidden tab)
  useEffect(() => {
    if (calmMode) return;
    let rafId = null;
    let targetX = 0;
    let targetY = 0;
    let currentX = 0;
    let currentY = 0;

    const handlePointerMove = (e) => {
      // Calculate normalized offset from center [-1 to 1]
      const nx = (e.clientX / window.innerWidth) * 2 - 1;
      const ny = (e.clientY / window.innerHeight) * 2 - 1;
      targetX = nx * 12; // Subtle 12px shift max
      targetY = ny * 8;
    };

    const animate = () => {
      if (document.hidden) {
        rafId = requestAnimationFrame(animate);
        return;
      }
      currentX += (targetX - currentX) * 0.05;
      currentY += (targetY - currentY) * 0.05;

      if (midLayerRef.current) {
        midLayerRef.current.style.transform = `translate3d(${currentX.toFixed(2)}px, ${currentY.toFixed(2)}px, 0)`;
      }
      rafId = requestAnimationFrame(animate);
    };

    window.addEventListener('pointermove', handlePointerMove, { passive: true });
    rafId = requestAnimationFrame(animate);

    return () => {
      window.removeEventListener('pointermove', handlePointerMove);
      cancelAnimationFrame(rafId);
    };
  }, [calmMode]);

  return (
    <div className="living-background" aria-hidden="true">
      {/* Far Layer: Ruled notebook grid & margin */}
      <div className="bg-layer-far" />
      <div className="bg-notebook-margin-line" />

      {/* Mid Layer: Slowly drifting Devanagari letters */}
      <div className="bg-layer-mid" ref={midLayerRef}>
        {DEVANAGARI_GLYPHS.map((glyph, idx) => {
          const leftPercent = 8 + (idx * 8) % 82;
          const delaySec = (idx * 3.8) % 35;
          const durationSec = 34 + (idx % 6) * 4;
          return (
            <span
              key={idx}
              className="floating-glyph"
              style={{
                left: `${leftPercent}%`,
                animationDelay: `-${delaySec}s`,
                animationDuration: `${durationSec}s`
              }}
            >
              {glyph}
            </span>
          );
        })}
      </div>

      {/* Near Layer: Glows, Stars & Paper-Cut Silhouette */}
      <div className="bg-layer-near">
        <div className="sunrise-glow" />
        <div className="lamp-glow" />

        {/* Night Stars */}
        {stars.map((s) => (
          <div
            key={s.id}
            className="star-particle"
            style={{
              left: s.left,
              top: s.top,
              animationDelay: s.delay,
              animationDuration: s.duration
            }}
          />
        ))}

        {/* Paper-cut hills silhouette at bottom */}
        <svg
          className="paper-cut-silhouette"
          viewBox="0 0 1440 120"
          preserveAspectRatio="none"
          fill="currentColor"
        >
          <path d="M0,70 C240,110 480,40 720,80 C960,115 1200,55 1440,90 L1440,120 L0,120 Z" />
        </svg>
      </div>
    </div>
  );
}
