import { useEffect, useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '../../components/ui/Card/Card';
import { useAuth } from '../../contexts/AuthContext';
import apiClient, { unwrapData } from '../../api/client';
import { User, Mail, Briefcase, Building, ShieldCheck } from 'lucide-react';
import styles from '../Dashboard.module.css';

export default function Settings() {
  const { user, employee, role } = useAuth();
  const [me, setMe] = useState<any>(null);

  useEffect(() => {
    apiClient.get('/auth/me').then((res) => setMe(unwrapData(res))).catch(() => setMe(null));
  }, []);

  const emp = me?.employee || employee;
  const session = me?.user || user;
  
  const getInitials = (firstName?: string, lastName?: string) => {
    if (!firstName || !lastName) return 'U';
    return `${firstName[0]}${lastName[0]}`.toUpperCase();
  };

  return (
    <div className={styles.container}>
      <header className={styles.header}>
        <div>
          <h1 className={styles.title}>Account Settings</h1>
          <p className={styles.subtitle}>Manage your profile and account preferences.</p>
        </div>
      </header>
      
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(300px, 1fr))', gap: '2rem', marginTop: '1rem' }}>
        <Card style={{ height: 'fit-content' }}>
          <CardContent style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', paddingTop: '2.5rem', paddingBottom: '2.5rem' }}>
            <div style={{ 
              width: '100px', height: '100px', borderRadius: '50%', 
              backgroundColor: 'var(--primary)', color: 'white', 
              display: 'flex', alignItems: 'center', justifyContent: 'center',
              fontSize: '2.5rem', fontWeight: 'bold', marginBottom: '1.5rem'
            }}>
              {emp ? getInitials(emp.first_name, emp.last_name) : <User size={48} />}
            </div>
            <h2 style={{ fontSize: '1.25rem', fontWeight: 600, margin: '0 0 0.25rem 0' }}>
              {emp ? `${emp.first_name} ${emp.last_name}` : 'User'}
            </h2>
            <p style={{ color: 'var(--text-secondary)', marginBottom: '1.5rem', fontSize: '0.9375rem' }}>{session?.email}</p>
            <div style={{ 
              backgroundColor: 'var(--bg-secondary)', padding: '0.5rem 1rem', 
              borderRadius: '9999px', fontSize: '0.875rem', fontWeight: 500,
              display: 'flex', alignItems: 'center', gap: '0.5rem'
            }}>
              <ShieldCheck size={16} style={{ color: 'var(--primary)' }} />
              {role}
            </div>
          </CardContent>
        </Card>
        
        <div style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
          <Card>
            <CardHeader><CardTitle>Profile Information</CardTitle></CardHeader>
            <CardContent style={{ display: 'flex', flexDirection: 'column', gap: '1.25rem' }}>
              <div style={{ display: 'flex', alignItems: 'flex-start', gap: '1rem' }}>
                <div style={{ marginTop: '0.25rem', color: 'var(--text-muted)' }}><Mail size={20} /></div>
                <div>
                  <p style={{ fontSize: '0.875rem', color: 'var(--text-secondary)', margin: '0 0 0.25rem 0' }}>Email Address</p>
                  <p style={{ margin: 0, fontWeight: 500 }}>{session?.email}</p>
                </div>
              </div>
              
              <div style={{ display: 'flex', alignItems: 'flex-start', gap: '1rem' }}>
                <div style={{ marginTop: '0.25rem', color: 'var(--text-muted)' }}><Briefcase size={20} /></div>
                <div>
                  <p style={{ fontSize: '0.875rem', color: 'var(--text-secondary)', margin: '0 0 0.25rem 0' }}>Employee ID</p>
                  <p style={{ margin: 0, fontWeight: 500 }}>{emp ? emp.employee_code : 'Not Assigned'}</p>
                </div>
              </div>
              
              <div style={{ display: 'flex', alignItems: 'flex-start', gap: '1rem' }}>
                <div style={{ marginTop: '0.25rem', color: 'var(--text-muted)' }}><Building size={20} /></div>
                <div>
                  <p style={{ fontSize: '0.875rem', color: 'var(--text-secondary)', margin: '0 0 0.25rem 0' }}>Department</p>
                  <p style={{ margin: 0, fontWeight: 500 }}>{emp?.department?.name || emp?.department_id || 'Not Assigned'}</p>
                </div>
              </div>
            </CardContent>
          </Card>
          
          <Card>
            <CardHeader><CardTitle>Security & Permissions</CardTitle></CardHeader>
            <CardContent>
              <p style={{ fontSize: '0.9375rem', color: 'var(--text-secondary)', lineHeight: 1.5, margin: 0 }}>
                You are currently signed in with <strong>{role}</strong> privileges. 
                <br /><br />
                System hierarchy is structured as: <code style={{ backgroundColor: 'var(--bg-secondary)', padding: '2px 6px', borderRadius: '4px' }}>EMPLOYEE &lt; HR &lt; ADMIN</code>
                <br /><br />
                Users with HR or ADMIN roles can manage organizations, schedules, payroll configurations, and perform audits from the administrative sidebar.
              </p>
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
}
