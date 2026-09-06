from sqlalchemy import Column, String, Boolean, Float, Text, Integer, Date, DateTime, Time, Numeric, FetchedValue
from sqlalchemy.dialects.postgresql import UUID, JSONB
from app.core.database import Base


class User(Base):
    __tablename__ = "users"
    __table_args__ = {"schema": "identity"}
    id = Column(UUID(as_uuid=False), primary_key=True)
    email = Column(String, unique=True, nullable=False)
    password_hash = Column(Text, nullable=False)
    status = Column(String, nullable=False)
    last_login_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=True)
    updated_at = Column(DateTime(timezone=True), nullable=True)


class Role(Base):
    __tablename__ = "roles"
    __table_args__ = {"schema": "identity"}
    id = Column(UUID(as_uuid=False), primary_key=True)
    name = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=True)


class UserRole(Base):
    __tablename__ = "user_roles"
    __table_args__ = {"schema": "identity"}
    user_id = Column(UUID(as_uuid=False), primary_key=True)
    role_id = Column(UUID(as_uuid=False), primary_key=True)
    assigned_at = Column(DateTime(timezone=True), nullable=True)


class Department(Base):
    __tablename__ = "departments"
    __table_args__ = {"schema": "organization"}
    id = Column(UUID(as_uuid=False), primary_key=True)
    name = Column(String, nullable=False)
    code = Column(String, nullable=False)
    manager_employee_id = Column(UUID(as_uuid=False), nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=True)
    updated_at = Column(DateTime(timezone=True), nullable=True)


class JobPosition(Base):
    __tablename__ = "job_positions"
    __table_args__ = {"schema": "organization"}
    id = Column(UUID(as_uuid=False), primary_key=True)
    name = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    department_id = Column(UUID(as_uuid=False), nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=True)
    updated_at = Column(DateTime(timezone=True), nullable=True)


class Employee(Base):
    __tablename__ = "employees"
    __table_args__ = {"schema": "hr"}
    id = Column(UUID(as_uuid=False), primary_key=True)
    user_id = Column(UUID(as_uuid=False), nullable=True)
    employee_code = Column(String, unique=True)
    first_name = Column(String, nullable=False)
    last_name = Column(String, nullable=False)
    email = Column(String, nullable=False)
    phone = Column(String, nullable=True)
    date_of_birth = Column(Date, nullable=True)
    joining_date = Column(Date, nullable=True)
    leaving_date = Column(Date, nullable=True)
    department_id = Column(UUID(as_uuid=False), nullable=True)
    job_position_id = Column(UUID(as_uuid=False), nullable=True)
    manager_id = Column(UUID(as_uuid=False), nullable=True)
    employment_type = Column(String, nullable=True)
    status = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=True)
    updated_at = Column(DateTime(timezone=True), nullable=True)


class Contract(Base):
    __tablename__ = "contracts"
    __table_args__ = {"schema": "hr"}
    id = Column(UUID(as_uuid=False), primary_key=True)
    employee_id = Column(UUID(as_uuid=False), nullable=False)
    contract_number = Column(String, nullable=False)
    contract_type = Column(String, nullable=True)
    start_date = Column(Date, nullable=False)
    end_date = Column(Date, nullable=True)
    basic_salary = Column(Numeric(14, 2), nullable=True)
    salary_structure_id = Column(UUID(as_uuid=False), nullable=True)
    working_hours_per_week = Column(Numeric(6, 2), nullable=True)
    status = Column(String, nullable=False)
    termination_reason = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=True)
    updated_at = Column(DateTime(timezone=True), nullable=True)


class Notification(Base):
    __tablename__ = "notifications"
    __table_args__ = {"schema": "hr"}
    id = Column(UUID(as_uuid=False), primary_key=True)
    title = Column(String, nullable=False)
    message = Column(Text, nullable=False)
    type = Column(String, nullable=True)
    priority = Column(String, nullable=True)
    target_type = Column(String, nullable=False)
    target_id = Column(UUID(as_uuid=False), nullable=True)
    created_by = Column(UUID(as_uuid=False), nullable=True)
    published_at = Column(DateTime(timezone=True), nullable=True)
    expires_at = Column(DateTime(timezone=True), nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), nullable=True)


