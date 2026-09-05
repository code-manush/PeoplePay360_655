"""
Payroll validators — checks that run before/after payroll computation.
Generates PayrollWarning records.
"""
from typing import List, Dict, Any
from datetime import date, datetime, timezone


DEDUCTION_CATEGORIES = {"DEDUCTION"}
CONTRIBUTION_CATEGORIES = {"CONTRIBUTION"}
GROSS_CATEGORIES = {"GROSS"}
NET_CATEGORIES = {"NET"}


def validate_pre_compute(
    employee: Dict,
    contract: Dict,
    bank_account: Any,
    existing_payslips: List[Dict],
    period_start: str,
    period_end: str,
) -> List[Dict]:
    """
    Pre-computation validation. Returns list of warning dicts.
    """
    warnings = []
    emp_id = employee["id"]
    emp_name = f"{employee['first_name']} {employee['last_name']} ({employee['employee_code']})"

    # Missing bank details
    if not bank_account:
        warnings.append({
            "code": "MISSING_BANK_DETAILS",
            "severity": "WARNING",
            "message": f"{emp_name} does not have verified bank details. Payment cannot be processed.",
            "employee_id": emp_id,
            "payrun_id": None,
            "payslip_id": None,
            "is_resolved": False,
            "resolved_by": None,
            "resolved_at": None,
        })

    # Duplicate payslip check
    for ps in existing_payslips:
        if (ps["employee_id"] == emp_id and
                ps["period_start"] == period_start and
                ps["period_end"] == period_end and
                ps["status"] not in ("CANCELLED",)):
            warnings.append({
                "code": "DUPLICATE_PAYSLIP",
                "severity": "ERROR",
                "message": f"A payslip already exists for {emp_name} for period {period_start} to {period_end}.",
                "employee_id": emp_id,
                "payrun_id": None,
                "payslip_id": ps["id"],
                "is_resolved": False,
                "resolved_by": None,
                "resolved_at": None,
            })

    # Contract expiry warning
    if contract:
        end_date_str = contract.get("end_date")
        if end_date_str:
            end_date = date.fromisoformat(end_date_str)
            today = date.today()
            days_remaining = (end_date - today).days
            if days_remaining <= 90:
                severity = "BLOCKER" if days_remaining <= 7 else ("ERROR" if days_remaining <= 30 else "WARNING")
                warnings.append({
                    "code": "CONTRACT_EXPIRING",
                    "severity": severity,
                    "message": f"Contract for {emp_name} expires on {end_date_str}. {days_remaining} days remaining.",
                    "employee_id": emp_id,
                    "payrun_id": None,
                    "payslip_id": None,
                    "is_resolved": False,
                    "resolved_by": None,
                    "resolved_at": None,
                })

    return warnings


def validate_post_compute(payslip: Dict) -> List[Dict]:
    """Post-computation validation of payslip values."""
    warnings = []
    emp_id = payslip.get("employee_id", "")

    # Net salary check
    if payslip.get("net", 0) < 0:
        warnings.append({
            "code": "PAYROLL_CALCULATION_ERROR",
            "severity": "ERROR",
            "message": f"Negative net salary computed for employee {emp_id}. Please review salary rules.",
            "employee_id": emp_id,
            "payrun_id": payslip.get("payrun_id"),
            "payslip_id": payslip.get("id"),
            "is_resolved": False,
            "resolved_by": None,
            "resolved_at": None,
        })

    return warnings
