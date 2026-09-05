"""
PayrollContext — assembles all inputs needed for payroll calculation.
Maps to the PayrollContext concept in the database schema.
"""
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any
from datetime import date


@dataclass
class PayrollContext:
    # Core entities
    employee: Dict[str, Any]
    contract: Dict[str, Any]
    schedule: Dict[str, Any]
    schedule_days: List[Dict[str, Any]]
    salary_structure: Dict[str, Any]
    salary_rule_versions: List[Dict[str, Any]]  # sorted by sequence

    # Period
    period_start: date
    period_end: date

    # Attendance data
    attendance_records: List[Dict[str, Any]] = field(default_factory=list)

    # Leave data
    approved_leave_requests: List[Dict[str, Any]] = field(default_factory=list)
    leave_types: Dict[str, Dict[str, Any]] = field(default_factory=dict)  # id -> type

    # Derived (computed before rule execution)
    total_working_days: int = 0
    worked_days: float = 0.0
    paid_leave_days: float = 0.0
    unpaid_leave_days: float = 0.0
    overtime_hours: float = 0.0
    contract_wage: float = 0.0

    # Accumulated values (updated during rule execution)
    computed_values: Dict[str, float] = field(default_factory=dict)
