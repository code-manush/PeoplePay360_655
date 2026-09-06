import { useEffect, useState } from 'react';

export type Theme = 'light' | 'dark';

export function readTheme(): Theme {
  const stored = localStorage.getItem('theme');
  return stored === 'dark' ? 'dark' : 'light';
}

export function applyTheme(theme: Theme) {
  document.documentElement.setAttribute('data-theme', theme);
  localStorage.setItem('theme', theme);
}

export function useTheme() {
  const [theme, setTheme] = useState<Theme>(() =>
    typeof document === 'undefined' ? 'light' : readTheme(),
  );

  useEffect(() => {
    applyTheme(theme);
  }, [theme]);

  const toggleTheme = () => setTheme((prev) => (prev === 'light' ? 'dark' : 'light'));

  return { theme, toggleTheme };
}
