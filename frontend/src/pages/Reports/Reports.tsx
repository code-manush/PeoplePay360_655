import { useEffect, useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '../../components/ui/Card/Card';
import { Badge } from '../../components/ui/Badge/Badge';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Cell } from 'recharts';
import apiClient, { unwrapData, unwrapList } from '../../api/client';
import styles from '../Dashboard.module.css';

const COLORS = ['#3b82f6', '#10b981', '#f59e0b', '#ef4444', '#8b5cf6', '#ec4899', '#06b6d4'];

export default function Reports() {
  const [data, setData] = useState<any>(null);
  const [departments, setDepartments] = useState<any[]>([]);
  const [departmentId, setDepartmentId] = useState('');
  const [error, setError] = useState('');

  async function load() {
    setError('');
    try {
      const [report, depts] = await Promise.all([
        apiClient.get('/reports', { params: { department_id: departmentId || undefined } }),
        apiClient.get('/departments'),
      ]);
      setData(unwrapData(report));
      setDepartments(unwrapList(depts));
    } catch (err: any) {
      setError(err.message);
    }
  }

  useEffect(() => { load(); }, [departmentId]);

  if (error) {
    return (
      <div className={styles.container}>
        <h1 className={styles.title}>Reports</h1>
        <p className={styles.error}>{error}{error.toLowerCase().includes('role') ? ' Sign out and sign in again if this persists.' : ''}</p>
        <button className="formInput" style={{ width: 160 }} onClick={load}>Retry</button>
      </div>
    );
  }
  if (!data) return <div className={styles.loader}>Loading reports...</div>;

  const k = data.kpis || {};
  return (
    <div className={styles.container}>
      <header className={styles.header}>
        <div>
          <h1 className={styles.title}>Reports</h1>
          <p className={styles.subtitle}>Live payroll, attendance, and leave metrics from peoplepay360.</p>
        </div>
        <select className="formInput" style={{ width: 240 }} value={departmentId} onChange={(e) => setDepartmentId(e.target.value)}>
          <option value="">All departments</option>
          {departments.map((d) => <option key={d.id} value={d.id}>{d.name}</option>)}
        </select>
      </header>
      <div className={styles.kpiGrid}>
        {[
          ['Employees', k.employees],
          ['Attendance health', `${k.attendance_health || 0}%`],
          ['Pending leave', k.pending_leave_requests],
          ['Total net paid', new Intl.NumberFormat('en-IN', { style: 'currency', currency: 'INR', maximumFractionDigits: 0 }).format(k.total_net_paid || 0)],
        ].map(([label, value]) => (
          <Card key={String(label)} className={styles.kpiCard}>
            <CardContent className={styles.kpiContent}>
              <div className={styles.kpiInfo}>
                <p className={styles.kpiLabel}>{label}</p>
                <h3 className={styles.kpiValue}>{value ?? '—'}</h3>
              </div>
            </CardContent>
          </Card>
        ))}
      </div>
      <div className={styles.grid2Col}>
        <Card>
          <CardHeader><CardTitle>Salary by department</CardTitle></CardHeader>
          <CardContent>
            {data.salaryByDepartment && data.salaryByDepartment.length > 0 ? (
              <div style={{ height: 300, width: '100%', marginBottom: '1.5rem', marginTop: '1rem' }}>
                <ResponsiveContainer>
                  <BarChart data={data.salaryByDepartment} margin={{ top: 10, right: 10, left: 10, bottom: 0 }}>
                    <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="var(--border-color)" />
                    <XAxis 
                      dataKey="department_name" 
                      axisLine={false} 
                      tickLine={false} 
                      tick={{ fill: 'var(--text-secondary)', fontSize: 12 }} 
                      dy={10} 
                    />
                    <YAxis 
                      axisLine={false} 
                      tickLine={false} 
                      tick={{ fill: 'var(--text-secondary)', fontSize: 12 }}
                      tickFormatter={(value) => `₹${value / 1000}k`}
                    />
                    <Tooltip 
                      cursor={{ fill: 'var(--bg-secondary)', opacity: 0.4 }}
                      contentStyle={{ borderRadius: '8px', border: '1px solid var(--border-color)', backgroundColor: 'var(--bg-primary)' }}
                      formatter={(value: any) => new Intl.NumberFormat('en-IN', { style: 'currency', currency: 'INR', maximumFractionDigits: 0 }).format(value || 0)}
                      labelStyle={{ color: 'var(--text-primary)', fontWeight: 'bold', marginBottom: '0.5rem' }}
                    />
                    <Bar dataKey="total_salary" radius={[4, 4, 0, 0]}>
                      {data.salaryByDepartment.map((_: any, index: number) => (
                        <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                      ))}
                    </Bar>
                  </BarChart>
                </ResponsiveContainer>
              </div>
            ) : null}
            <div className={styles.list}>
              {(data.salaryByDepartment || []).map((row: any) => (
                <div key={row.department_id} className={styles.listItem}>
                  <div className={styles.listText}>
                    <p className={styles.listTitle}>{row.department_name}</p>
                    <p className={styles.listDesc}>{row.headcount} employees</p>
                  </div>
                  <div className={styles.listRight}>
                    {new Intl.NumberFormat('en-IN', { style: 'currency', currency: 'INR', maximumFractionDigits: 0 }).format(row.total_salary || 0)}
                  </div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardHeader><CardTitle>Recent payruns</CardTitle></CardHeader>
          <CardContent>
            <div className={styles.list}>
              {(data.recentPayruns || []).map((pr: any) => (
                <div key={pr.id} className={styles.listItem}>
                  <div className={styles.listText}>
                    <p className={styles.listTitle}>{pr.run_number || pr.name}</p>
                    <p className={styles.listDesc}>{pr.period_start} – {pr.period_end}</p>
                  </div>
                  <Badge variant={pr.status === 'PAID' ? 'success' : 'warning'}>{pr.status}</Badge>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
