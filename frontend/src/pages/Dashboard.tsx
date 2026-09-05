import React, { useEffect, useState } from 'react';
import apiClient, { unwrapData } from '../api/client';
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/Card/Card';
import { Badge } from '../components/ui/Badge/Badge';
import { useAuth } from '../contexts/AuthContext';
import { 
  Users, Calendar, AlertCircle, Banknote, TrendingUp, Clock
} from 'lucide-react';
import styles from './Dashboard.module.css';

export default function Dashboard() {
  const { role } = useAuth();
  const [data, setData] = useState<any>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function loadDashboard() {
      try {
        const response = await apiClient.get('/dashboard');
        setData(unwrapData(response));
      } catch (error) {
        console.error('Failed to load dashboard', error);
      } finally {
        setLoading(false);
      }
    }
    loadDashboard();
  }, []);

  if (loading) {
    return <div className={styles.loader}>Loading Dashboard...</div>;
  }

  if (!data) {
    return <div className={styles.error}>Failed to load data.</div>;
  }

  const { kpis = {}, recentPayruns = [], pendingLeaveRequests = [], activeNotifications = [] } = data;

  return (
    <div className={styles.container}>
      <header className={styles.header}>
        <div>
          <h1 className={styles.title}>
            {role === 'ADMIN' ? 'Admin Dashboard' : role === 'HR' ? 'HR Dashboard' : 'My Dashboard'}
          </h1>
          <p className={styles.subtitle}>
            {role === 'EMPLOYEE' ? 'Welcome back! Here is your personal overview.' : 'Overview of company metrics and recent activity.'}
          </p>
        </div>
        <div className={styles.dateBadge}>
          {new Date().toLocaleDateString('en-US', { weekday: 'long', month: 'long', day: 'numeric', year: 'numeric' })}
        </div>
      </header>

      {/* KPIs */}
      <div className={styles.kpiGrid}>
        <Card className={styles.kpiCard}>
          <CardContent className={styles.kpiContent}>
            <div className={styles.kpiIconWrapper}>
              <Users size={24} className={styles.iconBlue} />
            </div>
            <div className={styles.kpiInfo}>
              <p className={styles.kpiLabel}>Total Employees</p>
              <h3 className={styles.kpiValue}>{kpis.active_employees}</h3>
              <p className={styles.kpiMeta}>
                <span className={styles.trendUp}>+{kpis.new_this_month} new</span> this month
              </p>
            </div>
          </CardContent>
        </Card>

        <Card className={styles.kpiCard}>
          <CardContent className={styles.kpiContent}>
            <div className={styles.kpiIconWrapper}>
              <Clock size={24} className={styles.iconGreen} />
            </div>
            <div className={styles.kpiInfo}>
              <p className={styles.kpiLabel}>Attendance (30d)</p>
              <h3 className={styles.kpiValue}>{kpis.attendance_rate_30d}%</h3>
              <p className={styles.kpiMeta}>
                {kpis.present_today} checked in today
              </p>
            </div>
          </CardContent>
        </Card>

        <Card className={styles.kpiCard}>
          <CardContent className={styles.kpiContent}>
            <div className={styles.kpiIconWrapper}>
              <Banknote size={24} className={styles.iconPurple} />
            </div>
            <div className={styles.kpiInfo}>
              <p className={styles.kpiLabel}>Last Payroll Disbursed</p>
              <h3 className={styles.kpiValue}>
                {new Intl.NumberFormat('en-IN', { style: 'currency', currency: 'INR' }).format(kpis.last_payrun_total)}
              </h3>
              <p className={styles.kpiMeta}>
                Total this year: {new Intl.NumberFormat('en-IN', { style: 'currency', currency: 'INR', maximumFractionDigits: 0 }).format(kpis.total_payroll_disbursed)}
              </p>
            </div>
          </CardContent>
        </Card>

        <Card className={styles.kpiCard}>
          <CardContent className={styles.kpiContent}>
            <div className={styles.kpiIconWrapper}>
              <AlertCircle size={24} className={styles.iconOrange} />
            </div>
            <div className={styles.kpiInfo}>
              <p className={styles.kpiLabel}>Action Items</p>
              <h3 className={styles.kpiValue}>{kpis.pending_leave_requests + kpis.unresolved_warnings}</h3>
              <p className={styles.kpiMeta}>
                <span className={styles.trendDown}>{kpis.critical_warnings} critical</span> issues
              </p>
            </div>
          </CardContent>
        </Card>
      </div>

      <div className={styles.grid2Col}>
        {/* Recent Payruns */}
        <Card>
          <CardHeader>
            <CardTitle>Recent Payroll Runs</CardTitle>
          </CardHeader>
          <CardContent>
            <div className={styles.list}>
              {recentPayruns.map((pr: any) => (
                <div key={pr.id} className={styles.listItem}>
                  <div className={styles.listIcon}>
                    <Banknote size={18} />
                  </div>
                  <div className={styles.listText}>
                    <p className={styles.listTitle}>{pr.run_number}</p>
                    <p className={styles.listDesc}>{pr.name}</p>
                  </div>
                  <div className={styles.listRight}>
                    <Badge variant={
                      pr.status === 'PAID' ? 'success' : 
                      pr.status === 'VALIDATED' ? 'primary' : 
                      pr.status === 'COMPUTED' ? 'warning' : 'default'
                    }>
                      {pr.status}
                    </Badge>
                  </div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>

        {/* Notifications */}
        <Card>
          <CardHeader>
            <CardTitle>Recent Activity</CardTitle>
          </CardHeader>
          <CardContent>
            <div className={styles.list}>
              {activeNotifications.slice(0, 5).map((n: any) => (
                <div key={n.id} className={styles.listItem}>
                  <div className={styles.listIcon}>
                    <AlertCircle size={18} />
                  </div>
                  <div className={styles.listText}>
                    <p className={styles.listTitle}>{n.title}</p>
                    <p className={styles.listDesc}>{new Date(n.published_at).toLocaleDateString()}</p>
                  </div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
