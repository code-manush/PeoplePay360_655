import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import apiClient from '../../api/client';
import loginStyles from '../Login.module.css';
import { Button } from '../../components/ui/Button/Button';
import { ArrowRight } from 'lucide-react';

export default function Register() {
  const navigate = useNavigate();
  const [cursorPos, setCursorPos] = useState({ x: -100, y: -100 });
  const [formData, setFormData] = useState({
    first_name: '',
    last_name: '',
    email: '',
    password: '',
    confirm_password: '',
  });
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    const handleMouseMove = (e: MouseEvent) => {
      setCursorPos({ x: e.clientX, y: e.clientY });
    };
    window.addEventListener('mousemove', handleMouseMove);
    return () => window.removeEventListener('mousemove', handleMouseMove);
  }, []);

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setFormData({ ...formData, [e.target.name]: e.target.value });
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
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
    } catch (err: any) {
      setError(err.message || 'Registration failed');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className={loginStyles.container}>
      <div 
        className={loginStyles.cursorGlow} 
        style={{ left: `${cursorPos.x}px`, top: `${cursorPos.y}px` }} 
      />
      <div className={loginStyles.leftPanel}>
        <div className={loginStyles.glassCard}>
          <div className={loginStyles.logo}>
            <div className={loginStyles.logoIcon}><span className={loginStyles.logoShape}></span></div>
            <h1>PeoplePay360</h1>
          </div>
          <div className={loginStyles.heroContent}>
            <h2>Join the platform.</h2>
            <p>Create an employee account to access your personalized HR dashboard.</p>
          </div>
        </div>
      </div>
      <div className={loginStyles.rightPanel}>
        <div className={loginStyles.loginBox}>
          <h3 className={loginStyles.loginTitle}>Create Account</h3>
          <p className={loginStyles.loginSubtitle}>Sign up for a new employee account</p>
          <form onSubmit={handleSubmit} style={{ display: 'flex', flexDirection: 'column', gap: '1rem', marginBottom: '1rem' }}>
            <div style={{ display: 'flex', gap: '1rem' }}>
              <div style={{ flex: 1 }}>
                <label className="formLabel">First Name</label>
                <input className="formInput" name="first_name" value={formData.first_name} onChange={handleChange} required />
              </div>
              <div style={{ flex: 1 }}>
                <label className="formLabel">Last Name</label>
                <input className="formInput" name="last_name" value={formData.last_name} onChange={handleChange} required />
              </div>
            </div>
            <div>
              <label className="formLabel">Email Address</label>
              <input className="formInput" name="email" type="email" value={formData.email} onChange={handleChange} required />
            </div>
            <div>
              <label className="formLabel">Password</label>
              <input className="formInput" name="password" type="password" value={formData.password} onChange={handleChange} required />
            </div>
            <div>
              <label className="formLabel">Confirm Password</label>
              <input className="formInput" name="confirm_password" type="password" value={formData.confirm_password} onChange={handleChange} required />
            </div>
            
            {error && <p className="formError">{error}</p>}
            
            <Button type="submit" isLoading={loading} fullWidth rightIcon={<ArrowRight size={16} />} style={{ marginTop: '0.5rem', padding: '0.6rem' }}>
              Register
            </Button>
          </form>
          <div style={{ textAlign: 'center', marginTop: '1rem' }}>
             <span style={{ color: 'var(--text-secondary)', fontSize: '0.875rem' }}>Already have an account? </span>
             <span onClick={() => navigate('/login')} style={{ color: 'var(--brand-primary)', cursor: 'pointer', fontWeight: 500, fontSize: '0.875rem' }}>Sign in</span>
          </div>
        </div>
      </div>
    </div>
  );
}
