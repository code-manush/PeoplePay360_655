"""
Centralized dummy data store — all JSON data loaded into memory at startup.
When integrating Aiven PostgreSQL, replace this module's usage in repositories
with actual database queries.
"""
import json
import os
from typing import Dict, List, Any
from copy import deepcopy

DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "data")


def _load(filename: str) -> List[Dict[str, Any]]:
    path = os.path.join(DATA_DIR, filename)
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


# ─── In-memory stores (mutable copies for runtime CRUD) ───────────────────────
employees: List[Dict] = _load("employees.json")
departments: List[Dict] = _load("departments.json")
job_positions: List[Dict] = _load("job_positions.json")
working_schedules: List[Dict] = _load("working_schedules.json")
working_schedule_days: List[Dict] = _load("working_schedule_days.json")
contracts: List[Dict] = _load("contracts.json")
employee_bank_accounts: List[Dict] = _load("employee_bank_accounts.json")
time_off_types: List[Dict] = _load("time_off_types.json")
leave_allocations: List[Dict] = _load("leave_allocations.json")
leave_requests: List[Dict] = _load("leave_requests.json")
attendance_records: List[Dict] = _load("attendance_records.json")
salary_structures: List[Dict] = _load("salary_structures.json")
salary_rules: List[Dict] = _load("salary_rules.json")
salary_rule_versions: List[Dict] = _load("salary_rule_versions.json")
payruns: List[Dict] = _load("payruns.json")
payrun_employees: List[Dict] = _load("payrun_employees.json")
payslips: List[Dict] = _load("payslips.json")
payslip_lines: List[Dict] = _load("payslip_lines.json")
payroll_warnings: List[Dict] = _load("payroll_warnings.json")
payments: List[Dict] = _load("payments.json")
payslip_deliveries: List[Dict] = _load("payslip_deliveries.json")
notifications: List[Dict] = _load("notifications.json")
audit_logs: List[Dict] = _load("audit_logs.json")


def next_id(prefix: str, store: List[Dict]) -> str:
    """Generate next sequential ID for a store."""
    existing = [item["id"] for item in store if item["id"].startswith(prefix + "-")]
    if not existing:
        return f"{prefix}-001"
    nums = []
    for eid in existing:
        try:
            nums.append(int(eid.split("-")[-1]))
        except ValueError:
            pass
    return f"{prefix}-{max(nums) + 1:03d}"
