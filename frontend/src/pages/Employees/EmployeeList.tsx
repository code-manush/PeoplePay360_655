import React, { useEffect, useState } from 'react';
import { Card } from '../../components/ui/Card/Card';
import { Badge } from '../../components/ui/Badge/Badge';
import { Button } from '../../components/ui/Button/Button';
import apiClient, { unwrapList } from '../../api/client';
import styles from './EmployeeList.module.css';
import { Plus, Search, Filter, Edit2, UserX } from 'lucide-react';
import Modal from '../../components/ui/Modal/Modal';

const emptyForm = { first_name: '', last_name: '', email: '', phone: '', department_id: '', job_position_id: '', employment_type: 'FULL_TIME' };

export default function EmployeeList() {
  const [employees, setEmployees] = useState<any[]>([]);
  const [departments, setDepartments] = useState<any[]>([]);
  const [positions, setPositions] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState('');
  const [open, setOpen] = useState(false);
  const [editingId, setEditingId] = useState<string | null>(null);
  const [error, setError] = useState('');
  const [form, setForm] = useState(emptyForm);

  async function load() {
    setLoading(true);
    try {
      const [empRes, deptRes, posRes] = await Promise.all([
        apiClient.get('/employees', { params: { page_size: 500, search: search || undefined } }),
        apiClient.get('/departments'),
        apiClient.get('/job-positions'),
      ]);
      setEmployees(unwrapList(empRes));
      setDepartments(unwrapList(deptRes));
      setPositions(unwrapList(posRes));
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => { load(); }, []);

  const [departmentFilter, setDepartmentFilter] = useState('');
  const [statusFilter, setStatusFilter] = useState('');

  const filtered = employees.filter(e => {
    const matchesSearch = `${e.first_name} ${e.last_name}`.toLowerCase().includes(search.toLowerCase()) ||
      (e.employee_code || '').toLowerCase().includes(search.toLowerCase()) ||
      (e.email || '').toLowerCase().includes(search.toLowerCase());
    
    const matchesDept = departmentFilter ? e.department_id === departmentFilter : true;
    const matchesStatus = statusFilter ? e.employment_status === statusFilter || e.status === statusFilter : true;

    return matchesSearch && matchesDept && matchesStatus;
  });

  function openCreate() {
    setEditingId(null);
    setForm(emptyForm);
    setError('');
    setOpen(true);
  }

  function openEdit(emp: any) {
    setEditingId(emp.id);
    setForm({
      first_name: emp.first_name || '',
      last_name: emp.last_name || '',
      email: emp.email || '',
      phone: emp.phone || '',
      department_id: emp.department_id || '',
      job_position_id: emp.job_position_id || '',
      employment_type: emp.employment_type || 'FULL_TIME',
    });
    setError('');
    setOpen(true);
  }

  async function saveEmployee() {
    setError('');
    try {
      if (editingId) {
        await apiClient.put(`/employees/${editingId}`, form);
      } else {
        await apiClient.post('/employees', form);
      }
      setOpen(false);
      setEditingId(null);
      setForm(emptyForm);
      load();
    } catch (err: any) {
      setError(err.message);
    }
  }

  async function deactivate(id: string) {
    if (!window.confirm('Deactivate this employee? They will no longer be able to sign in.')) return;
    await apiClient.patch(`/employees/${id}/deactivate`);
    load();
  }

  return (
    <div className={styles.container}>
      <div className={styles.header}>
        <div>
          <h1 className={styles.title}>Employees</h1>
          <p className={styles.subtitle}>Workforce records from the peoplepay360 database.</p>
        </div>
        <div className={styles.actions}>
          <Button leftIcon={<Plus size={18} />} onClick={openCreate}>Add Employee</Button>
        </div>
      </div>

      <Card className={styles.tableCard}>
        <div className={styles.toolbar}>
          <div className={styles.searchBar}>
            <Search size={18} className={styles.searchIcon} />
            <input placeholder="Search by name, email or ID..." className={styles.searchInput} value={search} onChange={(e) => setSearch(e.target.value)} />
          </div>
          
          <select 
            className="formInput" 
            style={{ width: '200px' }} 
            value={departmentFilter} 
            onChange={(e) => setDepartmentFilter(e.target.value)}
          >
            <option value="">All Departments (Branches)</option>
            {departments.map(d => <option key={d.id} value={d.id}>{d.name}</option>)}
          </select>

          <select 
            className="formInput" 
            style={{ width: '150px' }} 
            value={statusFilter} 
            onChange={(e) => setStatusFilter(e.target.value)}
          >
            <option value="">All Statuses</option>
            <option value="ACTIVE">Active</option>
            <option value="INACTIVE">Inactive</option>
          </select>

          <Button variant="outline" leftIcon={<Filter size={18} />} onClick={load}>Refresh</Button>
        </div>
        <div className={styles.tableWrapper}>
          <table className={styles.table}>
            <thead>
              <tr>
                <th>Employee</th><th>Employee ID</th><th>Department</th><th>Role</th><th>Status</th><th className={styles.actionsCell}>Actions</th>
              </tr>
            </thead>
            <tbody>
              {loading ? (
                <tr><td colSpan={6} className={styles.loadingCell}>Loading employees...</td></tr>
              ) : filtered.length === 0 ? (
                <tr><td colSpan={6} className={styles.emptyCell}>No employees found.</td></tr>
              ) : filtered.map(emp => (
                <tr key={emp.id}>
                  <td>
                    <div className={styles.employeeInfo}>
                      <div className={styles.avatar}>{emp.first_name?.[0]}{emp.last_name?.[0]}</div>
                      <div>
                        <p className={styles.empName}>{emp.first_name} {emp.last_name}</p>
                        <p className={styles.empEmail}>{emp.email}</p>
                      </div>
                    </div>
                  </td>
                  <td><span className={styles.empCode}>{emp.employee_code}</span></td>
                  <td>{emp.department?.name || '—'}</td>
                  <td>{emp.job_position?.title || emp.job_position?.name || '—'}</td>
                  <td><Badge variant={emp.is_active ? 'success' : 'default'}>{(emp.employment_status || emp.status || '').replace('_', ' ')}</Badge></td>
                  <td className={styles.actionsCell}>
                    <div className={styles.actionButtons}>
                      <button className={styles.iconButton} title="Edit" onClick={() => openEdit(emp)}><Edit2 size={16} /></button>
                      <button className={styles.iconButton} title="Deactivate" onClick={() => deactivate(emp.id)}><UserX size={16} /></button>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </Card>

      {open && (
        <Modal title={editingId ? 'Edit employee' : 'Add employee'} onClose={() => setOpen(false)} footer={<><Button variant="outline" onClick={() => setOpen(false)}>Cancel</Button><Button onClick={saveEmployee}>{editingId ? 'Update' : 'Save'}</Button></>}>
          <div><label className="formLabel">First name</label><input className="formInput" value={form.first_name} onChange={(e) => setForm({ ...form, first_name: e.target.value })} /></div>
          <div><label className="formLabel">Last name</label><input className="formInput" value={form.last_name} onChange={(e) => setForm({ ...form, last_name: e.target.value })} /></div>
          <div><label className="formLabel">Email</label><input className="formInput" value={form.email} onChange={(e) => setForm({ ...form, email: e.target.value })} disabled={!!editingId} /></div>
          <div><label className="formLabel">Phone</label><input className="formInput" value={form.phone} onChange={(e) => setForm({ ...form, phone: e.target.value })} /></div>
          <div>
            <label className="formLabel">Department</label>
            <select className="formInput" value={form.department_id} onChange={(e) => setForm({ ...form, department_id: e.target.value })}>
              <option value="">Select</option>
              {departments.map((d) => <option key={d.id} value={d.id}>{d.name}</option>)}
            </select>
          </div>
          <div>
            <label className="formLabel">Position</label>
            <select className="formInput" value={form.job_position_id} onChange={(e) => setForm({ ...form, job_position_id: e.target.value })}>
              <option value="">Select</option>
              {positions.map((p) => <option key={p.id} value={p.id}>{p.title || p.name}</option>)}
            </select>
          </div>
          {error && <p className="formError">{error}</p>}
        </Modal>
      )}
    </div>
  );
}
