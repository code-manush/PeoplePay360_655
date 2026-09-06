import React, { useEffect, useState } from 'react';
import { Card } from '../../components/ui/Card/Card';
import { Badge } from '../../components/ui/Badge/Badge';
import { Button } from '../../components/ui/Button/Button';
import apiClient, { unwrapList } from '../../api/client';
import styles from './ContractList.module.css';
import { Plus, Search, Filter, Calendar } from 'lucide-react';
import Modal from '../../components/ui/Modal/Modal';

export default function ContractList() {
  const [contracts, setContracts] = useState<any[]>([]);
  const [employees, setEmployees] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState('');
  const [open, setOpen] = useState(false);
  const [error, setError] = useState('');
  const [form, setForm] = useState({ employee_id: '', start_date: '', end_date: '', wage: '', contract_type: 'FULL_TIME', salary_structure_id: '', schedule_id: '' });
  const [structures, setStructures] = useState<any[]>([]);
  const [schedules, setSchedules] = useState<any[]>([]);

  async function load() {
    setLoading(true);
    try {
      const [cRes, eRes, sRes, schRes] = await Promise.all([
        apiClient.get('/contracts', { params: { page_size: 500 } }),
        apiClient.get('/employees', { params: { page_size: 500 } }),
        apiClient.get('/payroll/salary-structures'),
        apiClient.get('/schedules'),
      ]);
      setError('');
      setContracts(unwrapList(cRes));
      setEmployees(unwrapList(eRes));
      setStructures(unwrapList(sRes));
      setSchedules(unwrapList(schRes));
    } catch (err: any) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => { load(); }, []);

  async function createContract() {
    setError('');
    try {
      await apiClient.post('/contracts', { ...form, wage: Number(form.wage) });
      setOpen(false);
      load();
    } catch (err: any) {
      setError(err.message);
    }
  }

  const formatCurrency = (val: number | null) =>
    val != null ? new Intl.NumberFormat('en-IN', { style: 'currency', currency: 'INR' }).format(val) : '—';

  const q = search.toLowerCase().trim();
  const visible = contracts.filter((c) => {
    if (!q) return true;
    const name = `${c.employee?.first_name || ''} ${c.employee?.last_name || ''} ${c.employee?.employee_code || ''} ${c.contract_number || ''}`;
    return name.toLowerCase().includes(q);
  });

  return (
    <div className={styles.container}>
      <div className={styles.header}>
        <div>
          <h1 className={styles.title}>Contracts</h1>
          <p className={styles.subtitle}>Employee contracts and compensation from peoplepay360.</p>
        </div>
        <div className={styles.actions}>
          <Button leftIcon={<Plus size={18} />} onClick={() => setOpen(true)}>New Contract</Button>
        </div>
      </div>
      {error && <p className="formError">{error}</p>}
      <Card className={styles.tableCard}>
        <div className={styles.toolbar}>
          <div className={styles.searchBar}>
            <Search size={18} className={styles.searchIcon} />
            <input placeholder="Search contracts..." className={styles.searchInput} value={search} onChange={(e) => setSearch(e.target.value)} />
          </div>
          <Button variant="outline" leftIcon={<Filter size={18} />} onClick={load}>Refresh</Button>
        </div>
        <div className={styles.tableWrapper}>
          <table className={styles.table}>
            <thead>
              <tr><th>Employee</th><th>Type</th><th>Dates</th><th>Base Salary</th><th>Status</th></tr>
            </thead>
            <tbody>
              {loading ? <tr><td colSpan={5} className={styles.loadingCell}>Loading contracts...</td></tr>
              : visible.length === 0 ? <tr><td colSpan={5} className={styles.emptyCell}>{error ? 'Could not load contracts.' : 'No contracts found.'}</td></tr>
              : visible.map(c => (
                <tr key={c.id}>
                  <td>
                    <div className={styles.empInfo}>
                      <p className={styles.empName}>{c.employee?.first_name} {c.employee?.last_name}</p>
                      <span className={styles.empCode}>{c.employee?.employee_code}</span>
                    </div>
                  </td>
                  <td>
                    <p className={styles.cType}>{(c.contract_type || c.employment_type || '—').replace('_', ' ')}</p>
                    <p className={styles.cWage}>{c.wage_type || 'MONTHLY'}</p>
                  </td>
                  <td>
                    <div className={styles.dateInfo}><Calendar size={14} className={styles.iconMuted} /><span>{c.start_date}</span></div>
                    {c.end_date && <div className={styles.dateInfo}><span style={{marginLeft: 18}}>to {c.end_date}</span></div>}
                  </td>
                  <td><span className={styles.currency}>{formatCurrency(c.base_salary ?? c.wage)}</span></td>
                  <td><Badge variant={c.status === 'ACTIVE' ? 'success' : 'default'}>{c.status}</Badge></td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </Card>
      {open && (
        <Modal title="New contract" onClose={() => setOpen(false)} footer={<><Button variant="outline" onClick={() => setOpen(false)}>Cancel</Button><Button onClick={createContract}>Create</Button></>}>
          <div>
            <label className="formLabel">Employee</label>
            <select className="formInput" value={form.employee_id} onChange={(e) => setForm({ ...form, employee_id: e.target.value })}>
              <option value="">Select</option>
              {employees.map((e) => <option key={e.id} value={e.id}>{e.first_name} {e.last_name}</option>)}
            </select>
          </div>
          <div><label className="formLabel">Start date</label><input className="formInput" type="date" value={form.start_date} onChange={(e) => setForm({ ...form, start_date: e.target.value })} /></div>
          <div><label className="formLabel">End date</label><input className="formInput" type="date" value={form.end_date} onChange={(e) => setForm({ ...form, end_date: e.target.value })} /></div>
          <div><label className="formLabel">Monthly wage</label><input className="formInput" type="number" value={form.wage} onChange={(e) => setForm({ ...form, wage: e.target.value })} /></div>
          <div>
            <label className="formLabel">Salary structure</label>
            <select className="formInput" value={form.salary_structure_id} onChange={(e) => setForm({ ...form, salary_structure_id: e.target.value })}>
              <option value="">Select structure</option>
              {structures.map((s) => <option key={s.id} value={s.id}>{s.name}</option>)}
            </select>
          </div>
          <div>
            <label className="formLabel">Work schedule</label>
            <select className="formInput" value={form.schedule_id} onChange={(e) => setForm({ ...form, schedule_id: e.target.value })}>
              <option value="">Default weekdays</option>
              {schedules.map((s) => <option key={s.id} value={s.id}>{s.name}</option>)}
            </select>
          </div>
          {error && <p className="formError">{error}</p>}
        </Modal>
      )}
    </div>
  );
}