class NotificationRead(Base):
    __tablename__ = "notification_reads"
    __table_args__ = {"schema": "hr"}
    notification_id = Column(UUID(as_uuid=False), primary_key=True)
    employee_id = Column(UUID(as_uuid=False), primary_key=True)
    read_at = Column(DateTime(timezone=True), nullable=True)


class AttendanceRecord(Base):
    __tablename__ = "attendance_records"
    __table_args__ = {"schema": "attendance"}
    id = Column(UUID(as_uuid=False), primary_key=True)
    employee_id = Column(UUID(as_uuid=False), nullable=False)
    attendance_date = Column(Date, nullable=False)
    check_in = Column(DateTime(timezone=True), nullable=True)
    check_out = Column(DateTime(timezone=True), nullable=True)
    scheduled_hours = Column(Numeric(6, 2), nullable=True)
    worked_hours = Column(Numeric(6, 2), nullable=True)
    overtime_hours = Column(Numeric(6, 2), nullable=True)
    status = Column(String, nullable=False)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=True)
    updated_at = Column(DateTime(timezone=True), nullable=True)


class Schedule(Base):
    __tablename__ = "schedules"
    __table_args__ = {"schema": "attendance"}
    id = Column(UUID(as_uuid=False), primary_key=True)
    name = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    monday_start = Column(Time, nullable=True)
    monday_end = Column(Time, nullable=True)
    tuesday_start = Column(Time, nullable=True)
    tuesday_end = Column(Time, nullable=True)
    wednesday_start = Column(Time, nullable=True)
    wednesday_end = Column(Time, nullable=True)
    thursday_start = Column(Time, nullable=True)
    thursday_end = Column(Time, nullable=True)
    friday_start = Column(Time, nullable=True)
    friday_end = Column(Time, nullable=True)
    saturday_start = Column(Time, nullable=True)
    saturday_end = Column(Time, nullable=True)
    sunday_start = Column(Time, nullable=True)
    sunday_end = Column(Time, nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=True)
    updated_at = Column(DateTime(timezone=True), nullable=True)


class EmployeeSchedule(Base):
    __tablename__ = "employee_schedules"
    __table_args__ = {"schema": "attendance"}
    id = Column(UUID(as_uuid=False), primary_key=True)
    employee_id = Column(UUID(as_uuid=False), nullable=False)
    schedule_id = Column(UUID(as_uuid=False), nullable=False)
    effective_from = Column(Date, nullable=False)
    effective_to = Column(Date, nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=True)


class EmploymentHistory(Base):
    __tablename__ = "employment_history"
    __table_args__ = {"schema": "hr"}
    id = Column(UUID(as_uuid=False), primary_key=True)
    employee_id = Column(UUID(as_uuid=False), nullable=False)
    department_id = Column(UUID(as_uuid=False), nullable=True)
    job_position_id = Column(UUID(as_uuid=False), nullable=True)
    manager_id = Column(UUID(as_uuid=False), nullable=True)
    employment_type = Column(String, nullable=True)
    effective_from = Column(Date, nullable=False)
    effective_to = Column(Date, nullable=True)
    reason = Column(String, nullable=True)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=True)


class LeaveType(Base):
    __tablename__ = "leave_types"
    __table_args__ = {"schema": "leave_management"}
    id = Column(UUID(as_uuid=False), primary_key=True)
    name = Column(String, nullable=False)
    code = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    unit = Column(String, nullable=True)
    is_paid = Column(Boolean, default=True)
    requires_approval = Column(Boolean, default=True)
    max_consecutive_days = Column(Numeric(6, 2), nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=True)
    updated_at = Column(DateTime(timezone=True), nullable=True)


