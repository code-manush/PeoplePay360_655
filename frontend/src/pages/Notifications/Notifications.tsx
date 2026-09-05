import React, { useEffect, useState } from 'react';
import { Card } from '../../components/ui/Card/Card';
import { Badge } from '../../components/ui/Badge/Badge';
import { Button } from '../../components/ui/Button/Button';
import apiClient, { unwrapList } from '../../api/client';
import styles from '../Employees/EmployeeList.module.css';
import Modal from '../../components/ui/Modal/Modal';
import { useAuth } from '../../contexts/AuthContext';
import { Plus } from 'lucide-react';

export default function Notifications() {
  const { role } = useAuth();
  const canSend = role === 'HR' || role === 'ADMIN';
  const [items, setItems] = useState<any[]>([]);
  const [departments, setDepartments] = useState<any[]>([]);
  const [employees, setEmployees] = useState<any[]>([]);
  const [open, setOpen] = useState(false);
  const [error, setError] = useState('');
  const [form, setForm] = useState({ title: '', message: '', target_type: 'ALL', target_id: '', priority: 'NORMAL' });

  async function load() {
    try {
      const [notes, depts, emps] = await Promise.all([
        apiClient.get('/notifications/inbox'),
        canSend ? apiClient.get('/departments') : Promise.resolve({ data: [] }),
        canSend ? apiClient.get('/employees', { params: { page_size: 500 } }) : Promise.resolve({ data: [] }),
      ]);
      setItems(unwrapList(notes).filter((n: any) => {
        if (canSend) return true;
        const target = String(n.target_type || '').toUpperCase();
        const type = String(n.type || '').toUpperCase();
        const title = String(n.title || '').toLowerCase();
        const staffOnly = target === 'ROLE' || ((type === 'LEAVE' || title.includes('leave request')) && target !== 'EMPLOYEE');
        return !staffOnly;
      }));
      setDepartments(unwrapList(depts));
      setEmployees(unwrapList(emps));
    } catch (err: any) {
      setError(err.message);
    }
  }

  useEffect(() => { load(); }, []);

  async function send() {
    setError('');
    if (!form.title.trim() || !form.message.trim()) {
      setError('Title and message are required.');
      return;
    }
    if ((form.target_type === 'DEPARTMENT' || form.target_type === 'EMPLOYEE') && !form.target_id) {
      setError('Please choose who should receive this notification.');
      return;
    }
    try {
      await apiClient.post('/notifications', form);
      setOpen(false);
      setForm({ title: '', message: '', target_type: 'ALL', target_id: '', priority: 'NORMAL' });
      load();
    } catch (err: any) {
      const msg = String(err.message || '');
      if (msg.toLowerCase().includes('role')) {
        setError('This account cannot send notifications. Sign out and sign in as Admin or HR.');
      } else {
        setError(err.message);
      }
    }
  }

  return (
    <div className={styles.container}>
      <div className={styles.header}>
        <div>
          <h1 className={styles.title}>Notifications</h1>
          <p className={styles.subtitle}>{canSend ? 'Company messages and leave requests waiting for HR or Admin.' : 'Announcements sent to you. Leave replies stay private.'}</p>
        </div>
        {canSend && <Button leftIcon={<Plus size={18} />} onClick={() => setOpen(true)}>Send notification</Button>}
      </div>
      <Card className={styles.tableCard}>
        <div className={styles.tableWrapper}>
          <table className={styles.table}>
            <thead>
              <tr><th>Title</th><th>Message</th><th>Audience</th><th>Priority</th><th>Sent</th></tr>
            </thead>
            <tbody>
              {items.length === 0 ? (
                <tr><td colSpan={5} className={styles.emptyCell}>No notifications yet.</td></tr>
              ) : items.map((n) => (
                <tr key={n.id}>
                  <td><strong>{n.title}</strong></td>
                  <td>{n.message || n.body}</td>
                  <td>{n.target_type}</td>
                  <td><Badge variant={n.priority === 'HIGH' || n.priority === 'URGENT' ? 'warning' : 'default'}>{n.priority || 'NORMAL'}</Badge></td>
                  <td>{n.published_at ? new Date(n.published_at).toLocaleString() : '—'}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </Card>
      {open && (
        <Modal title="Notify people" onClose={() => setOpen(false)} footer={<><Button variant="outline" onClick={() => setOpen(false)}>Cancel</Button><Button onClick={send}>Send</Button></>}>
          <div><label className="formLabel">Title</label><input className="formInput" value={form.title} onChange={(e) => setForm({ ...form, title: e.target.value })} /></div>
          <div><label className="formLabel">Message</label><textarea className="formInput" rows={4} value={form.message} onChange={(e) => setForm({ ...form, message: e.target.value })} /></div>
          <div>
            <label className="formLabel">Audience</label>
            <select className="formInput" value={form.target_type} onChange={(e) => setForm({ ...form, target_type: e.target.value, target_id: '' })}>
              <option value="ALL">Everyone</option>
              <option value="ALL_EMPLOYEES">All employees</option>
              <option value="ROLE">HR and Admin</option>
              <option value="DEPARTMENT">A department</option>
              <option value="EMPLOYEE">One employee</option>
            </select>
          </div>
          {form.target_type === 'DEPARTMENT' && (
            <select className="formInput" value={form.target_id} onChange={(e) => setForm({ ...form, target_id: e.target.value })}>
              <option value="">Select department</option>
              {departments.map((d) => <option key={d.id} value={d.id}>{d.name}</option>)}
            </select>
          )}
          {form.target_type === 'EMPLOYEE' && (
            <select className="formInput" value={form.target_id} onChange={(e) => setForm({ ...form, target_id: e.target.value })}>
              <option value="">Select employee</option>
              {employees.map((e) => <option key={e.id} value={e.id}>{e.first_name} {e.last_name}</option>)}
            </select>
          )}
          {error && <p className="formError">{error}</p>}
        </Modal>
      )}
    </div>
  );
}
