import { useEffect, useState } from 'react';
import { Card } from '../../components/ui/Card/Card';
import { Button } from '../../components/ui/Button/Button';
import apiClient, { unwrapList } from '../../api/client';
import styles from '../Leave/LeaveList.module.css';
import { Plus } from 'lucide-react';
import Modal from '../../components/ui/Modal/Modal';
import { useAuth } from '../../contexts/AuthContext';

export default function Organization() {
  const { role } = useAuth();
  const isHr = role === 'HR' || role === 'ADMIN';
  const [departments, setDepartments] = useState<any[]>([]);
  const [positions, setPositions] = useState<any[]>([]);
  const [error, setError] = useState('');
  const [deptOpen, setDeptOpen] = useState(false);
  const [posOpen, setPosOpen] = useState(false);
  const [deptForm, setDeptForm] = useState({ name: '', code: '' });
  const [posForm, setPosForm] = useState({ name: '', department_id: '', description: '' });

  async function load() {
    try {
      const [d, p] = await Promise.all([
        apiClient.get('/departments'),
        apiClient.get('/job-positions'),
      ]);
      setDepartments(unwrapList(d));
      setPositions(unwrapList(p));
      setError('');
    } catch (err: any) {
      setError(err.message);
    }
  }

  useEffect(() => { load(); }, []);

  async function saveDept() {
    try {
      await apiClient.post('/departments', deptForm);
      setDeptOpen(false);
      setDeptForm({ name: '', code: '' });
      load();
    } catch (err: any) {
      setError(err.message);
    }
  }

  async function savePos() {
    try {
      await apiClient.post('/job-positions', posForm);
      setPosOpen(false);
      setPosForm({ name: '', department_id: '', description: '' });
      load();
    } catch (err: any) {
      setError(err.message);
    }
  }

  return (
    <div className={styles.container}>
      <div className={styles.header}>
        <div>
          <h1 className={styles.title}>Organization</h1>
          <p className={styles.subtitle}>Departments and job positions in peoplepay360.</p>
        </div>
        {isHr && (
          <div className={styles.actions}>
            <Button variant="outline" leftIcon={<Plus size={18} />} onClick={() => setDeptOpen(true)}>Department</Button>
            <Button leftIcon={<Plus size={18} />} onClick={() => setPosOpen(true)}>Position</Button>
          </div>
        )}
      </div>
      {error && <p className="formError">{error}</p>}
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1.5rem' }}>
        <Card className={styles.tableCard}>
          <table className={styles.table}>
            <thead><tr><th>Department</th><th>Code</th></tr></thead>
            <tbody>
              {departments.map((d) => (
                <tr key={d.id}><td className={styles.empName}>{d.name}</td><td className={styles.empCode}>{d.code}</td></tr>
              ))}
            </tbody>
          </table>
        </Card>
        <Card className={styles.tableCard}>
          <table className={styles.table}>
            <thead><tr><th>Position</th><th>Department</th></tr></thead>
            <tbody>
              {positions.map((p) => (
                <tr key={p.id}>
                  <td className={styles.empName}>{p.name || p.title}</td>
                  <td className={styles.empCode}>{departments.find((d) => d.id === p.department_id)?.name || '—'}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </Card>
      </div>
      {deptOpen && (
        <Modal title="New department" onClose={() => setDeptOpen(false)} footer={<><Button variant="outline" onClick={() => setDeptOpen(false)}>Cancel</Button><Button onClick={saveDept}>Create</Button></>}>
          <div><label className="formLabel">Name</label><input className="formInput" value={deptForm.name} onChange={(e) => setDeptForm({ ...deptForm, name: e.target.value })} /></div>
          <div><label className="formLabel">Code</label><input className="formInput" value={deptForm.code} onChange={(e) => setDeptForm({ ...deptForm, code: e.target.value })} /></div>
        </Modal>
      )}
      {posOpen && (
        <Modal title="New position" onClose={() => setPosOpen(false)} footer={<><Button variant="outline" onClick={() => setPosOpen(false)}>Cancel</Button><Button onClick={savePos}>Create</Button></>}>
          <div><label className="formLabel">Name</label><input className="formInput" value={posForm.name} onChange={(e) => setPosForm({ ...posForm, name: e.target.value })} /></div>
          <div>
            <label className="formLabel">Department</label>
            <select className="formInput" value={posForm.department_id} onChange={(e) => setPosForm({ ...posForm, department_id: e.target.value })}>
              <option value="">Select</option>
              {departments.map((d) => <option key={d.id} value={d.id}>{d.name}</option>)}
            </select>
          </div>
        </Modal>
      )}
    </div>
  );
}
