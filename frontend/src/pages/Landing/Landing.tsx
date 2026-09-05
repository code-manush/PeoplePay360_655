import React from 'react';
import { useNavigate } from 'react-router-dom';
import styles from './Landing.module.css';

const Landing: React.FC = () => {
  const navigate = useNavigate();

  return (
    <div className={styles.landingContainer}>
      <header className={styles.header}>
        <div className={styles.logo}>PeoplePay360</div>
        <nav className={styles.nav}>
          <button className={styles.signInBtn} onClick={() => navigate('/login')}>Sign In</button>
          <button className={styles.registerBtn} onClick={() => navigate('/register')}>Register</button>
        </nav>
      </header>
      
      <main className={styles.mainContent}>
        <div className={styles.heroSection}>
          <h1 className={styles.title}>Integrated HR & Payroll Operations Platform</h1>
          <p className={styles.subtitle}>
            A centralized solution to manage employee lifecycles, attendance, time off, contracts, and payroll all in one place.
          </p>
          <div className={styles.actionButtons}>
            <button className={styles.primaryBtn} onClick={() => navigate('/register')}>
              Get Started for Free
            </button>
            <button className={styles.secondaryBtn} onClick={() => navigate('/login')}>
              Sign In to Your Account
            </button>
          </div>
        </div>

        <div className={styles.featuresSection}>
          <div className={styles.featureCard}>
            <h3>Unified HR Flow</h3>
            <p>Centralized employee records with seamless navigation to Contracts, Attendance, and Time Off.</p>
          </div>
          <div className={styles.featureCard}>
            <h3>Operational Tracking</h3>
            <p>Implement flexible Working Schedules, attendance tracking, and comprehensive Time Off.</p>
          </div>
          <div className={styles.featureCard}>
            <h3>Payroll Processing</h3>
            <p>Enable a two-step pay run workflow with automated salary computation and payslip generation.</p>
          </div>
        </div>
      </main>

      <footer className={styles.footer}>
        <p>&copy; {new Date().getFullYear()} PeoplePay360. All rights reserved.</p>
      </footer>
    </div>
  );
};

export default Landing;
