import React, { useEffect, useMemo, useState } from 'react';
import { Card } from '../../components/ui/Card/Card';
import { Badge } from '../../components/ui/Badge/Badge';
import { Button } from '../../components/ui/Button/Button';
import apiClient, { unwrapList } from '../../api/client';
import styles from './AttendanceList.module.css';
import { CalendarDays, Clock, Edit, LogIn, LogOut, Search, X } from 'lucide-react';
import { useAuth } from '../../contexts/AuthContext';
import Modal from '../../components/ui/Modal/Modal';

function recordDate(record: any) {
  return String(record?.date || record?.attendance_date || '').slice(0, 10);
}

export default function AttendanceList() {
  const { role } = useAuth();
  const isHr = role === 'HR' || role === 'ADMIN';
  const [records, setRecords] = useState<any[]>([]);
  const [employees, setEmployees] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [date, setDate] = useState(() => new Date().toISOString().slice(0, 10));
  const [employeeId, setEmployeeId] = useState('');
  const [employeeQuery, setEmployeeQuery] = useState('');
  const [pickerOpen, setPickerOpen] = useState(false);
  const [error, setError] = useState('');
  const [now, setNow] = useState(Date.now());
  const [correcting, setCorrecting] = useState<any | null>(null);
  const [correction, setCorrection] = useState({ check_in: '', check_out: '', correction_reason: '' });

  async function load() {
    setLoading(true);
    try {
      const params: any = { page_size: 500 };
      if (isHr && date) params.date = date;
      if (isHr && employeeId) {
        params.employee_id = employeeId;
        if (!date) delete params.date;
      }
      if (!isHr) delete params.date;
      const [attRes, empRes] = await Promise.all([
        apiClient.get('/attendance', { params }),
        isHr ? apiClient.get('/employees', { params: { page_size: 500 } }) : Promise.resolve({ data: [] }),
      ]);
      setRecords(unwrapList(attRes));
      setEmployees(unwrapList(empRes));
    } catch (err: any) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => { load(); }, [date, employeeId, isHr]);

  const today = new Date().toISOString().slice(0, 10);
  const todayRecord = useMemo(
    () => records.find((r) => recordDate(r) === today),
    [records, today]
  );

  useEffect(() => {
    if (!todayRecord?.check_in || todayRecord?.check_out) return undefined;
    const timer = setInterval(() => setNow(Date.now()), 1000);
    return () => clearInterval(timer);
  }, [todayRecord]);

  const selectedEmployee = employees.find((e) => e.id === employeeId);
  const filteredEmployees = employees.filter((e) => {
    const q = employeeQuery.toLowerCase().trim();
    if (!q) return true;
    return `${e.first_name} ${e.last_name} ${e.employee_code} ${e.email || ''}`.toLowerCase().includes(q);
  }).slice(0, 8);

  const visibleRecords = useMemo(() => {
    const q = employeeQuery.toLowerCase().trim();
    if (isHr && q && !employeeId) {
      return records.filter((r) =>
        `${r.employee?.first_name || ''} ${r.employee?.last_name || ''} ${r.employee?.employee_code || ''}`.toLowerCase().includes(q)
      );
    }
    return records;
  }, [records, employeeQuery, employeeId, isHr]);

  async function checkIn() {
    setError('');
    try {
      await apiClient.post('/attendance/check-in', {});
      load();
    } catch (err: any) {
      setError(err.message);
    }
  }

  async function checkOut(id?: string) {
    setError('');
    try {
      if (id) await apiClient.post(`/attendance/${id}/check-out`, {});
      else await apiClient.post('/attendance/check-out', {});
      load();
    } catch (err: any) {
      setError(err.message);
    }
  }

  function openCorrect(record: any) {
    setCorrecting(record);
    setCorrection({
      check_in: record.check_in ? String(record.check_in).slice(0, 16) : '',
      check_out: record.check_out ? String(record.check_out).slice(0, 16) : '',
      correction_reason: '',
    });
  }

  async function saveCorrection() {
    if (!correcting) return;
    setError('');
    try {
      await apiClient.post(`/attendance/${correcting.id}/correct`, {
        check_in: correction.check_in ? new Date(correction.check_in).toISOString() : null,
        check_out: correction.check_out ? new Date(correction.check_out).toISOString() : null,
        correction_reason: correction.correction_reason,
      });
      setCorrecting(null);
      load();
    } catch (err: any) {
      setError(err.message);
    }
  }

  const formatTime = (isoStr: string | null) => {
    if (!isoStr) return '—';
    return new Date(isoStr).toLocaleTimeString('en-IN', { hour: '2-digit', minute: '2-digit' });
  };

  const workedLabel = (hours: number | null) => {
    if (hours == null) return '—';
    const h = Math.floor(Number(hours));
    const m = Math.round((Number(hours) - h) * 60);
    return `${h}h ${m.toString().padStart(2, '0')}m`;
  };

  const liveWorked = () => {
    if (!todayRecord?.check_in) return '0h 00m';
    const start = new Date(todayRecord.check_in).getTime();
    const mins = Math.max(0, Math.floor((now - start) / 60000));
    return `${Math.floor(mins / 60)}h ${(mins % 60).toString().padStart(2, '0')}m`;
  };

  const getStatusVariant = (status: string) => {
    switch (status) {
      case 'PRESENT': return 'success';
      case 'LATE':
      case 'HALF_DAY': return 'warning';
      case 'ABSENT':
      case 'LEAVE': return 'danger';
      default: return 'default';
    }
  };

  return (
    <div className={styles.container}>
      <div className={styles.header}>
        <div>
          <h1 className={styles.title}>Attendance</h1>
          <p className={styles.subtitle}>{isHr ? 'Filter by day or look up one person.' : 'Check in when you start, check out when you finish.'}</p>
        </div>
      </div>
      {error && <p className="formError">{error}</p>}

      {!isHr && (
        <Card className={styles.todayCard}>
          <div className={styles.todayMeta}>
            <p className={styles.todayLabel}>Today</p>
            <h2 className={styles.todayDate}>{new Date().toLocaleDateString('en-IN', { weekday: 'long', day: 'numeric', month: 'long' })}</h2>
            {todayRecord?.check_in && !todayRecord?.check_out && (
              <p className={styles.todayHint}>Checked in at {formatTime(todayRecord.check_in)} · working {liveWorked()}</p>
            )}
            {todayRecord?.check_out && (
              <p className={styles.todayHint}>Worked {workedLabel(todayRecord.worked_hours)} · out at {formatTime(todayRecord.check_out)}</p>
            )}
            {!todayRecord?.check_in && <p className={styles.todayHint}>You have not checked in yet.</p>}
          </div>
          <div className={styles.todayActions}>
            {!todayRecord?.check_in && (
              <Button leftIcon={<LogIn size={18} />} onClick={checkIn}>Check in</Button>
            )}
            {todayRecord?.check_in && !todayRecord?.check_out && (
              <>
                <span className={styles.hoursPill}>{liveWorked()}</span>
                <Button leftIcon={<LogOut size={18} />} onClick={() => checkOut(todayRecord.id)}>Check out</Button>
              </>
            )}
            {todayRecord?.check_out && (
              <span className={styles.hoursPill}>{workedLabel(todayRecord.worked_hours)}</span>
            )}
          </div>
        </Card>
      )}

      {isHr && (
        <Card className={styles.filterCard}>
          <div className={styles.filterBar}>
            <label className={styles.dateField}>
              <CalendarDays size={16} />
              <input type="date" value={date} onChange={(e) => setDate(e.target.value)} />
            </label>
            <div className={styles.picker}>
              <Search size={16} />
              <input
                value={employeeQuery}
                onChange={(e) => { setEmployeeQuery(e.target.value); setPickerOpen(true); }}
                onFocus={() => setPickerOpen(true)}
                placeholder="Search by name or employee code"
              />
              {pickerOpen && employeeQuery && (
                <div className={styles.pickerMenu}>
                  {filteredEmployees.length === 0 ? (
                    <p className={styles.pickerEmpty}>No matching employees</p>
                  ) : filteredEmployees.map((e) => (
                    <button
                      key={e.id}
                      type="button"
                      className={styles.pickerItem}
                      onClick={() => {
                        setEmployeeId(e.id);
                        setEmployeeQuery(`${e.first_name} ${e.last_name}`);
                        setPickerOpen(false);
                      }}
                    >
                      <span>{e.first_name} {e.last_name}</span>
                      <small>{e.employee_code}</small>
                    </button>
                  ))}
                </div>
              )}
            </div>
            <Button variant="outline" onClick={() => { setDate(''); setEmployeeId(''); setEmployeeQuery(''); setPickerOpen(false); }}>All days</Button>
          </div>
          {selectedEmployee && (
            <div className={styles.chips}>
              <span className={styles.chip}>
                {selectedEmployee.first_name} {selectedEmployee.last_name}
                <small>{selectedEmployee.employee_code}</small>
                <button type="button" onClick={() => { setEmployeeId(''); setEmployeeQuery(''); }} aria-label="Clear employee">
                  <X size={14} />
                </button>
              </span>
              {date && <span className={styles.chipMuted}>{date}</span>}
            </div>
          )}
        </Card>
      )}

      <Card className={styles.tableCard}>
        <div className={styles.tableWrapper}>
          <table className={styles.table}>
            <thead>
              <tr>
                <th>Date</th>
                {isHr && <th>Employee</th>}
                <th>Check In</th>
                <th>Check Out</th>
                <th>Worked</th>
                <th>Status</th>
                {isHr && <th className={styles.actionsCell}>Actions</th>}
              </tr>
            </thead>
            <tbody>
              {loading ? (
                <tr><td colSpan={7} className={styles.loadingCell}>Loading attendance records...</td></tr>
              ) : visibleRecords.length === 0 ? (
                <tr><td colSpan={7} className={styles.emptyCell}>No records found.</td></tr>
              ) : visibleRecords.map(r => (
                <tr key={r.id}>
                  <td><span className={styles.dateCell}>{recordDate(r)}</span></td>
                  {isHr && (
                    <td>
                      <div className={styles.empInfo}>
                        <p className={styles.empName}>{r.employee?.first_name} {r.employee?.last_name}</p>
                        <span className={styles.empCode}>{r.employee?.employee_code}</span>
                      </div>
                    </td>
                  )}
                  <td><div className={styles.timeInfo}><Clock size={14} className={styles.timeIcon} /><span>{formatTime(r.check_in)}</span></div></td>
                  <td><div className={styles.timeInfo}><Clock size={14} className={styles.timeIcon} /><span>{formatTime(r.check_out)}</span></div></td>
                  <td>{r.worked_hours != null ? <span className={styles.hoursCell}>{workedLabel(r.worked_hours)}</span> : '—'}</td>
                  <td><Badge variant={getStatusVariant(r.status)}>{(r.status || '').replace('_', ' ')}</Badge></td>
                  {isHr && (
                    <td className={styles.actionsCell}>
                      <button className={styles.iconButton} title="Correct" onClick={() => openCorrect(r)}><Edit size={16} /></button>
                    </td>
                  )}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </Card>

      {correcting && (
        <Modal title="Correct attendance" onClose={() => setCorrecting(null)} footer={<><Button variant="outline" onClick={() => setCorrecting(null)}>Cancel</Button><Button onClick={saveCorrection}>Save correction</Button></>}>
          <p className="formLabel">{correcting.employee?.first_name} {correcting.employee?.last_name} · {correcting.date}</p>
          <div><label className="formLabel">Check in</label><input className="formInput" type="datetime-local" value={correction.check_in} onChange={(e) => setCorrection({ ...correction, check_in: e.target.value })} /></div>
          <div><label className="formLabel">Check out</label><input className="formInput" type="datetime-local" value={correction.check_out} onChange={(e) => setCorrection({ ...correction, check_out: e.target.value })} /></div>
          <div><label className="formLabel">Reason</label><textarea className="formInput" rows={3} value={correction.correction_reason} onChange={(e) => setCorrection({ ...correction, correction_reason: e.target.value })} /></div>
        </Modal>
      )}
    </div>
  );
}
