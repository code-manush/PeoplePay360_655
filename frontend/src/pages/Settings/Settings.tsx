import { useEffect, useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '../../components/ui/Card/Card';
import { useAuth } from '../../contexts/AuthContext';
import apiClient, { unwrapData } from '../../api/client';

export default function Settings() {
  const { user, employee, role } = useAuth();
  const [me, setMe] = useState<any>(null);

  useEffect(() => {
    apiClient.get('/auth/me').then((res) => setMe(unwrapData(res))).catch(() => setMe(null));
  }, []);

  const emp = me?.employee || employee;
  const session = me?.user || user;

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
      <div>
        <h1 style={{ fontSize: '1.875rem', fontWeight: 700 }}>Settings</h1>
        <p style={{ color: 'var(--text-secondary)' }}>Signed-in identity from JWT and peoplepay360.</p>
      </div>
      <Card>
        <CardHeader><CardTitle>Session</CardTitle></CardHeader>
        <CardContent>
          <p><strong>Role:</strong> {role}</p>
          <p><strong>Email:</strong> {session?.email}</p>
          <p><strong>Employee:</strong> {emp ? `${emp.first_name} ${emp.last_name} (${emp.employee_code})` : '—'}</p>
          <p><strong>Department:</strong> {emp?.department?.name || emp?.department_id || '—'}</p>
          <p style={{ marginTop: '1rem', color: 'var(--text-muted)' }}>
            Hierarchy: EMPLOYEE &lt; HR &lt; ADMIN. HR can manage organization, schedules, payroll config, and audit from the sidebar.
          </p>
        </CardContent>
      </Card>
    </div>
  );
}
