import { Moon, Sun } from 'lucide-react';
import { useTheme } from '../../hooks/useTheme';
import styles from './ThemeToggle.module.css';

export default function ThemeToggle() {
  const { theme, toggleTheme } = useTheme();

  return (
    <button
      type="button"
      className={styles.toggle}
      onClick={toggleTheme}
      title={theme === 'light' ? 'Switch to dark theme' : 'Switch to light theme'}
      aria-label="Toggle color theme"
    >
      {theme === 'light' ? <Moon size={18} /> : <Sun size={18} />}
    </button>
  );
}
