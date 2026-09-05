import React, { useState, useEffect } from 'react';
import styles from './AIAgent.module.css';
import apiClient, { unwrapData } from '../../api/client';
import { Sparkles, BrainCircuit, AlertTriangle, User, Clock, Calendar, Briefcase, CreditCard } from 'lucide-react';

interface Employee {
  id: string;
  first_name: string;
  last_name: string;
  employment_type: string;
}

interface AIReport {
  brief_info: string;
  rating: string;
  recommendation: string;
  remark: string;
  metrics: {
    total_attendance: number;
    late_arrivals: number;
    avg_late_mins: number;
    overtime_count: number;
    avg_overtime_hours: number;
    approved_leaves: number;
    declined_leaves: number;
    contract_salary: string | number;
  }
}

const AIAgent: React.FC = () => {
  const [employees, setEmployees] = useState<Employee[]>([]);
  const [selectedEmp, setSelectedEmp] = useState<string | null>(null);
  const [report, setReport] = useState<AIReport | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const [listLoading, setListLoading] = useState(true);
  const [listError, setListError] = useState<string | null>(null);

  useEffect(() => {
    const fetchEmployees = async () => {
      setListLoading(true);
      setListError(null);
      try {
        const response: any = await apiClient.get('/employees');
        let items: any[] = [];
        if (Array.isArray(response)) items = response;
        else if (Array.isArray(response?.data)) items = response.data;
        else if (Array.isArray(response?.data?.items)) items = response.data.items;
        else if (Array.isArray(response?.items)) items = response.items;
        else items = unwrapData(response)?.items || [];
        setEmployees(items);
      } catch (err: any) {
        console.error('Failed to fetch employees', err);
        setListError(err.message || 'Failed to fetch employees');
      } finally {
        setListLoading(false);
      }
    };
    fetchEmployees();
  }, []);

  const handleSelect = async (empId: string) => {
    setSelectedEmp(empId);
    setReport(null);
    setLoading(true);
    setError(null);
    try {
      const response = await apiClient.get(`/ai/employee-analysis/${empId}`);
      const data = unwrapData(response);
      setReport(data);
    } catch (err: any) {
      setError(err.message || 'An error occurred during analysis');
    } finally {
      setLoading(false);
    }
  };

  const selectedEmpData = employees.find(e => e.id === selectedEmp);

  return (
    <div className={styles.container}>
      <div className={styles.header}>
        <div>
          <h1 className={styles.title} style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
            <BrainCircuit color="var(--brand-primary)" size={28} /> AI Employee Analysis
          </h1>
          <p className={styles.subtitle}>Analyze employee performance and get comprehensive AI-driven insights.</p>
        </div>
      </div>

      <div className={styles.contentWrapper}>
        <div className={styles.selectCard}>
          <h3 className={styles.selectTitle}>Select Employee</h3>
          <div className={styles.employeeList}>
            {listLoading ? (
                <p style={{ fontSize: '0.875rem', color: 'var(--text-muted)' }}>Loading employees...</p>
            ) : listError ? (
                <p style={{ fontSize: '0.875rem', color: 'var(--danger)' }}>{listError}</p>
            ) : employees.length === 0 ? (
                <p style={{ fontSize: '0.875rem', color: 'var(--text-muted)' }}>No employees found.</p>
            ) : null}
            {!listLoading && employees.map(emp => (
              <div 
                key={emp.id}
                className={`${styles.employeeItem} ${selectedEmp === emp.id ? styles.active : ''}`}
                onClick={() => handleSelect(emp.id)}
              >
                <span className={styles.empName}>{emp.first_name} {emp.last_name}</span>
                <span className={styles.empRole}>{emp.employment_type || 'Employee'}</span>
              </div>
            ))}
          </div>
        </div>

        <div className={styles.resultCard}>
          {!selectedEmp && !loading && (
            <div className={styles.emptyState}>
              <BrainCircuit size={64} style={{ opacity: 0.2, color: 'var(--text-secondary)' }} />
              <p>Select an employee from the left to generate an AI performance report.</p>
            </div>
          )}

          {loading && (
            <div className={styles.loader}>
              <div className={styles.spinner}></div>
              <p>Analyzing attendance, leaves, and payroll records...</p>
            </div>
          )}

          {error && !loading && (
            <div className={styles.emptyState}>
              <AlertTriangle size={48} style={{ color: 'var(--danger)', opacity: 0.8 }} />
              <p style={{ color: 'var(--danger)' }}>{error}</p>
            </div>
          )}

          {report && !loading && (
            <div>
              <div className={styles.reportHeader}>
                <div className={styles.reportAvatar}><User size={24} color="var(--brand-primary)" /></div>
                <div>
                  <div className={styles.reportTitle}>{selectedEmpData?.first_name} {selectedEmpData?.last_name}</div>
                  <div style={{ color: 'var(--text-secondary)', fontSize: '0.875rem' }}>AI Performance Report</div>
                </div>
              </div>

              {/* Full Report Details */}
              {report.metrics && (
                <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: '1rem', marginBottom: '2rem' }}>
                  <div style={{ background: 'var(--bg-primary)', padding: '1rem', borderRadius: '8px', border: '1px solid var(--border-color)' }}>
                    <div style={{ color: 'var(--text-secondary)', fontSize: '0.75rem', fontWeight: 600, display: 'flex', alignItems: 'center', gap: '0.375rem', marginBottom: '0.5rem' }}><Clock size={14}/> Attendance</div>
                    <div style={{ fontSize: '1.25rem', fontWeight: 700 }}>{report.metrics.total_attendance} <span style={{fontSize:'0.875rem', fontWeight:500, color:'var(--text-muted)'}}>days</span></div>
                    <div style={{ fontSize: '0.75rem', color: 'var(--text-secondary)', marginTop: '0.25rem' }}>Late: {report.metrics.late_arrivals} times ({report.metrics.avg_late_mins}m avg)</div>
                  </div>
                  
                  <div style={{ background: 'var(--bg-primary)', padding: '1rem', borderRadius: '8px', border: '1px solid var(--border-color)' }}>
                    <div style={{ color: 'var(--text-secondary)', fontSize: '0.75rem', fontWeight: 600, display: 'flex', alignItems: 'center', gap: '0.375rem', marginBottom: '0.5rem' }}><Briefcase size={14}/> Overtime</div>
                    <div style={{ fontSize: '1.25rem', fontWeight: 700 }}>{report.metrics.overtime_count} <span style={{fontSize:'0.875rem', fontWeight:500, color:'var(--text-muted)'}}>times</span></div>
                    <div style={{ fontSize: '0.75rem', color: 'var(--text-secondary)', marginTop: '0.25rem' }}>Avg: {report.metrics.avg_overtime_hours}h</div>
                  </div>
                  
                  <div style={{ background: 'var(--bg-primary)', padding: '1rem', borderRadius: '8px', border: '1px solid var(--border-color)' }}>
                    <div style={{ color: 'var(--text-secondary)', fontSize: '0.75rem', fontWeight: 600, display: 'flex', alignItems: 'center', gap: '0.375rem', marginBottom: '0.5rem' }}><Calendar size={14}/> Leaves</div>
                    <div style={{ fontSize: '1.25rem', fontWeight: 700 }}>{report.metrics.approved_leaves} <span style={{fontSize:'0.875rem', fontWeight:500, color:'var(--text-muted)'}}>approved</span></div>
                    <div style={{ fontSize: '0.75rem', color: 'var(--danger)', marginTop: '0.25rem' }}>{report.metrics.declined_leaves} declined</div>
                  </div>
                  
                  <div style={{ background: 'var(--bg-primary)', padding: '1rem', borderRadius: '8px', border: '1px solid var(--border-color)' }}>
                    <div style={{ color: 'var(--text-secondary)', fontSize: '0.75rem', fontWeight: 600, display: 'flex', alignItems: 'center', gap: '0.375rem', marginBottom: '0.5rem' }}><CreditCard size={14}/> Base Salary</div>
                    <div style={{ fontSize: '1.25rem', fontWeight: 700 }}>{report.metrics.contract_salary}</div>
                  </div>
                </div>
              )}

              <div className={styles.reportSection}>
                <div className={styles.sectionTitle}>Employee Summary</div>
                <div className={styles.infoText}>{report.brief_info}</div>
              </div>

              <div style={{ display: 'flex', gap: '2rem', marginBottom: '1.5rem' }}>
                <div className={styles.reportSection}>
                  <div className={styles.sectionTitle}>Performance Rating</div>
                  <div className={styles.ratingBox}>{report.rating}</div>
                </div>
              </div>

              <div className={styles.recommendationBox}>
                <div className={styles.sectionTitle} style={{ display: 'flex', alignItems: 'center', gap: '0.4rem', color: 'var(--brand-primary)' }}>
                  <Sparkles size={16} /> AI Recommendation
                </div>
                <div className={styles.infoText} style={{ fontWeight: 600, color: 'var(--text-primary)', marginBottom: '0.5rem', fontSize: '1.1rem' }}>
                  {report.recommendation}
                </div>
                <div className={styles.infoText} style={{ fontSize: '0.9375rem', color: 'var(--text-secondary)' }}>
                  {report.remark}
                </div>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default AIAgent;