class LeaveAllocation(Base):
    __tablename__ = "leave_allocations"
    __table_args__ = {"schema": "leave_management"}
    id = Column(UUID(as_uuid=False), primary_key=True)
    employee_id = Column(UUID(as_uuid=False), nullable=False)
    leave_type_id = Column(UUID(as_uuid=False), nullable=False)
    allocation_period_start = Column(Date, nullable=True)
    allocation_period_end = Column(Date, nullable=True)
    allocated_units = Column(Numeric(10, 2), nullable=False)
    used_units = Column(Numeric(10, 2), default=0)
    remaining_units = Column(Numeric(10, 2), FetchedValue())
    created_at = Column(DateTime(timezone=True), nullable=True)
    updated_at = Column(DateTime(timezone=True), nullable=True)


class LeaveRequest(Base):
    __tablename__ = "leave_requests"
    __table_args__ = {"schema": "leave_management"}
    id = Column(UUID(as_uuid=False), primary_key=True)
    employee_id = Column(UUID(as_uuid=False), nullable=False)
    leave_type_id = Column(UUID(as_uuid=False), nullable=False)
    allocation_id = Column(UUID(as_uuid=False), nullable=True)
    start_date = Column(Date, nullable=False)
    end_date = Column(Date, nullable=False)
    requested_units = Column(Numeric(10, 2), nullable=False)
    reason = Column(Text, nullable=True)
    status = Column(String, nullable=False)
    approved_by = Column(UUID(as_uuid=False), nullable=True)
    approved_at = Column(DateTime(timezone=True), nullable=True)
    rejection_reason = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=True)
    updated_at = Column(DateTime(timezone=True), nullable=True)


class SalaryStructure(Base):
    __tablename__ = "salary_structures"
    __table_args__ = {"schema": "payroll_config"}
    id = Column(UUID(as_uuid=False), primary_key=True)
    name = Column(String, nullable=False)
    code = Column(String, nullable=True)
    description = Column(Text, nullable=True)
    currency = Column(String, nullable=True)
    status = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=True)
    updated_at = Column(DateTime(timezone=True), nullable=True)


class SalaryRule(Base):
    __tablename__ = "salary_rules"
    __table_args__ = {"schema": "payroll_config"}
    id = Column(UUID(as_uuid=False), primary_key=True)
    code = Column(String, nullable=False)
    name = Column(String, nullable=False)
    category = Column(String, nullable=True)
    description = Column(Text, nullable=True)
    version_id = Column(UUID(as_uuid=False), nullable=True)
    is_active = Column(Boolean, default=True)


class SalaryRuleVersion(Base):
    __tablename__ = "salary_rule_versions"
    __table_args__ = {"schema": "payroll_config"}
    id = Column(UUID(as_uuid=False), primary_key=True)
    version_number = Column(Integer, nullable=False)
    effective_from = Column(Date, nullable=False)
    effective_to = Column(Date, nullable=True)
    formula_expression = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), nullable=True)


class SalaryStructureRule(Base):
    __tablename__ = "salary_structure_rules"
    __table_args__ = {"schema": "payroll_config"}
    id = Column(UUID(as_uuid=False), primary_key=True)
    salary_structure_id = Column(UUID(as_uuid=False), nullable=False)
    salary_rule_id = Column(UUID(as_uuid=False), nullable=False)
    sequence = Column(Integer, nullable=False)
    is_mandatory = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), nullable=True)


class Payrun(Base):
    __tablename__ = "payruns"
    __table_args__ = {"schema": "payroll"}
    id = Column(UUID(as_uuid=False), primary_key=True)
    run_number = Column(String, nullable=False)
    period_start = Column(Date, nullable=False)
    period_end = Column(Date, nullable=False)
    payment_date = Column(Date, nullable=True)
    status = Column(String, nullable=False)
    employee_count = Column(Integer, nullable=True)
    total_gross = Column(Numeric(14, 2), nullable=True)
    total_deductions = Column(Numeric(14, 2), nullable=True)
    total_net = Column(Numeric(14, 2), nullable=True)
    created_by = Column(UUID(as_uuid=False), nullable=True)
    started_at = Column(DateTime(timezone=True), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=True)
    updated_at = Column(DateTime(timezone=True), nullable=True)


