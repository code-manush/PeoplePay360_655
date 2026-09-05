import React, { useEffect, useState } from 'react';
import { Card } from '../../components/ui/Card/Card';
import { Badge } from '../../components/ui/Badge/Badge';
import { Button } from '../../components/ui/Button/Button';
import apiClient, { unwrapList } from '../../api/client';
import styles from './PayrollList.module.css';
import { Plus, Search, Filter, Edit2 } from 'lucide-react';
import Modal from '../../components/ui/Modal/Modal';
import { useAuth } from '../../contexts/AuthContext';

export default function SalaryConfig() {
  const { role } = useAuth();
  const isHr = role === 'HR' || role === 'ADMIN';
  const [activeTab, setActiveTab] = useState<'structures' | 'rules'>('structures');
  
  const [structures, setStructures] = useState<any[]>([]);
  const [rules, setRules] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState('');
  
  const [structureModalOpen, setStructureModalOpen] = useState(false);
  const [ruleModalOpen, setRuleModalOpen] = useState(false);
  
  const [editingStructureId, setEditingStructureId] = useState<string | null>(null);
  const [editingRuleId, setEditingRuleId] = useState<string | null>(null);
  const [error, setError] = useState('');

  const [structureForm, setStructureForm] = useState({ name: '', code: '', description: '', currency: 'INR', status: 'ACTIVE' });
  const [ruleForm, setRuleForm] = useState({ code: '', name: '', category: 'EARNING', calculation_type: 'FIXED', fixed_amount: 0, percentage: 0, base_code: '', formula: '0', description: '', is_active: true });

  const [manageStructureRulesId, setManageStructureRulesId] = useState<string | null>(null);
  const [structureRulesForm, setStructureRulesForm] = useState({ salary_rule_id: '', sequence: 10, is_mandatory: true });

  async function load() {
    setLoading(true);
    try {
      const [strRes, rulRes] = await Promise.all([
        apiClient.get('/payroll/salary-structures'),
        apiClient.get('/payroll-config/salary-rules')
      ]);
      setStructures(unwrapList(strRes));
      setRules(unwrapList(rulRes));
    } catch (err: any) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    if (isHr) load();
  }, [isHr]);

  if (!isHr) return <div className={styles.container}><p>You do not have permission to view this page.</p></div>;

  const filteredStructures = structures.filter(s => `${s.name} ${s.code}`.toLowerCase().includes(search.toLowerCase()));
  const filteredRules = rules.filter(r => `${r.name} ${r.code} ${r.category}`.toLowerCase().includes(search.toLowerCase()));

  // Form submit handlers
  async function saveStructure() {
    setError('');
    try {
      if (editingStructureId) {
        await apiClient.put(`/payroll-config/salary-structures/${editingStructureId}`, structureForm);
      } else {
        await apiClient.post('/payroll-config/salary-structures', structureForm);
      }
      setStructureModalOpen(false);
      load();
    } catch (err: any) {
      setError(err.message);
    }
  }

  async function saveRule() {
    setError('');
    try {
      if (editingRuleId) {
        await apiClient.put(`/payroll-config/salary-rules/${editingRuleId}`, ruleForm);
      } else {
        await apiClient.post('/payroll-config/salary-rules', ruleForm);
      }
      setRuleModalOpen(false);
      load();
    } catch (err: any) {
      setError(err.message);
    }
  }

  async function addRuleToStructure() {
    setError('');
    if (!manageStructureRulesId) return;
    try {
      await apiClient.post(`/payroll-config/salary-structures/${manageStructureRulesId}/rules`, structureRulesForm);
      alert('Rule added successfully');
      setManageStructureRulesId(null);
      load();
    } catch (err: any) {
      setError(err.message);
    }
  }

  return (
    <div className={styles.container}>
      <div className={styles.header}>
        <div>
          <h1 className={styles.title}>Payroll Configuration</h1>
          <p className={styles.subtitle}>Configure Salary Structures and Rules.</p>
        </div>
      </div>
      
      <div style={{ display: 'flex', gap: '1rem', marginBottom: '1rem' }}>
        <Button variant={activeTab === 'structures' ? 'primary' : 'outline'} onClick={() => setActiveTab('structures')}>Salary Structures</Button>
        <Button variant={activeTab === 'rules' ? 'primary' : 'outline'} onClick={() => setActiveTab('rules')}>Salary Rules</Button>
      </div>

      <Card className={styles.tableCard}>
        <div className={styles.toolbar}>
          <div className={styles.searchBar}>
            <Search size={18} className={styles.searchIcon} />
            <input type="text" placeholder={`Search ${activeTab}...`} className={styles.searchInput} value={search} onChange={(e) => setSearch(e.target.value)} />
          </div>
          <Button variant="outline" leftIcon={<Filter size={18} />} onClick={load}>Refresh</Button>
          <Button leftIcon={<Plus size={18} />} onClick={() => {
            if (activeTab === 'structures') {
              setStructureForm({ name: '', code: '', description: '', currency: 'INR', status: 'ACTIVE' });
              setEditingStructureId(null);
              setStructureModalOpen(true);
            } else {
              setRuleForm({ code: '', name: '', category: 'EARNING', calculation_type: 'FIXED', fixed_amount: 0, percentage: 0, base_code: '', formula: '0', description: '', is_active: true });
              setEditingRuleId(null);
              setRuleModalOpen(true);
            }
          }}>New {activeTab === 'structures' ? 'Structure' : 'Rule'}</Button>
        </div>

        <div className={styles.tableWrapper}>
          {activeTab === 'structures' ? (
            <table className={styles.table}>
              <thead>
                <tr>
                  <th>Name</th>
                  <th>Code</th>
                  <th>Status</th>
                  <th>Rules Count</th>
                  <th className={styles.actionsCell}>Actions</th>
                </tr>
              </thead>
              <tbody>
                {loading ? <tr><td colSpan={5}>Loading...</td></tr> : filteredStructures.map(s => (
                  <tr key={s.id}>
                    <td>{s.name}</td>
                    <td><span className={styles.prCode}>{s.code}</span></td>
                    <td><Badge variant={s.status === 'ACTIVE' ? 'success' : 'default'}>{s.status}</Badge></td>
                    <td>{s.rules_count || 0}</td>
                    <td className={styles.actionsCell}>
                      <div className={styles.actionButtons}>
                        <button className={styles.iconButton} onClick={() => { setManageStructureRulesId(s.id); setStructureRulesForm({ ...structureRulesForm, sequence: (s.rules_count || 0) * 10 + 10 }); }}>+ Rule</button>
                        <button className={styles.iconButton} onClick={() => { setEditingStructureId(s.id); setStructureForm(s); setStructureModalOpen(true); }}><Edit2 size={16} /></button>
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
                  <th>Code</th>
                  <th>Name</th>
                  <th>Category</th>
                  <th>Status</th>
                  <th className={styles.actionsCell}>Actions</th>
                </tr>
              </thead>
              <tbody>
                {loading ? <tr><td colSpan={5}>Loading...</td></tr> : filteredRules.map(r => (
                  <tr key={r.id}>
                    <td><span className={styles.prCode}>{r.code}</span></td>
                    <td>{r.name}</td>
                    <td><Badge>{r.category}</Badge></td>
                    <td><Badge variant={r.is_active ? 'success' : 'default'}>{r.is_active ? 'ACTIVE' : 'INACTIVE'}</Badge></td>
                    <td className={styles.actionsCell}>
                      <div className={styles.actionButtons}>
                        <button className={styles.iconButton} onClick={() => { setEditingRuleId(r.id); setRuleForm({...ruleForm, ...r}); setRuleModalOpen(true); }}><Edit2 size={16} /></button>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </div>
      </Card>

      {structureModalOpen && (
        <Modal title={editingStructureId ? 'Edit Structure' : 'New Structure'} onClose={() => setStructureModalOpen(false)} footer={<><Button variant="outline" onClick={() => setStructureModalOpen(false)}>Cancel</Button><Button onClick={saveStructure}>Save</Button></>}>
          <div><label className="formLabel">Name</label><input className="formInput" value={structureForm.name} onChange={e => setStructureForm({...structureForm, name: e.target.value})} /></div>
          <div><label className="formLabel">Code</label><input className="formInput" value={structureForm.code} onChange={e => setStructureForm({...structureForm, code: e.target.value})} /></div>
          <div><label className="formLabel">Description</label><input className="formInput" value={structureForm.description} onChange={e => setStructureForm({...structureForm, description: e.target.value})} /></div>
          <div><label className="formLabel">Status</label><select className="formInput" value={structureForm.status} onChange={e => setStructureForm({...structureForm, status: e.target.value})}><option value="ACTIVE">ACTIVE</option><option value="INACTIVE">INACTIVE</option></select></div>
          {error && <p className="formError">{error}</p>}
        </Modal>
      )}

      {ruleModalOpen && (
        <Modal title={editingRuleId ? 'Edit Rule' : 'New Rule'} onClose={() => setRuleModalOpen(false)} footer={<><Button variant="outline" onClick={() => setRuleModalOpen(false)}>Cancel</Button><Button onClick={saveRule}>Save</Button></>}>
          <div><label className="formLabel">Code (e.g. BASIC)</label><input className="formInput" value={ruleForm.code} onChange={e => setRuleForm({...ruleForm, code: e.target.value})} /></div>
          <div><label className="formLabel">Name</label><input className="formInput" value={ruleForm.name} onChange={e => setRuleForm({...ruleForm, name: e.target.value})} /></div>
          <div><label className="formLabel">Category</label><select className="formInput" value={ruleForm.category} onChange={e => setRuleForm({...ruleForm, category: e.target.value})}><option value="EARNING">EARNING</option><option value="DEDUCTION">DEDUCTION</option><option value="GROSS">GROSS</option><option value="NET">NET</option><option value="COMPANY_CONTRIB">COMPANY_CONTRIB</option></select></div>
          
          <div><label className="formLabel">Calculation Type</label><select className="formInput" value={ruleForm.calculation_type} onChange={e => setRuleForm({...ruleForm, calculation_type: e.target.value})}><option value="FIXED">FIXED</option><option value="PERCENTAGE">PERCENTAGE</option><option value="FORMULA">FORMULA</option></select></div>
          
          {ruleForm.calculation_type === 'FIXED' && <div><label className="formLabel">Fixed Amount</label><input className="formInput" type="number" value={ruleForm.fixed_amount} onChange={e => setRuleForm({...ruleForm, fixed_amount: parseFloat(e.target.value) || 0})} /></div>}
          
          {ruleForm.calculation_type === 'PERCENTAGE' && (
            <>
              <div><label className="formLabel">Base Code (e.g. BASIC)</label><input className="formInput" value={ruleForm.base_code} onChange={e => setRuleForm({...ruleForm, base_code: e.target.value})} /></div>
              <div><label className="formLabel">Percentage</label><input className="formInput" type="number" value={ruleForm.percentage} onChange={e => setRuleForm({...ruleForm, percentage: parseFloat(e.target.value) || 0})} /></div>
            </>
          )}

          {ruleForm.calculation_type === 'FORMULA' && <div><label className="formLabel">Formula Expression</label><input className="formInput" value={ruleForm.formula} onChange={e => setRuleForm({...ruleForm, formula: e.target.value})} /></div>}

          {error && <p className="formError">{error}</p>}
        </Modal>
      )}

      {manageStructureRulesId && (
        <Modal title="Add Rule to Structure" onClose={() => setManageStructureRulesId(null)} footer={<><Button variant="outline" onClick={() => setManageStructureRulesId(null)}>Cancel</Button><Button onClick={addRuleToStructure}>Add</Button></>}>
          <div>
            <label className="formLabel">Rule</label>
            <select className="formInput" value={structureRulesForm.salary_rule_id} onChange={e => setStructureRulesForm({...structureRulesForm, salary_rule_id: e.target.value})}>
              <option value="">Select...</option>
              {rules.map(r => <option key={r.id} value={r.id}>{r.name} ({r.code})</option>)}
            </select>
          </div>
          <div><label className="formLabel">Sequence</label><input className="formInput" type="number" value={structureRulesForm.sequence} onChange={e => setStructureRulesForm({...structureRulesForm, sequence: parseInt(e.target.value) || 0})} /></div>
          {error && <p className="formError">{error}</p>}
        </Modal>
      )}
    </div>
  );
}
