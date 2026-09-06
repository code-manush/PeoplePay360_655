import { useEffect, type RefObject } from 'react';

export function usePointerVars(ref: RefObject<HTMLElement | null>) {
  useEffect(() => {
    const node = ref.current;
    if (!node) return;

    const onMove = (event: PointerEvent) => {
      node.style.setProperty('--mx', `${event.clientX}px`);
      node.style.setProperty('--my', `${event.clientY}px`);
      node.style.setProperty('--px', (event.clientX / window.innerWidth).toFixed(4));
      node.style.setProperty('--py', (event.clientY / window.innerHeight).toFixed(4));
    };

    window.addEventListener('pointermove', onMove, { passive: true });
    return () => window.removeEventListener('pointermove', onMove);
  }, [ref]);
}