class PayrunStatusHistory(Base):
    __tablename__ = "payrun_status_history"
    __table_args__ = {"schema": "payroll"}
    id = Column(UUID(as_uuid=False), primary_key=True)
    payrun_id = Column(UUID(as_uuid=False), nullable=False)
    old_status = Column(String, nullable=True)
    new_status = Column(String, nullable=False)
    changed_by = Column(UUID(as_uuid=False), nullable=True)
    reason = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=True)


class PayrunEmployee(Base):
    __tablename__ = "payrun_employees"
    __table_args__ = {"schema": "payroll"}
    id = Column(UUID(as_uuid=False), primary_key=True)
    payrun_id = Column(UUID(as_uuid=False), nullable=False)
    employee_id = Column(UUID(as_uuid=False), nullable=False)
    contract_id = Column(UUID(as_uuid=False), nullable=True)
    calculation_status = Column(String, nullable=True)
    error_message = Column(Text, nullable=True)


class Payslip(Base):
    __tablename__ = "payslips"
    __table_args__ = {"schema": "payroll"}
    id = Column(UUID(as_uuid=False), primary_key=True)
    payrun_id = Column(UUID(as_uuid=False), nullable=True)
    employee_id = Column(UUID(as_uuid=False), nullable=False)
    contract_id = Column(UUID(as_uuid=False), nullable=True)
    payslip_number = Column(String, nullable=True)
    period_start = Column(Date, nullable=False)
    period_end = Column(Date, nullable=False)
    currency = Column(String, nullable=True)
    gross_salary = Column(Numeric(14, 2), nullable=True)
    total_deductions = Column(Numeric(14, 2), nullable=True)
    net_salary = Column(Numeric(14, 2), nullable=True)
    status = Column(String, nullable=False)
    pdf_path = Column(Text, nullable=True)
    generated_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=True)
    updated_at = Column(DateTime(timezone=True), nullable=True)


class PayslipLine(Base):
    __tablename__ = "payslip_lines"
    __table_args__ = {"schema": "payroll"}
    id = Column(UUID(as_uuid=False), primary_key=True)
    payslip_id = Column(UUID(as_uuid=False), nullable=False)
    salary_rule_id = Column(UUID(as_uuid=False), nullable=True)
    rule_code = Column(String, nullable=True)
    rule_name = Column(String, nullable=True)
    category = Column(String, nullable=True)
    sequence = Column(Integer, nullable=True)
    base_amount = Column(Numeric(14, 2), nullable=True)
    rate = Column(Numeric(8, 4), nullable=True)
    amount = Column(Numeric(14, 2), nullable=True)
    calculation_expression = Column(Text, nullable=True)
    explanation = Column(Text, nullable=True)


class PayslipCalculationTrace(Base):
    __tablename__ = "payslip_calculation_trace"
    __table_args__ = {"schema": "payroll"}
    id = Column(UUID(as_uuid=False), primary_key=True)
    payslip_id = Column(UUID(as_uuid=False), nullable=False)
    step_number = Column(Integer, nullable=False)
    rule_id = Column(UUID(as_uuid=False), nullable=True)
    rule_code = Column(String, nullable=False)
    rule_name = Column(String, nullable=True)
    input_snapshot = Column(JSONB, nullable=True)
    base_code = Column(String, nullable=True)
    base_value = Column(Numeric(18, 4), nullable=True)
    rate = Column(Numeric(10, 4), nullable=True)
    expression = Column(Text, nullable=True)
    result = Column(Numeric(18, 2), nullable=False)
    explanation = Column(Text, nullable=True)
    calculated_at = Column(DateTime(timezone=True), nullable=True)


