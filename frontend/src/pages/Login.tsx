import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import styles from './Login.module.css';
import { Shield, Users, User, ArrowRight } from 'lucide-react';
import { Button } from '../components/ui/Button/Button';

const DEMOS = [
  { role: 'ADMIN', email: 'anmolkj006@gmail.com', label: 'Admin', icon: <Shield size={20} />, hint: 'Anmol@Pay360' },
  { role: 'HR', email: 'gauriborse1808@gmail.com', label: 'HR', icon: <Users size={20} />, hint: 'Gauri@Pay360' },
  { role: 'EMPLOYEE', email: 'manushpatel1002@gmail.com', label: 'Employee', icon: <User size={20} />, hint: 'Manush@Pay360' },
];

export default function Login() {
  const { login } = useAuth();
  const navigate = useNavigate();
  const [email, setEmail] = useState('anmolkj006@gmail.com');
  const [password, setPassword] = useState('Anmol@Pay360');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError('');
    try {
      await login(email, password);
      navigate('/');
    } catch (err: any) {
      setError(err.message || 'Sign in failed');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className={styles.container}>
      <div className={styles.leftPanel}>
        <div className={styles.logo}>
          <div className={styles.logoIcon}><span className={styles.logoShape}></span></div>
          <h1>PeoplePay360</h1>
        </div>
        <div className={styles.heroContent}>
          <h2>The complete HR & Payroll platform.</h2>
          <p>Sign in with JWT against the peoplepay360 database. Roles: Employee &lt; HR &lt; Admin.</p>
        </div>
      </div>
      <div className={styles.rightPanel}>
        <div className={styles.loginBox}>
          <h3 className={styles.loginTitle}>Welcome back</h3>
          <p className={styles.loginSubtitle}>Use a demo account or your own credentials</p>
          <form onSubmit={handleSubmit} style={{ display: 'flex', flexDirection: 'column', gap: '0.9rem', marginBottom: '1.5rem' }}>
            <div>
              <label className="formLabel">Email</label>
              <input className="formInput" value={email} onChange={(e) => setEmail(e.target.value)} type="email" required />
            </div>
            <div>
              <label className="formLabel">Password</label>
              <input className="formInput" value={password} onChange={(e) => setPassword(e.target.value)} type="password" required />
            </div>
            {error && <p className="formError">{error}</p>}
            <Button type="submit" isLoading={loading} fullWidth rightIcon={<ArrowRight size={16} />}>Sign in</Button>
          </form>
          <div className={styles.roleGrid}>
            {DEMOS.map((d) => (
              <button key={d.email} className={styles.roleCard} type="button" onClick={() => { setEmail(d.email); setPassword(d.hint.includes('@') ? d.hint : 'demo123'); }}>
                <div className={`${styles.iconWrapper} ${d.role === 'ADMIN' ? styles.iconAdmin : d.role === 'HR' ? styles.iconHR : styles.iconEmployee}`}>
                  {d.icon}
                </div>
                <div className={styles.roleInfo}>
                  <h4>{d.label}</h4>
                  <p>{d.email}</p>
                </div>
              </button>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}
