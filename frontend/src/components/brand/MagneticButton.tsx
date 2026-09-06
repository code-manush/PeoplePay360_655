import { useRef, type ButtonHTMLAttributes, type ReactNode } from 'react';

type Props = ButtonHTMLAttributes<HTMLButtonElement> & {
  children: ReactNode;
};

export default function MagneticButton({ children, onPointerMove, onPointerLeave, ...props }: Props) {
  const ref = useRef<HTMLButtonElement>(null);

  return (
    <button
      {...props}
      ref={ref}
      onPointerMove={(event) => {
        const node = ref.current;
        if (node && !window.matchMedia('(prefers-reduced-motion: reduce)').matches) {
          const box = node.getBoundingClientRect();
          const x = event.clientX - (box.left + box.width / 2);
          const y = event.clientY - (box.top + box.height / 2);
          node.style.transform = `translate(${x * 0.16}px, ${y * 0.16}px)`;
        }
        onPointerMove?.(event);
      }}
      onPointerLeave={(event) => {
        if (ref.current) ref.current.style.transform = '';
        onPointerLeave?.(event);
      }}
    >
      {children}
    </button>
  );
}