class PayslipDelivery(Base):
    __tablename__ = "payslip_deliveries"
    __table_args__ = {"schema": "payroll"}
    id = Column(UUID(as_uuid=False), primary_key=True)
    payslip_id = Column(UUID(as_uuid=False), nullable=False)
    delivery_method = Column(String, nullable=False)
    recipient = Column(String, nullable=True)
    status = Column(String, nullable=True)
    sent_at = Column(DateTime(timezone=True), nullable=True)
    error_message = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=True)


class PayslipInput(Base):
    __tablename__ = "payslip_inputs"
    __table_args__ = {"schema": "payroll"}
    id = Column(UUID(as_uuid=False), primary_key=True)
    payslip_id = Column(UUID(as_uuid=False), nullable=False)
    input_code = Column(String, nullable=False)
    input_name = Column(String, nullable=False)
    input_type = Column(String, nullable=False)
    numeric_value = Column(Numeric(18, 4), nullable=True)
    text_value = Column(Text, nullable=True)
    boolean_value = Column(Boolean, nullable=True)
    date_value = Column(Date, nullable=True)
    source = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=True)


class PayslipSnapshot(Base):
    __tablename__ = "payslip_snapshots"
    __table_args__ = {"schema": "payroll"}
    id = Column(UUID(as_uuid=False), primary_key=True)
    payslip_id = Column(UUID(as_uuid=False), nullable=False)
    employee_snapshot = Column(JSONB, nullable=False)
    contract_snapshot = Column(JSONB, nullable=False)
    attendance_snapshot = Column(JSONB, nullable=True)
    leave_snapshot = Column(JSONB, nullable=True)
    salary_structure_snapshot = Column(JSONB, nullable=True)
    salary_rules_snapshot = Column(JSONB, nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=True)


class PayslipWorkedDays(Base):
    __tablename__ = "payslip_worked_days"
    __table_args__ = {"schema": "payroll"}
    id = Column(UUID(as_uuid=False), primary_key=True)
    payslip_id = Column(UUID(as_uuid=False), nullable=False)
    category = Column(String, nullable=False)
    number_of_days = Column(Numeric(8, 2), nullable=True)
    number_of_hours = Column(Numeric(10, 2), nullable=True)
    source = Column(String, nullable=True)
    description = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=True)


class PayrollWarning(Base):
    __tablename__ = "payroll_warnings"
    __table_args__ = {"schema": "payroll"}
    id = Column(UUID(as_uuid=False), primary_key=True)
    payrun_id = Column(UUID(as_uuid=False), nullable=True)
    employee_id = Column(UUID(as_uuid=False), nullable=True)
    payslip_id = Column(UUID(as_uuid=False), nullable=True)
    severity = Column(String, nullable=True)
    warning_code = Column(String, nullable=True)
    message = Column(Text, nullable=True)
    is_resolved = Column(Boolean, default=False)
    resolved_by = Column(UUID(as_uuid=False), nullable=True)
    resolved_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=True)


class Payment(Base):
    __tablename__ = "payments"
    __table_args__ = {"schema": "payroll"}
    id = Column(UUID(as_uuid=False), primary_key=True)
    payslip_id = Column(UUID(as_uuid=False), nullable=True)
    payment_reference = Column(String, nullable=True)
    payment_date = Column(Date, nullable=True)
    amount = Column(Numeric(14, 2), nullable=True)
    payment_method = Column(String, nullable=True)
    status = Column(String, nullable=True)
    failure_reason = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=True)
    updated_at = Column(DateTime(timezone=True), nullable=True)


class AuditLog(Base):
    __tablename__ = "audit_logs"
    __table_args__ = {"schema": "audit"}
    id = Column(UUID(as_uuid=False), primary_key=True)
    user_id = Column(UUID(as_uuid=False), nullable=True)
    action = Column(String, nullable=False)
    entity_schema = Column(String, nullable=True)
    entity_table = Column(String, nullable=True)
    entity_id = Column(UUID(as_uuid=False), nullable=True)
    old_values = Column(JSONB, nullable=True)
    new_values = Column(JSONB, nullable=True)
    ip_address = Column(String, nullable=True)
    user_agent = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=True)
