import { useEffect, useState } from 'react';
import { Search } from 'lucide-react';
import { Card } from '../../components/ui/Card/Card';
import { Badge } from '../../components/ui/Badge/Badge';
import { Button } from '../../components/ui/Button/Button';
import { useAuth } from '../../contexts/AuthContext';
import apiClient, { unwrapList } from '../../api/client';
import styles from '../Payroll/PayrollList.module.css';

function formatWhen(value?: string) {
  if (!value) return '—';
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return String(value).replace('T', ' ').slice(0, 19);
  return date.toLocaleString('en-IN', {
    timeZone: 'Asia/Kolkata',
    day: '2-digit',
    month: 'short',
    year: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  });
}

function formatAction(action?: string) {
  return String(action || 'Unknown').replace(/_/g, ' ').toLowerCase().replace(/\b\w/g, (c) => c.toUpperCase());
}

const ACTION_OPTIONS = [
  'PAYRUN_CREATED', 'PAYRUN_COMPUTED', 'PAYRUN_VALIDATED', 'PAYRUN_PAID', 'PAYRUN_CANCELLED',
  'LEAVE_APPROVED', 'LEAVE_REJECTED', 'EMPLOYEE_CREATED', 'EMPLOYEE_UPDATED',
  'CONTRACT_CREATED', 'CONTRACT_RENEWED', 'ATTENDANCE_CORRECTED',
];

function actionVariant(action?: string): 'success' | 'warning' | 'danger' | 'primary' | 'default' {
  const value = String(action || '').toUpperCase();
  if (value.includes('PAID') || value.includes('APPROVED') || value.includes('CREATED')) return 'success';
  if (value.includes('REJECT') || value.includes('CANCEL') || value.includes('DEACTIV')) return 'danger';
  if (value.includes('COMPUTE') || value.includes('CORRECT')) return 'warning';
  if (value.includes('VALIDAT')) return 'primary';
  return 'default';
}

export default function AuditLogs() {
  const { role } = useAuth();
  const canView = role === 'HR' || role === 'ADMIN';
  const [logs, setLogs] = useState<any[]>([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [search, setSearch] = useState('');
  const [eventType, setEventType] = useState('');

  async function load() {
    if (!canView) {
      setLoading(false);
      setLogs([]);
      return;
    }
    setLoading(true);
    try {
      const res: any = await apiClient.get('/audit', {
        params: { page_size: 200, search: search || undefined, event_type: eventType || undefined },
      });
      setLogs(unwrapList(res));
      setTotal(res?.meta?.total ?? unwrapList(res).length);
      setError('');
    } catch (err: any) {
      setError(err.message || 'Failed to load audit logs');
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => { load(); }, [canView]);

  const actions = Array.from(new Set([...ACTION_OPTIONS, ...logs.map((log) => log.event_type || log.action).filter(Boolean)]));

  return (
    <div className={styles.container}>
      <div className={styles.header}>
        <div>
          <h1 className={styles.title}>Audit log</h1>
          <p className={styles.subtitle}>Who changed what in peoplepay360, newest first.</p>
        </div>
        <Button variant="outline" onClick={load}>Refresh</Button>
      </div>
      {error && <p className="formError">{error}</p>}
      <Card className={styles.tableCard}>
        <div className={styles.toolbar}>
          <div className={styles.searchBar}>
            <Search size={18} className={styles.searchIcon} />
            <input
              type="text"
              placeholder="Search action or entity..."
              className={styles.searchInput}
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              onKeyDown={(e) => { if (e.key === 'Enter') load(); }}
            />
          </div>
          <select className="formInput" style={{ width: 220 }} value={eventType} onChange={(e) => setEventType(e.target.value)}>
            <option value="">All actions</option>
            {actions.map((action) => (
              <option key={action} value={action}>{formatAction(action)}</option>
            ))}
          </select>
          <Button variant="outline" onClick={load}>Apply</Button>
        </div>
        <div className={styles.tableWrapper}>
          <table className={styles.table}>
            <thead>
              <tr>
                <th>When (IST)</th>
                <th>Action</th>
                <th>Entity</th>
                <th>Actor</th>
                <th>Detail</th>
              </tr>
            </thead>
            <tbody>
              {loading ? (
                <tr><td colSpan={5} className={styles.loadingCell}>Loading audit events...</td></tr>
              ) : logs.length === 0 ? (
                <tr><td colSpan={5} className={styles.emptyCell}>No audit events yet.</td></tr>
              ) : logs.map((log) => (
                <tr key={log.id}>
                  <td className={styles.prCode}>{formatWhen(log.created_at)}</td>
                  <td><Badge variant={actionVariant(log.event_type || log.action)}>{formatAction(log.event_type || log.action)}</Badge></td>
                  <td>{log.entity_type || log.entity_table || '—'}</td>
                  <td>{log.actor_email || log.actor_role || 'System'}</td>
                  <td>{log.description || '—'}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </Card>
      {!loading && <p className={styles.subtitle}>{total} event{total === 1 ? '' : 's'}</p>}
    </div>
  );
}
