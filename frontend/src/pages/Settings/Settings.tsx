import React from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '../../components/ui/Card/Card';
import { useAuth } from '../../contexts/AuthContext';

export default function Settings() {
  const { user, employee, role } = useAuth();
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
          <p><strong>Email:</strong> {user?.email}</p>
          <p><strong>Employee:</strong> {employee ? `${employee.first_name} ${employee.last_name} (${employee.employee_code})` : '—'}</p>
          <p style={{ marginTop: '1rem', color: 'var(--text-muted)' }}>Hierarchy: EMPLOYEE &lt; HR &lt; ADMIN. Demo password for all seeded users is demo123.</p>
        </CardContent>
      </Card>
    </div>
  );
}
