import React, { useEffect, useState } from 'react';
import { Bell, Search, Menu } from 'lucide-react';
import { useNavigate } from 'react-router-dom';
import styles from './Header.module.css';
import apiClient, { unwrapList } from '../api/client';

export default function Header() {
  const navigate = useNavigate();
  const [count, setCount] = useState(0);

  useEffect(() => {
    apiClient.get('/notifications/inbox')
      .then((res) => setCount(unwrapList(res).length))
      .catch(() => setCount(0));
  }, []);

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
        <button className={styles.iconButton} onClick={() => navigate('/notifications')} title="Notifications">
          {count > 0 && <div className={styles.notificationBadge}>{count > 9 ? '9+' : count}</div>}
          <Bell size={20} />
        </button>
      </div>
    </header>
  );
}
