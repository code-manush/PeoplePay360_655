import React, { useEffect, useState } from 'react';
import { Card } from '../../components/ui/Card/Card';
import { Badge } from '../../components/ui/Badge/Badge';
import { Button } from '../../components/ui/Button/Button';
import apiClient, { unwrapList } from '../../api/client';
import styles from './LeaveList.module.css';
import { Plus, Search, Filter, Check, X } from 'lucide-react';
import Modal from '../../components/ui/Modal/Modal';
import { useAuth } from '../../contexts/AuthContext';

export default function LeaveList() {
  const { role } = useAuth();
  const isHr = role === 'HR' || role === 'ADMIN';
  const [requests, setRequests] = useState<any[]>([]);
  const [types, setTypes] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState('');
  const [open, setOpen] = useState(false);
  const [rejectId, setRejectId] = useState<string | null>(null);
  const [reason, setReason] = useState('');
  const [error, setError] = useState('');
  const [form, setForm] = useState({ time_off_type_id: '', start_date: '', end_date: '', reason: '' });

  async function load() {
    setLoading(true);
    try {
      const [reqRes, typeRes] = await Promise.all([
        apiClient.get('/leave/requests', { params: { page_size: 200 } }),
        apiClient.get('/time-off/types'),
      ]);
      setRequests(unwrapList(reqRes));
      const loadedTypes = unwrapList(typeRes);
      setTypes(loadedTypes);
      setForm((prev) => prev.time_off_type_id || !loadedTypes[0] ? prev : { ...prev, time_off_type_id: loadedTypes[0].id });
    } catch (err: any) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => { load(); }, []);

  async function applyLeave() {
    setError('');
    if (!form.time_off_type_id) {
      setError('Please select a leave type.');
      return;
    }
    if (!form.start_date || !form.end_date) {
      setError('Please choose start and end dates.');
      return;
    }
    if (!form.reason.trim()) {
      setError('Please add a reason for the leave.');
      return;
    }
    try {
      await apiClient.post('/leave/requests', form);
      setOpen(false);
      setForm({ time_off_type_id: types[0]?.id || '', start_date: '', end_date: '', reason: '' });
      load();
    } catch (err: any) {
      setError(err.message);
    }
  }

  async function approve(id: string) {
    await apiClient.post(`/leave/requests/${id}/approve`, {});
    load();
  }

  async function reject() {
    if (!rejectId) return;
    await apiClient.post(`/leave/requests/${rejectId}/reject`, { reason });
    setRejectId(null);
    setReason('');
    load();
  }

  const getStatusVariant = (status: string) => {
    switch (status) {
      case 'APPROVED': return 'success';
      case 'PENDING': return 'warning';
      case 'REJECTED': return 'danger';
      default: return 'default';
    }
  };

  return (
    <div className={styles.container}>
      <div className={styles.header}>
        <div>
          <h1 className={styles.title}>Leave Management</h1>
          <p className={styles.subtitle}>{isHr ? 'Review and approve employee time-off requests.' : 'Apply for leave and track your requests.'}</p>
        </div>
        <div className={styles.actions}>
          <Button leftIcon={<Plus size={18} />} onClick={() => setOpen(true)}>Request Leave</Button>
        </div>
      </div>

      <Card className={styles.tableCard}>
        <div className={styles.toolbar}>
          <div className={styles.searchBar}>
            <Search size={18} className={styles.searchIcon} />
            <input placeholder="Search by employee name..." className={styles.searchInput} value={search} onChange={(e) => setSearch(e.target.value)} />
          </div>
          <Button variant="outline" leftIcon={<Filter size={18} />} onClick={load}>Refresh</Button>
        </div>
        <div className={styles.tableWrapper}>
          <table className={styles.table}>
            <thead>
              <tr>
                <th>Employee</th><th>Leave Type</th><th>Dates</th><th>Duration</th><th>Reason</th><th>Status</th>
                {isHr && <th className={styles.actionsCell}>Actions</th>}
              </tr>
            </thead>
            <tbody>
              {loading ? (
                <tr><td colSpan={7} className={styles.loadingCell}>Loading leave requests...</td></tr>
              ) : requests.filter((r) => `${r.employee?.first_name || ''} ${r.employee?.last_name || ''} ${r.reason || ''}`.toLowerCase().includes(search.toLowerCase())).length === 0 ? (
                <tr><td colSpan={7} className={styles.emptyCell}>No requests found.</td></tr>
              ) : requests.filter((r) => `${r.employee?.first_name || ''} ${r.employee?.last_name || ''} ${r.reason || ''}`.toLowerCase().includes(search.toLowerCase())).map(r => (
                <tr key={r.id}>
                  <td>
                    <div className={styles.empInfo}>
                      <p className={styles.empName}>{r.employee?.first_name} {r.employee?.last_name}</p>
                      <span className={styles.empCode}>{r.employee?.employee_code}</span>
                    </div>
                  </td>
                  <td>{r.time_off_type?.name || '—'}</td>
                  <td>{r.start_date} – {r.end_date}</td>
                  <td><span className={styles.duration}>{r.duration_days || r.requested_units} days</span></td>
                  <td>{r.reason || '—'}</td>
                  <td><Badge variant={getStatusVariant(r.status)}>{r.status}</Badge></td>
                  {isHr && (
                    <td className={styles.actionsCell}>
                      {r.status === 'PENDING' ? (
                        <div className={styles.actionButtons}>
                          <button className={styles.iconButtonSuccess} title="Approve" onClick={() => approve(r.id)}><Check size={16} /></button>
                          <button className={styles.iconButtonDanger} title="Reject" onClick={() => setRejectId(r.id)}><X size={16} /></button>
                        </div>
                      ) : '—'}
                    </td>
                  )}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </Card>

      {open && (
        <Modal title="Apply for leave" onClose={() => setOpen(false)} footer={<><Button variant="outline" onClick={() => setOpen(false)}>Cancel</Button><Button onClick={applyLeave}>Submit request</Button></>}>
          <div>
            <label className="formLabel">Leave type</label>
            <select className="formInput" value={form.time_off_type_id} onChange={(e) => setForm({ ...form, time_off_type_id: e.target.value })}>
              <option value="">Select type</option>
              {types.map((t) => <option key={t.id} value={t.id}>{t.name}</option>)}
            </select>
          </div>
          <div><label className="formLabel">Start date</label><input className="formInput" type="date" value={form.start_date} onChange={(e) => setForm({ ...form, start_date: e.target.value })} /></div>
          <div><label className="formLabel">End date</label><input className="formInput" type="date" value={form.end_date} onChange={(e) => setForm({ ...form, end_date: e.target.value })} /></div>
          <div><label className="formLabel">Reason / message</label><textarea className="formInput" rows={3} value={form.reason} onChange={(e) => setForm({ ...form, reason: e.target.value })} /></div>
          {error && <p className="formError">{error}</p>}
        </Modal>
      )}

      {rejectId && (
        <Modal title="Reject leave request" onClose={() => setRejectId(null)} footer={<><Button variant="outline" onClick={() => setRejectId(null)}>Cancel</Button><Button variant="danger" onClick={reject}>Reject</Button></>}>
          <div><label className="formLabel">Reason for the employee</label><textarea className="formInput" rows={3} value={reason} onChange={(e) => setReason(e.target.value)} /></div>
        </Modal>
      )}
    </div>
  );
}
