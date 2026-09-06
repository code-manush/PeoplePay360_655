import React from 'react';
import styles from './PayslipPrintTemplate.module.css';
import { numberToWords } from '../../utils/currencyUtils';

interface PayslipPrintTemplateProps {
  payslip: any;
  payrun: any;
  employee: any;
}

const PayslipPrintTemplate: React.FC<PayslipPrintTemplateProps> = ({ payslip, payrun, employee }) => {
  if (!payslip || !employee) return null;

  const earnings = payslip.components?.filter((c: any) => c.type === 'EARNING') || [];
  const deductions = payslip.components?.filter((c: any) => c.type === 'DEDUCTION') || [];
  
  const formatCur = (val: number) => 
    new Intl.NumberFormat('en-IN', { style: 'currency', currency: 'INR' }).format(val);

  const getMonthYear = (dateStr: string) => {
    if (!dateStr) return '';
    return new Date(dateStr).toLocaleDateString('en-US', { month: 'long', year: 'numeric' });
  };

  const formatDate = (dateStr: string) => {
    if (!dateStr) return '';
    return new Date(dateStr).toLocaleDateString('en-IN');
  };

  const totalEarnings = earnings.reduce((acc: number, c: any) => acc + (c.amount || 0), 0);
  const totalDeductions = deductions.reduce((acc: number, c: any) => acc + (c.amount || 0), 0);

  return (
    <div className={styles.printContainer}>
      <div className={styles.header}>
        <div className={styles.companyInfo}>
          <div className={styles.logoRow}>
            <div className={styles.logoShapes}>
              <div className={styles.shape1}></div>
              <div className={styles.shape2}></div>
              <div className={styles.shape3}></div>
            </div>
            <div className={styles.companyTitle}>
              <h2>ODOO</h2>
              <p>Kerala India</p>
            </div>
          </div>
        </div>
        <div className={styles.payPeriodInfo}>
          <p>Payslip For the Month</p>
          <h3>{getMonthYear(payrun?.period_start)}</h3>
        </div>
      </div>
      <div className={styles.divider}></div>

      <div className={styles.summarySection}>
        <div className={styles.empDetails}>
          <h4 className={styles.sectionTitle}>EMPLOYEE SUMMARY</h4>
          <table className={styles.detailsTable}>
            <tbody>
              <tr><td>Employee Name</td><td>:</td><td className={styles.bold}>{employee.first_name} {employee.last_name}</td></tr>
              <tr><td>Designation</td><td>:</td><td className={styles.bold}>{employee.job_title || 'Employee'}</td></tr>
              <tr><td>Employee ID</td><td>:</td><td className={styles.bold}>{employee.employee_code || employee.id.split('-')[0]}</td></tr>
              <tr><td>Date of Joining</td><td>:</td><td className={styles.bold}>{formatDate(employee.created_at)}</td></tr>
              <tr><td>Pay Period</td><td>:</td><td className={styles.bold}>{getMonthYear(payrun?.period_start)}</td></tr>
              <tr><td>Pay Date</td><td>:</td><td className={styles.bold}>{formatDate(payrun?.created_at)}</td></tr>
            </tbody>
          </table>
        </div>
        <div className={styles.netPayCard}>
          <div className={styles.netPayTop}>
            <div className={styles.netPayAmount}>{formatCur(payslip.net_salary)}</div>
            <div className={styles.netPayLabel}>Employee Net Pay</div>
          </div>
          <div className={styles.netPayDivider}></div>
          <div className={styles.netPayBottom}>
            <div className={styles.payDays}>
              <span>Paid Days</span><span>:</span><span className={styles.bold}>30</span>
            </div>
            <div className={styles.payDays}>
              <span>LOP Days</span><span>:</span><span className={styles.bold}>0</span>
            </div>
          </div>
        </div>
      </div>

      <div className={styles.pfSection}>
        <div className={styles.pfItem}>
          <span>PF A/C Number</span><span>:</span><span className={styles.bold}>AA/AAA/9999999/99G/9899999</span>
        </div>
        <div className={styles.pfItem}>
          <span>UAN</span><span>:</span><span className={styles.bold}>111111111111</span>
        </div>
      </div>

      <div className={styles.componentsSection}>
        <div className={styles.componentsGrid}>
          <div className={styles.column}>
            <table className={styles.compTable}>
              <thead>
                <tr>
                  <th>EARNINGS</th>
                  <th className={styles.right}>AMOUNT</th>
                </tr>
              </thead>
              <tbody>
                {earnings.map((e: any) => (
                  <tr key={e.id}>
                    <td>{e.name}</td>
                    <td className={`${styles.right} ${styles.bold}`}>{formatCur(e.amount)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          <div className={styles.column}>
            <table className={styles.compTable}>
              <thead>
                <tr>
                  <th>DEDUCTIONS</th>
                  <th className={styles.right}>AMOUNT</th>
                </tr>
              </thead>
              <tbody>
                {deductions.map((d: any) => (
                  <tr key={d.id}>
                    <td>{d.name}</td>
                    <td className={`${styles.right} ${styles.bold}`}>{formatCur(d.amount)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
        <div className={styles.totalsRow}>
          <div className={styles.totalCol}>
            <span>Gross Earnings</span>
            <span className={styles.bold}>{formatCur(totalEarnings)}</span>
          </div>
          <div className={styles.totalCol}>
            <span>Total Deductions</span>
            <span className={styles.bold}>{formatCur(totalDeductions)}</span>
          </div>
        </div>
      </div>

      <div className={styles.netPayableSection}>
        <div>
          <h4 className={styles.netPayableTitle}>TOTAL NET PAYABLE</h4>
          <p className={styles.netPayableSub}>Gross Earnings - Total Deductions</p>
        </div>
        <div className={styles.netPayableAmount}>{formatCur(payslip.net_salary)}</div>
      </div>
      
      <div className={styles.amountInWords}>
        Amount In Words : <span className={styles.bold}>Indian Rupee {numberToWords(payslip.net_salary)} Only</span>
      </div>

      <div className={styles.footerNote}>
        -- This document has been automatically generated by Odoo Payroll; therefore, a signature is not required. --
      </div>
    </div>
  );
};

export default PayslipPrintTemplate;
