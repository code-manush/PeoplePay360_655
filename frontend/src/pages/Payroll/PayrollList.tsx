import React, { useEffect, useState } from 'react';
import { Card } from '../../components/ui/Card/Card';
import { Badge } from '../../components/ui/Badge/Badge';
import { Button } from '../../components/ui/Button/Button';
import { Plus, Search, Filter, FileText, CheckCircle, PlayCircle, Download } from 'lucide-react';
import { useAuth } from '../../contexts/AuthContext';
import Modal from '../../components/ui/Modal/Modal';
import apiClient, { unwrapList, unwrapData, downloadPayslipPdf } from '../../api/client';
import styles from './PayrollList.module.css';

export default function PayrollList() {
  const { role } = useAuth();
  const isHr = role === 'HR' || role === 'ADMIN';
  const [payruns, setPayruns] = useState<any[]>([]);
  const [payslips, setPayslips] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState('');
  const [open, setOpen] = useState(false);
  const [detail, setDetail] = useState<any | null>(null);
  const [payslipDetail, setPayslipDetail] = useState<any | null>(null);
  const [error, setError] = useState('');
  const [saving, setSaving] = useState(false);
  const [form, setForm] = useState({ period_start: '', period_end: '', include: 'sample' });

  async function load() {
    setLoading(true);
    try {
      if (isHr) {
        const response = await apiClient.get('/payroll/payruns', { params: { page_size: 50 } });
        setPayruns(unwrapList(response));
      } else {
        const response = await apiClient.get('/payroll/payslips', { params: { page_size: 50 } });
        setPayslips(unwrapList(response));
      }
      setError('');
    } catch (err: any) {
      setError(err.message || 'Failed to load payroll');
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    load();
  }, [isHr]);

  const formatCurrency = (val: number | null) =>
    val !== null && val !== undefined ? new Intl.NumberFormat('en-IN', { style: 'currency', currency: 'INR' }).format(val) : '—';

  async function createPayrun() {
    setError('');
    setSaving(true);
    try {
      await apiClient.post('/payroll/payruns', form);
      setOpen(false);
      setForm({ period_start: '', period_end: '', include: 'sample' });
      await load();
    } catch (err: any) {
      setError(err.message);
    } finally {
      setSaving(false);
    }
  }

  async function runAction(id: string, action: string) {
    setError('');
    try {
      await apiClient.post(`/payroll/payruns/${id}/${action}`, {});
      load();
    } catch (err: any) {
      setError(err.message);
    }
  }

  async function viewDetails(id: string) {
    const res = await apiClient.get(`/payroll/payruns/${id}`);
    setDetail(unwrapData(res));
  }

  async function viewPayslip(id: string) {
    const res = await apiClient.get(`/payroll/payslips/${id}`);
    setPayslipDetail(unwrapData(res));
  }

  async function downloadPdf(id: string, number?: string) {
    try {
      await downloadPayslipPdf(id, `${number || 'payslip'}.pdf`);
    } catch (err: any) {
      setError(err.message);
    }
  }

  const filteredRuns = payruns.filter((pr) =>
    `${pr.run_number || ''} ${pr.name || ''} ${pr.status || ''}`.toLowerCase().includes(search.toLowerCase())
  );

  return (
    <div className={styles.container}>
      <div className={styles.header}>
        <div>
          <h1 className={styles.title}>{isHr ? 'Payroll Management' : 'My Payslips'}</h1>
          <p className={styles.subtitle}>{isHr ? 'Execute payroll, review payslips, and manage disbursals.' : 'Your payslips stored in peoplepay360.'}</p>
        </div>
        {isHr && (
          <div className={styles.actions}>
            <Button leftIcon={<Plus size={18} />} onClick={() => setOpen(true)}>New Payrun</Button>
          </div>
        )}
      </div>
      {error && <p className="formError">{error}</p>}

      <Card className={styles.tableCard}>
        <div className={styles.toolbar}>
          <div className={styles.searchBar}>
            <Search size={18} className={styles.searchIcon} />
            <input type="text" placeholder={isHr ? 'Search payruns...' : 'Search payslips...'} className={styles.searchInput} value={search} onChange={(e) => setSearch(e.target.value)} />
          </div>
          <Button variant="outline" leftIcon={<Filter size={18} />} onClick={load}>Refresh</Button>
        </div>

        <div className={styles.tableWrapper}>
          {isHr ? (
            <table className={styles.table}>
              <thead>
                <tr>
                  <th>Run Number</th>
                  <th>Period</th>
                  <th>Status</th>
                  <th>Employees</th>
                  <th>Total Net</th>
                  <th className={styles.actionsCell}>Actions</th>
                </tr>
              </thead>
              <tbody>
                {loading ? (
                  <tr><td colSpan={6} className={styles.loadingCell}>Loading payroll runs...</td></tr>
                ) : filteredRuns.length === 0 ? (
                  <tr><td colSpan={6} className={styles.emptyCell}>No payruns found.</td></tr>
                ) : filteredRuns.map(pr => (
                  <tr key={pr.id}>
                    <td>
                      <p className={styles.prName}>{pr.name || pr.run_number}</p>
                      <span className={styles.prCode}>{pr.run_number}</span>
                    </td>
                    <td>
                      {pr.period_start} – {pr.period_end}
                    </td>
                    <td>
                      <Badge variant={
                        pr.status === 'PAID' ? 'success' :
                        pr.status === 'VALIDATED' ? 'primary' :
                        pr.status === 'COMPUTED' ? 'warning' : 'default'
                      }>
                        {pr.status}
                      </Badge>
                    </td>
                    <td>{pr.total_employees || pr.employee_count || 0}</td>
                    <td className={styles.currency}>{formatCurrency(pr.total_net)}</td>
                    <td className={styles.actionsCell}>
                      <div className={styles.actionButtons}>
                        {pr.status === 'DRAFT' && (
                          <Button size="sm" variant="outline" leftIcon={<PlayCircle size={14} />} onClick={() => runAction(pr.id, 'compute')}>Compute</Button>
                        )}
                        {pr.status === 'COMPUTED' && (
                          <Button size="sm" variant="primary" leftIcon={<CheckCircle size={14} />} onClick={() => runAction(pr.id, 'validate')}>Validate</Button>
                        )}
                        {pr.status === 'VALIDATED' && (
                          <Button size="sm" variant="primary" leftIcon={<CheckCircle size={14} />} onClick={() => runAction(pr.id, 'pay')}>Pay Now</Button>
                        )}
                        <button className={styles.iconButton} title="View Details" onClick={() => viewDetails(pr.id)}>
                          <FileText size={16} />
                        </button>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          ) : (
            <table className={styles.table}>
              <thead>
                <tr>
                  <th>Payslip</th>
                  <th>Period</th>
                  <th>Gross</th>
                  <th>Net</th>
                  <th>Status</th>
                  <th className={styles.actionsCell}>Actions</th>
                </tr>
              </thead>
              <tbody>
                {loading ? (
                  <tr><td colSpan={6} className={styles.loadingCell}>Loading payslips...</td></tr>
                ) : payslips.length === 0 ? (
                  <tr><td colSpan={6} className={styles.emptyCell}>No payslips found.</td></tr>
                ) : payslips.filter((p) => `${p.payslip_number || ''} ${p.period_start || ''}`.toLowerCase().includes(search.toLowerCase())).map((p) => (
                  <tr key={p.id}>
                    <td>{p.payslip_number || p.id.slice(0, 8)}</td>
                    <td>{p.period_start} – {p.period_end}</td>
                    <td className={styles.currency}>{formatCurrency(p.gross ?? p.gross_salary)}</td>
                    <td className={styles.currency}>{formatCurrency(p.net ?? p.net_salary)}</td>
                    <td><Badge variant={p.status === 'PAID' ? 'success' : p.status === 'CALCULATED' || p.status === 'VALIDATED' ? 'warning' : 'default'}>{p.status}</Badge></td>
                    <td className={styles.actionsCell}>
                      <div className={styles.actionButtons}>
                        <button className={styles.iconButton} title="View" onClick={() => viewPayslip(p.id)}><FileText size={16} /></button>
                        <button className={styles.iconButton} title="Download PDF" onClick={() => downloadPdf(p.id, p.payslip_number)}><Download size={16} /></button>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </div>
      </Card>

      {open && (
        <Modal title="New payrun" onClose={() => !saving && setOpen(false)} footer={<><Button variant="outline" onClick={() => setOpen(false)} disabled={saving}>Cancel</Button><Button onClick={createPayrun} disabled={saving}>{saving ? 'Creating…' : 'Create draft'}</Button></>}>
          <div><label className="formLabel">Period start</label><input className="formInput" type="date" value={form.period_start} onChange={(e) => setForm({ ...form, period_start: e.target.value })} /></div>
          <div><label className="formLabel">Period end</label><input className="formInput" type="date" value={form.period_end} onChange={(e) => setForm({ ...form, period_end: e.target.value })} /></div>
          <div>
            <label className="formLabel">Employees</label>
            <select className="formInput" value={form.include} onChange={(e) => setForm({ ...form, include: e.target.value })}>
              <option value="sample">Sample of 5 people with attendance (recommended)</option>
              <option value="attendance">Everyone with attendance in this period</option>
              <option value="all">All active employees</option>
            </select>
          </div>
          {error && <p className="formError">{error}</p>}
        </Modal>
      )}

      {detail && (
        <Modal title={`Payrun ${detail.run_number}`} onClose={() => setDetail(null)} footer={<Button onClick={() => setDetail(null)}>Close</Button>}>
          <p><strong>Status:</strong> {detail.status}</p>
          <p><strong>Period:</strong> {detail.period_start} – {detail.period_end}</p>
          <p><strong>Employees:</strong> {detail.employee_count || detail.total_employees || 0}</p>
          <p><strong>Total net:</strong> {formatCurrency(detail.total_net)}</p>
          {(detail.warnings || []).length > 0 && <p><strong>Warnings:</strong> {detail.warnings.length}</p>}
          <div style={{ marginTop: '1rem', display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
            {(detail.payslips || []).map((p: any) => (
              <div key={p.id} style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', gap: '0.75rem' }}>
                <span>{p.employee?.first_name} {p.employee?.last_name} — {formatCurrency(p.net ?? p.net_salary)}</span>
                <div style={{ display: 'flex', gap: '0.5rem' }}>
                  <Button size="sm" variant="outline" onClick={() => viewPayslip(p.id)}>Lines</Button>
                  <Button size="sm" variant="outline" onClick={() => downloadPdf(p.id, p.payslip_number)}>PDF</Button>
                </div>
              </div>
            ))}
          </div>
        </Modal>
      )}

      {payslipDetail && (
        <Modal title={`Payslip ${payslipDetail.payslip_number || ''}`} onClose={() => setPayslipDetail(null)} footer={<><Button variant="outline" onClick={() => downloadPdf(payslipDetail.id, payslipDetail.payslip_number)}>Download PDF</Button><Button onClick={() => setPayslipDetail(null)}>Close</Button></>}>
          <p><strong>Employee:</strong> {payslipDetail.employee?.first_name} {payslipDetail.employee?.last_name}</p>
          <p><strong>Period:</strong> {payslipDetail.period_start} – {payslipDetail.period_end}</p>
          <p><strong>Gross:</strong> {formatCurrency(payslipDetail.gross ?? payslipDetail.gross_salary)}</p>
          <p><strong>Deductions:</strong> {formatCurrency(payslipDetail.total_deductions)}</p>
          <p><strong>Net:</strong> {formatCurrency(payslipDetail.net ?? payslipDetail.net_salary)}</p>
          <div style={{ marginTop: '1rem' }}>
            {(payslipDetail.lines || []).map((line: any) => (
              <p key={line.id}>{line.rule_name || line.rule_code}: {formatCurrency(line.amount ?? line.computed_amount)}</p>
            ))}
          </div>
        </Modal>
      )}
    </div>
  );
}
