import React from 'react';
import styles from './ContractPrintTemplate.module.css';

interface ContractPrintTemplateProps {
  contract: any;
  employee: any;
}

const ContractPrintTemplate: React.FC<ContractPrintTemplateProps> = ({ contract, employee }) => {
  if (!contract || !employee) return null;

  const formatDate = (dateStr: string) => {
    if (!dateStr) return '__________________';
    return new Date(dateStr).toLocaleDateString('en-US', { year: 'numeric', month: 'long', day: 'numeric' });
  };

  const formatCur = (val: number) => {
    if (val === null || val === undefined) return '__________________';
    return new Intl.NumberFormat('en-IN', { style: 'currency', currency: 'INR' }).format(val);
  };

  return (
    <div className={styles.printContainer}>
      <h1 className={styles.mainTitle}>EMPLOYMENT CONTRACT</h1>
      <hr className={styles.titleLine} />
      
      <p className={styles.introText}>
        This Employment Contract Agreement ("Agreement") is made and entered into as of 
        <strong className={styles.dateVal}> {formatDate(contract.start_date)}</strong>,
      </p>

      <div className={styles.partyBlock}>
        <div className={styles.partyRow}>
          <div className={styles.partyLabel}><strong>BY AND<br/>BETWEEN:</strong></div>
          <div className={styles.partyContent}>
            <p><strong>Employer:</strong> <span className={styles.valLine}>ODOO</span>, a corporation with its principal place of business at</p>
            <p className={styles.valLine}>Kerala India ("Employer");</p>
          </div>
        </div>

        <div className={styles.partyRow}>
          <div className={styles.partyLabel}><strong>AND:</strong></div>
          <div className={styles.partyContent}>
            <p><strong>Employee:</strong> <span className={styles.valLine}>{employee.first_name} {employee.last_name}</span>, residing at</p>
            <p className={styles.valLine}>{employee.address || '___________________________'} ("Employee").</p>
          </div>
        </div>
      </div>

      <div className={styles.section}>
        <h3 className={styles.sectionTitle}>1. Employment Position & Duties</h3>
        <p>
          The employer agrees to hire the Employee in the position of <strong>{contract.contract_type || employee.job_title || '__________________'}</strong>. 
          The employee shall perform all duties and responsibilities customarily associated with this position and as directed by the Employer.
        </p>
      </div>

      <div className={styles.section}>
        <h3 className={styles.sectionTitle}>2. Term of Employment</h3>
        <p>
          This Agreement shall commence on <strong>{formatDate(contract.start_date)}</strong> and continue unless terminated in accordance with this Agreement.
        </p>
      </div>

      <div className={styles.section}>
        <h3 className={styles.sectionTitle}>3. Compensation & Benefits</h3>
        <ul>
          <li><strong>Salary:</strong> Employee shall receive a salary of <strong>{formatCur(contract.basic_salary)}</strong> per month payable in accordance with Employer's standard payroll schedule.</li>
          <li><strong>Benefits:</strong> As per the employer's policies, employees may be eligible for benefits, including, but not limited to, health insurance, paid time off, and retirement plans.</li>
        </ul>
      </div>

      <div className={styles.section}>
        <h3 className={styles.sectionTitle}>4. Work Schedule & Location</h3>
        <p>
          Employee shall work from the designated office at <strong>Kerala India</strong>, with standard work hours of <strong>{contract.working_hours_per_week || '40'} hours per week</strong>.
        </p>
      </div>

      <div className={styles.section}>
        <h3 className={styles.sectionTitle}>5. Confidentiality & Non-Disclosure</h3>
        <p>
          Employee agrees to maintain the confidentiality of Employer's proprietary information and not disclose or use such information for any purpose other than Employer's business.
        </p>
      </div>

      <div className={styles.section}>
        <h3 className={styles.sectionTitle}>6. Non-Compete & Non-Solicitation</h3>
        <p>
          For a period of two (2) years following termination of employment, Employee agrees not to engage in direct competition with Employer or solicit Employer's clients or employees.
        </p>
      </div>
      
    </div>
  );
};

export default ContractPrintTemplate;
