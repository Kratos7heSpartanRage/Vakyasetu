import React, { useEffect, useRef, useState } from 'react';

const DEVANAGARI_GLYPHS = [
  'अ', 'आ', 'इ', 'ई', 'उ', 'ऊ', 'ऋ', 'ए', 'ऐ', 'ओ', 'क', 'ख', 
  'ग', 'घ', 'च', 'ज', 'त', 'द', 'न', 'प', 'म', 'य', 'श', 'स', 'ह', 'ॐ'
];

export default function LiveBackground({ calmMode }) {
  const farLayerRef = useRef(null);
  const midLayerRef = useRef(null);
  const nearLayerRef = useRef(null);
  const [stars, setStars] = useState([]);
  const [motes, setMotes] = useState([]);

  // Generate stars and ink motes
  useEffect(() => {
    const starList = Array.from({ length: 28 }).map((_, i) => ({
      id: i,
      left: `${(i * 3.7 + 2) % 96}%`,
      top: `${(i * 5.3 + 4) % 65}%`,
      delay: `${(i * 0.35) % 5}s`,
      duration: `${3.5 + (i % 4)}s`
    }));
    setStars(starList);

    const moteList = Array.from({ length: 14 }).map((_, i) => ({
      id: i,
      left: `${(i * 7.1 + 5) % 92}%`,
      top: `${(i * 9.3 + 12) % 85}%`,
      delay: `${(i * 0.8) % 12}s`,
      duration: `${14 + (i % 6) * 2}s`
    }));
    setMotes(moteList);
  }, []);

  // Parallax Pointer + Scroll Physics
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
      targetX = nx * 32; // Responsive 32px mouse shift
      targetY = ny * 20;
    };

    const handleScroll = () => {
      scrollY = window.scrollY;
    };

    const animate = () => {
      if (!document.hidden) {
        currentX += (targetX - currentX) * 0.06;
        currentY += (targetY - currentY) * 0.06;

        // Far layer moves gently with scroll
        if (farLayerRef.current) {
          farLayerRef.current.style.transform = `translate3d(0, ${(scrollY * 0.08).toFixed(1)}px, 0)`;
        }

        // Mid glyph layer moves with mouse tilt and counter-scrolls
        if (midLayerRef.current) {
          midLayerRef.current.style.transform = `translate3d(${currentX.toFixed(1)}px, ${(currentY - scrollY * 0.12).toFixed(1)}px, 0)`;
        }

        // Near layer shifts subtly
        if (nearLayerRef.current) {
          nearLayerRef.current.style.transform = `translate3d(0, ${(-scrollY * 0.04).toFixed(1)}px, 0)`;
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
    <div className="living-background" aria-hidden="true">
      {/* Far Layer: Ruled notebook grid with scroll-linked movement */}
      <div className="bg-layer-far" ref={farLayerRef} />
      <div className="bg-notebook-margin-line" />

      {/* Mid Layer: Dynamic Drifting Devanagari Letters */}
      <div className="bg-layer-mid" ref={midLayerRef}>
        {DEVANAGARI_GLYPHS.map((glyph, idx) => {
          const leftPercent = 4 + (idx * 3.8) % 92;
          const delaySec = (idx * 1.9) % 24;
          const durationSec = 18 + (idx % 5) * 3;
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

        {/* Ambient floating ink motes */}
        {motes.map((m) => (
          <div
            key={m.id}
            className="ambient-ink-mote"
            style={{
              left: m.left,
              top: m.top,
              animationDelay: `-${m.delay}`,
              animationDuration: m.duration
            }}
          />
        ))}
      </div>

      {/* Near Layer: Atmospheric Glows & Paper-Cut Hills */}
      <div className="bg-layer-near" ref={nearLayerRef}>
        <div className="sunrise-glow" />
        <div className="lamp-glow" />

        {/* Night Twinkling Stars */}
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
          viewBox="0 0 1440 140"
          preserveAspectRatio="none"
          fill="currentColor"
        >
          <path d="M0,75 C260,120 520,35 780,85 C1040,130 1260,60 1440,95 L1440,140 L0,140 Z" />
        </svg>
      </div>
    </div>
  );
}
