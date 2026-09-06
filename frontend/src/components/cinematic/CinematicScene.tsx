import { useEffect, useRef, useState } from 'react';
import styles from './CinematicScene.module.css';

type Star = { x: number; y: number; z: number; r: number };

export default function CinematicScene() {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const [isDark, setIsDark] = useState(
    () => document.documentElement.getAttribute('data-theme') === 'dark',
  );

  useEffect(() => {
    const root = document.documentElement;
    const sync = () => setIsDark(root.getAttribute('data-theme') === 'dark');
    sync();
    const observer = new MutationObserver(sync);
    observer.observe(root, { attributes: true, attributeFilter: ['data-theme'] });
    return () => observer.disconnect();
  }, []);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    const stars: Star[] = Array.from({ length: isDark ? 140 : 70 }, () => ({
      x: Math.random(),
      y: Math.random(),
      z: Math.random(),
      r: Math.random() * 1.2 + 0.15,
    }));

    const resize = () => {
      const ratio = Math.min(window.devicePixelRatio || 1, 2);
      canvas.width = window.innerWidth * ratio;
      canvas.height = window.innerHeight * ratio;
    };

    resize();
    window.addEventListener('resize', resize);

    let frame = 0;
    const draw = (time: number) => {
      const { width, height } = canvas;
      ctx.clearRect(0, 0, width, height);
      for (const star of stars) {
        const drift = ((star.y + time * 0.000016 * (0.2 + star.z)) % 1 + 1) % 1;
        const alpha = isDark ? 0.16 + star.z * 0.7 : 0.08 + star.z * 0.28;
        ctx.fillStyle =
          star.z > 0.78
            ? `rgba(35, 131, 226, ${alpha})`
            : isDark
              ? `rgba(238, 244, 251, ${alpha})`
              : `rgba(77, 160, 240, ${alpha})`;
        ctx.beginPath();
        ctx.arc(star.x * width, drift * height, star.r * (0.5 + star.z), 0, Math.PI * 2);
        ctx.fill();
      }
      frame = requestAnimationFrame(draw);
    };

    frame = requestAnimationFrame(draw);
    return () => {
      cancelAnimationFrame(frame);
      window.removeEventListener('resize', resize);
    };
  }, [isDark]);

  return (
    <div className={styles.scene} aria-hidden="true">
      <canvas ref={canvasRef} className={styles.stars} />
      <div className={styles.auroraA} />
      <div className={styles.auroraB} />
      <div className={styles.auroraC} />
      <div className={styles.rings} />
      <div className={styles.cursorLight} />
      <div className={styles.vignette} />
      <div className={styles.grain} />
    </div>
  );
}
