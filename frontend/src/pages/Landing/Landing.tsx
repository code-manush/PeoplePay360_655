import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import styles from './Landing.module.css';
import { ArrowRight, ShieldCheck, Zap, Database } from 'lucide-react';
import { Button } from '../../components/ui/Button/Button';

export default function Landing() {
  const navigate = useNavigate();
  const [cursorPos, setCursorPos] = useState({ x: -100, y: -100 });

  useEffect(() => {
    const handleMouseMove = (e: MouseEvent) => {
      setCursorPos({ x: e.clientX, y: e.clientY });
    };
    window.addEventListener('mousemove', handleMouseMove);
    return () => window.removeEventListener('mousemove', handleMouseMove);
  }, []);

  return (
    <div className={styles.landingContainer}>
      <div 
        className={styles.cursorGlow} 
        style={{ left: `${cursorPos.x}px`, top: `${cursorPos.y}px` }} 
      />
      <div className={styles.topNav}>
        <div className={styles.logo}>
          <div className={styles.logoIcon}></div>
          <span className={styles.logoText}>PeoplePay360</span>
        </div>
        <div className={styles.navActions}>
          <Button variant="outline" onClick={() => navigate('/login')}>Sign In</Button>
          <Button onClick={() => navigate('/register')}>Get Started</Button>
        </div>
      </div>

      <main className={styles.mainContent}>
        <div className={styles.heroSection}>
          <div className={styles.badge}>v3.0 — The AI-Powered OS for HR</div>
          <h1 className={styles.headline}>Manage your workforce<br/>with intelligent automation.</h1>
          <p className={styles.description}>
            PeoplePay360 brings payroll, attendance, leave management, and AI-driven performance analytics into a single, unified glassmorphic interface.
          </p>
          <div className={styles.ctaGroup}>
            <Button onClick={() => navigate('/register')} rightIcon={<ArrowRight size={18}/>} style={{ padding: '0.75rem 1.5rem', fontSize: '1rem' }}>
              Create Account
            </Button>
            <Button variant="outline" onClick={() => navigate('/login')} style={{ padding: '0.75rem 1.5rem', fontSize: '1rem' }}>
              Sign In to Demo
            </Button>
          </div>
        </div>

        <div className={styles.featureGrid}>
          <div className={styles.featureCard}>
            <div className={styles.iconBox}><Zap size={24} color="var(--brand-primary)" /></div>
            <h3>AI Analytics</h3>
            <p>Utilize the local Qwen3 model to dynamically analyze employee performance and metrics.</p>
          </div>
          <div className={styles.featureCard}>
            <div className={styles.iconBox}><Database size={24} color="var(--brand-primary)" /></div>
            <h3>Unified Payroll</h3>
            <p>Automated salary generation, payslips, and compliance tracking all in one database.</p>
          </div>
          <div className={styles.featureCard}>
            <div className={styles.iconBox}><ShieldCheck size={24} color="var(--brand-primary)" /></div>
            <h3>Role-Based Security</h3>
            <p>Strict access controls separating Employees, HR, and Admin privileges securely.</p>
          </div>
        </div>
      </main>
    </div>
  );
}
