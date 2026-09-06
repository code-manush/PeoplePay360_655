import { useEffect, useState } from 'react';
import { Card } from '../../components/ui/Card/Card';
import { Button } from '../../components/ui/Button/Button';
import apiClient, { unwrapList } from '../../api/client';
import styles from '../Leave/LeaveList.module.css';
import { Plus } from 'lucide-react';
import Modal from '../../components/ui/Modal/Modal';
import { useAuth } from '../../contexts/AuthContext';

const DAYS = ['MONDAY', 'TUESDAY', 'WEDNESDAY', 'THURSDAY', 'FRIDAY', 'SATURDAY', 'SUNDAY'];

export default function ScheduleList() {
  const { role } = useAuth();
  const isHr = role === 'HR' || role === 'ADMIN';
  const [schedules, setSchedules] = useState<any[]>([]);
  const [error, setError] = useState('');
  const [open, setOpen] = useState(false);
  const [form, setForm] = useState({ name: '', description: '' });

  async function load() {
    try {
      setSchedules(unwrapList(await apiClient.get('/schedules')));
      setError('');
    } catch (err: any) {
      setError(err.message);
    }
  }

  useEffect(() => { load(); }, []);

  async function createSchedule() {
    try {
      const days = DAYS.map((day) => ({
        day_of_week: day,
        is_working: !['SATURDAY', 'SUNDAY'].includes(day),
        start_time: '09:00:00',
        end_time: '18:00:00',
        expected_hours: 9,
      }));
      await apiClient.post('/schedules', { ...form, days });
      setOpen(false);
      setForm({ name: '', description: '' });
      load();
    } catch (err: any) {
      setError(err.message);
    }
  }

  return (
    <div className={styles.container}>
      <div className={styles.header}>
        <div>
          <h1 className={styles.title}>Work Schedules</h1>
          <p className={styles.subtitle}>Weekly hours used for attendance and payroll working days.</p>
        </div>
        {isHr && <Button leftIcon={<Plus size={18} />} onClick={() => setOpen(true)}>New schedule</Button>}
      </div>
      {error && <p className="formError">{error}</p>}
      <Card className={styles.tableCard}>
        <table className={styles.table}>
          <thead><tr><th>Name</th><th>Working days</th><th>Weekly hours</th></tr></thead>
          <tbody>
            {schedules.length === 0 ? (
              <tr><td colSpan={3} className={styles.emptyCell}>No schedules yet.</td></tr>
            ) : schedules.map((s) => (
              <tr key={s.id}>
                <td className={styles.empName}>{s.name}</td>
                <td>{s.working_days_count ?? (s.days || []).filter((d: any) => d.is_working).length}</td>
                <td>{s.weekly_hours ?? '—'}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </Card>
      {open && (
        <Modal title="New schedule" onClose={() => setOpen(false)} footer={<><Button variant="outline" onClick={() => setOpen(false)}>Cancel</Button><Button onClick={createSchedule}>Create Mon–Fri 9–6</Button></>}>
          <div><label className="formLabel">Name</label><input className="formInput" value={form.name} onChange={(e) => setForm({ ...form, name: e.target.value })} /></div>
          <div><label className="formLabel">Description</label><input className="formInput" value={form.description} onChange={(e) => setForm({ ...form, description: e.target.value })} /></div>
        </Modal>
      )}
    </div>
  );
}
