import React from 'react';
import { NavLink, useNavigate, useLocation } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import { 
  LayoutDashboard, 
  Users, 
  FileSignature, 
  Clock, 
  Calendar, 
  CreditCard,
  PieChart,
  Settings,
  LogOut,
  Bell
} from 'lucide-react';
import styles from './Sidebar.module.css';
import { clsx } from 'clsx';

const NAV_ITEMS = [
  { name: 'Dashboard', path: '/', icon: <LayoutDashboard size={20} />, roles: ['ADMIN', 'HR', 'EMPLOYEE'] },
  { name: 'Employees', path: '/employees', icon: <Users size={20} />, roles: ['ADMIN', 'HR'] },
  { name: 'Contracts', path: '/contracts', icon: <FileSignature size={20} />, roles: ['ADMIN', 'HR'] },
  { name: 'Attendance', path: '/attendance', icon: <Clock size={20} />, roles: ['ADMIN', 'HR', 'EMPLOYEE'] },
  { name: 'Leave', path: '/leave', icon: <Calendar size={20} />, roles: ['ADMIN', 'HR', 'EMPLOYEE'] },
  { name: 'Payroll', path: '/payroll', icon: <CreditCard size={20} />, roles: ['ADMIN', 'HR', 'EMPLOYEE'] },
  { name: 'Reports', path: '/reports', icon: <PieChart size={20} />, roles: ['ADMIN', 'HR'] },
  { name: 'Notifications', path: '/notifications', icon: <Bell size={20} />, roles: ['ADMIN', 'HR', 'EMPLOYEE'] },
  { name: 'Settings', path: '/settings', icon: <Settings size={20} />, roles: ['ADMIN', 'HR', 'EMPLOYEE'] },
];

export default function Sidebar() {
  const { role, employee, logout } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();

  const handleLogout = () => {
    logout();
    navigate('/login');
  };

  const filteredNavItems = NAV_ITEMS.filter(item => item.roles.includes(role || ''));

  return (
    <aside className={styles.sidebar}>
      <div className={styles.logoContainer}>
        <div className={styles.logoIcon}>
          <span className={styles.logoShape}></span>
        </div>
        <div className={styles.logoText}>
          <h1 className={styles.brandName}>PeoplePay360</h1>
          <span className={styles.brandSub}>HR & Payroll</span>
        </div>
      </div>

      <nav className={styles.navMenu}>
        {filteredNavItems.map((item) => {
          const isActive = location.pathname === item.path || 
                          (item.path !== '/' && location.pathname.startsWith(item.path));
          
          return (
            <NavLink
              key={item.path}
              to={item.path}
              className={clsx(styles.navItem, isActive && styles.active)}
            >
              <div className={styles.navIcon}>{item.icon}</div>
              <span className={styles.navLabel}>{item.name}</span>
              {isActive && <div className={styles.activeIndicator} />}
            </NavLink>
          );
        })}
      </nav>

      <div className={styles.sidebarFooter}>
        <div className={styles.userInfo} style={{ display: 'flex', alignItems: 'center', width: '100%', gap: '0.75rem', padding: '0.5rem' }}>
          <div className={styles.avatar}>
            {employee ? `${employee.first_name[0]}${employee.last_name[0]}` : (role === 'ADMIN' ? 'SA' : role === 'HR' ? 'HR' : 'EM')}
          </div>
          <div className={styles.userDetails} style={{ flex: 1 }}>
            <span className={styles.userName} style={{ fontSize: '0.875rem', fontWeight: 600, display: 'block' }}>
              {employee ? `${employee.first_name} ${employee.last_name}` : (role === 'ADMIN' ? 'System Admin' : role === 'HR' ? 'HR Manager' : 'Employee')}
            </span>
            <span className={styles.userRole} style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>{role}</span>
          </div>
          <button 
            onClick={handleLogout} 
            title="Log Out" 
            style={{ 
              background: 'transparent', 
              border: 'none', 
              color: 'var(--text-muted)', 
              cursor: 'pointer',
              padding: '0.25rem'
            }}
          >
            <LogOut size={20} />
          </button>
        </div>
      </div>
    </aside>
  );
}
