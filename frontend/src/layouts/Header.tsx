import React, { useEffect, useState } from 'react';
import { Bell, Search, Menu, Moon, Sun } from 'lucide-react';
import { useNavigate, useLocation } from 'react-router-dom';
import styles from './Header.module.css';
import apiClient, { unwrapList } from '../api/client';

export default function Header() {
  const navigate = useNavigate();
  const location = useLocation();
  const [count, setCount] = useState(0);
  
  const [theme, setTheme] = useState<'light' | 'dark'>(() => {
    return (localStorage.getItem('theme') as 'light' | 'dark') || 'light';
  });

  useEffect(() => {
    document.documentElement.setAttribute('data-theme', theme);
    localStorage.setItem('theme', theme);
  }, [theme]);

  const toggleTheme = () => {
    setTheme(prev => prev === 'light' ? 'dark' : 'light');
  };

  useEffect(() => {
    if (location.pathname === '/notifications') {
      const now = new Date().toISOString();
      localStorage.setItem('lastReadNotifTimestamp', now);
      setCount(0); // Clear on view
    } else {
      apiClient.get('/notifications/inbox')
        .then((res) => {
          const notifs = unwrapList(res);
          const lastRead = localStorage.getItem('lastReadNotifTimestamp');
          if (!lastRead) {
            setCount(notifs.length);
          } else {
            const lastReadDate = new Date(lastRead);
            const unread = notifs.filter((n: any) => new Date(n.published_at) > lastReadDate);
            setCount(unread.length);
          }
        })
        .catch(() => setCount(0));
    }
  }, [location.pathname]);

  return (
    <header className={styles.header}>
      <div className={styles.leftSection}>
        <button className={styles.menuButton}>
          <Menu size={24} />
        </button>
        <div className={styles.searchBar}>
          <Search size={18} className={styles.searchIcon} />
          <input
            type="text"
            placeholder="Search employees, payroll, reports..."
            className={styles.searchInput}
          />
        </div>
      </div>
      <div className={styles.rightSection}>
        <button className={styles.iconButton} onClick={toggleTheme} title="Toggle Theme">
          {theme === 'light' ? <Moon size={20} /> : <Sun size={20} />}
        </button>
        <button className={styles.iconButton} onClick={() => navigate('/notifications')} title="Notifications">
          {count > 0 && <div className={styles.notificationBadge}>+{count}</div>}
          <Bell size={20} />
        </button>
      </div>
    </header>
  );
}
