import { useRef, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { ArrowRight, Shield, User, Users } from 'lucide-react';
import { useAuth } from '../contexts/AuthContext';
import CinematicScene from '../components/cinematic/CinematicScene';
import MagneticButton from '../components/brand/MagneticButton';
import ThemeToggle from '../components/brand/ThemeToggle';
import { usePointerVars } from '../hooks/usePointerVars';
import styles from './Login.module.css';

const DEMOS = [
  { role: 'ADMIN', email: 'anmolkj006@gmail.com', label: 'Admin', icon: <Shield size={18} />, hint: 'Anmol@Pay360' },
  { role: 'HR', email: 'gauriborse1808@gmail.com', label: 'HR', icon: <Users size={18} />, hint: 'Gauri@Pay360' },
  { role: 'EMPLOYEE', email: 'manushpatel1002@gmail.com', label: 'Employee', icon: <User size={18} />, hint: 'Manush@Pay360' },
];

export default function Login() {
  const { login } = useAuth();
  const navigate = useNavigate();
  const pageRef = useRef<HTMLDivElement>(null);
  usePointerVars(pageRef);
  const [email, setEmail] = useState('anmolkj006@gmail.com');
  const [password, setPassword] = useState('Anmol@Pay360');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (event: React.FormEvent) => {
    event.preventDefault();
    setLoading(true);
    setError('');
    try {
      await login(email, password);
      navigate('/');
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Sign in failed');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className={styles.page} ref={pageRef}>
      <CinematicScene />

      <header className={styles.nav}>
        <button className={styles.brand} type="button" onClick={() => navigate('/landing')}>
          <img src="/brand/logo.png" alt="PeoplePay360" className={styles.logo} />
          <span>PeoplePay360</span>
        </button>
        <div className={styles.navActions}>
          <ThemeToggle />
          <MagneticButton className={styles.ghostBtn} type="button" onClick={() => navigate('/register')}>
            Create account
          </MagneticButton>
        </div>
      </header>

      <div className={styles.stage}>
        <div className={styles.panel}>
          <p className={styles.kicker}>Welcome back</p>
          <h1 className={styles.title}>Sign in to your workspace.</h1>
          <p className={styles.subtitle}>Use a demo account or your own credentials.</p>

          <form onSubmit={handleSubmit} className={styles.form}>
            <label className={styles.field}>
              <span>Email</span>
              <input
                value={email}
                onChange={(event) => setEmail(event.target.value)}
                type="email"
                required
              />
            </label>
            <label className={styles.field}>
              <span>Password</span>
              <input
                value={password}
                onChange={(event) => setPassword(event.target.value)}
                type="password"
                required
              />
            </label>
            {error && <p className={styles.error}>{error}</p>}
            <MagneticButton className={styles.submit} type="submit" disabled={loading}>
              {loading ? 'Signing in…' : 'Sign in'}
              {!loading && <ArrowRight size={16} />}
            </MagneticButton>
          </form>

          <div className={styles.roleHeader}>Or enter as a demo user</div>
          <div className={styles.roleGrid}>
            {DEMOS.map((demo) => (
              <button
                key={demo.email}
                className={styles.roleCard}
                type="button"
                onClick={() => {
                  setEmail(demo.email);
                  setPassword(demo.hint);
                }}
              >
                <span className={styles.roleIcon}>{demo.icon}</span>
                <span className={styles.roleInfo}>
                  <strong>{demo.label}</strong>
                  <small>{demo.email}</small>
                </span>
              </button>
            ))}
          </div>

          <p className={styles.switch}>
            New to PeoplePay360?{' '}
            <button type="button" onClick={() => navigate('/register')}>
              Create an account
            </button>
          </p>
        </div>
      </div>
    </div>
  );
}
