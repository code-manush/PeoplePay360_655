import { useRef, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { ArrowRight } from 'lucide-react';
import apiClient from '../../api/client';
import CinematicScene from '../../components/cinematic/CinematicScene';
import MagneticButton from '../../components/brand/MagneticButton';
import ThemeToggle from '../../components/brand/ThemeToggle';
import { usePointerVars } from '../../hooks/usePointerVars';
import styles from '../Login.module.css';

export default function Register() {
  const navigate = useNavigate();
  const pageRef = useRef<HTMLDivElement>(null);
  usePointerVars(pageRef);
  const [formData, setFormData] = useState({
    first_name: '',
    last_name: '',
    email: '',
    password: '',
    confirm_password: '',
  });
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  const handleChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    setFormData({ ...formData, [event.target.name]: event.target.value });
  };

  const handleSubmit = async (event: React.FormEvent) => {
    event.preventDefault();
    setError('');

    if (formData.password !== formData.confirm_password) {
      setError('Passwords do not match');
      return;
    }

    setLoading(true);
    try {
      await apiClient.post('/auth/register', {
        email: formData.email,
        password: formData.password,
        first_name: formData.first_name,
        last_name: formData.last_name,
      });
      navigate('/login');
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Registration failed');
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
          <MagneticButton className={styles.ghostBtn} type="button" onClick={() => navigate('/login')}>
            Sign in
          </MagneticButton>
        </div>
      </header>

      <div className={styles.stage}>
        <div className={styles.panel}>
          <p className={styles.kicker}>Join the platform</p>
          <h1 className={styles.title}>Create your workspace.</h1>
          <p className={styles.subtitle}>Open an employee account and step into PeoplePay360.</p>

          <form onSubmit={handleSubmit} className={styles.form}>
            <div className={styles.row}>
              <label className={styles.field}>
                <span>First name</span>
                <input name="first_name" value={formData.first_name} onChange={handleChange} required />
              </label>
              <label className={styles.field}>
                <span>Last name</span>
                <input name="last_name" value={formData.last_name} onChange={handleChange} required />
              </label>
            </div>
            <label className={styles.field}>
              <span>Email address</span>
              <input name="email" type="email" value={formData.email} onChange={handleChange} required />
            </label>
            <label className={styles.field}>
              <span>Password</span>
              <input name="password" type="password" value={formData.password} onChange={handleChange} required />
            </label>
            <label className={styles.field}>
              <span>Confirm password</span>
              <input
                name="confirm_password"
                type="password"
                value={formData.confirm_password}
                onChange={handleChange}
                required
              />
            </label>
            {error && <p className={styles.error}>{error}</p>}
            <MagneticButton className={styles.submit} type="submit" disabled={loading}>
              {loading ? 'Creating account…' : 'Register'}
              {!loading && <ArrowRight size={16} />}
            </MagneticButton>
          </form>

          <p className={styles.switch}>
            Already have an account?{' '}
            <button type="button" onClick={() => navigate('/login')}>
              Sign in
            </button>
          </p>
        </div>
      </div>
    </div>
  );
}
