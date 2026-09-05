"""
Payroll Engine — orchestrates payrun computation.
Coordinates data assembly → calculation → validation → persistence.
"""
from typing import Dict, List, Any, Tuple
from datetime import date

from app.payroll.context import PayrollContext
from app.payroll.calculator import calculate_payslip
from app.payroll.validators import validate_pre_compute, validate_post_compute
from app.payroll.trace import CalculationTrace


class PayrollEngine:
    """
    Orchestrates payroll calculation for a payrun.

    FUTURE INTEGRATION:
    - AI insights can hook into the result of compute() to generate recommendations.
    - WiFi validation was intentionally not placed here — it's at the attendance layer.
    """

    def __init__(self, payroll_repo, employee_repo, contract_repo, schedule_repo,
                 attendance_repo, leave_repo, bank_repo):
        self.payroll_repo = payroll_repo
        self.employee_repo = employee_repo
        self.contract_repo = contract_repo
        self.schedule_repo = schedule_repo
        self.attendance_repo = attendance_repo
        self.leave_repo = leave_repo
        self.bank_repo = bank_repo

    def compute_payrun(self, payrun: Dict, period_start: date, period_end: date) -> Dict:
        """
        Compute all payslips for a payrun.
        Returns summary with warnings.
        """
        payrun_id = payrun["id"]
        structure_id = payrun["salary_structure_id"]

        # Load salary structure & rule versions (joined with rule metadata)
        structure = self.payroll_repo.find_structure_by_id(structure_id)
        raw_versions = self.payroll_repo.find_rule_versions(structure_id)

        # Enrich versions with rule metadata
        all_rules = {r["id"]: r for r in self.payroll_repo.find_rules()}
        versions = []
        for rv in raw_versions:
            rule = all_rules.get(rv["rule_id"], {})
            enriched = {**rv, **{
                "rule_code": rule.get("code", ""),
                "rule_name": rule.get("name", ""),
                "category": rule.get("category", ""),
                "sequence": rule.get("sequence", 10),
            }}
            versions.append(enriched)
        versions.sort(key=lambda v: v.get("sequence", 0))

        # Load all leave types
        leave_types = {t["id"]: t for t in self.leave_repo.find_types()}

        payrun_emps = self.payroll_repo.find_payrun_employees(payrun_id)
        all_warnings = []
        total_gross = 0.0
        total_deductions = 0.0
        total_net = 0.0
        computed_payslips = []

        for pe in payrun_emps:
            emp_id = pe["employee_id"]
            contract_id = pe["contract_id"]

            employee = self.employee_repo.find_by_id(emp_id)
            contract = self.contract_repo.find_by_id(contract_id)
            if not employee or not contract:
                continue

            schedule = self.schedule_repo.find_by_id(contract.get("schedule_id", ""))
            schedule_days = self.schedule_repo.find_days(contract.get("schedule_id", ""))
            bank_account = self.bank_repo.find_primary(emp_id)

            # Existing payslips for duplicate check
            existing = self.payroll_repo.find_payslips({"employee_id": emp_id})

            # Pre-compute validation
            pre_warns = validate_pre_compute(
                employee, contract, bank_account, existing,
                period_start.isoformat(), period_end.isoformat()
            )
            for w in pre_warns:
                w["payrun_id"] = payrun_id
                created = self.payroll_repo.create_warning(w)
                all_warnings.append(created)

            att_records = self.attendance_repo.find_all({
                "employee_id": emp_id,
                "date_from": period_start.isoformat(),
                "date_to": period_end.isoformat(),
            })

            all_leaves = self.leave_repo.find_requests({
                "employee_id": emp_id,
                "status": "APPROVED",
            })

            ctx = PayrollContext(
                employee=employee,
                contract=contract,
                schedule=schedule or {},
                schedule_days=schedule_days,
                salary_structure=structure,
                salary_rule_versions=versions,
                period_start=period_start,
                period_end=period_end,
                attendance_records=att_records,
                approved_leave_requests=all_leaves,
                leave_types=leave_types,
            )

            payslip_data, trace, lines = calculate_payslip(ctx)
            payslip_data["payrun_id"] = payrun_id

            # Delete existing lines if recomputing
            created_payslip = None
            for ps in existing:
                if (ps["employee_id"] == emp_id and
                        ps["payrun_id"] == payrun_id and
                        ps["period_start"] == period_start.isoformat()):
                    # Update existing
                    self.payroll_repo.delete_payslip_lines(ps["id"])
                    created_payslip = self.payroll_repo.update_payslip(ps["id"], payslip_data)
                    break

            if not created_payslip:
                created_payslip = self.payroll_repo.create_payslip(payslip_data)

            ps_id = created_payslip["id"]
            for line in lines:
                line["payslip_id"] = ps_id
                self.payroll_repo.create_payslip_line(line)

            # Post-compute validation
            post_warns = validate_post_compute(created_payslip)
            for w in post_warns:
                w["payrun_id"] = payrun_id
                created = self.payroll_repo.create_warning(w)
                all_warnings.append(created)

            total_gross += created_payslip.get("gross", 0.0)
            total_deductions += created_payslip.get("total_deductions", 0.0)
            total_net += created_payslip.get("net", 0.0)
            computed_payslips.append(created_payslip)

        return {
            "payslips": computed_payslips,
            "warnings": all_warnings,
            "total_gross": round(total_gross, 2),
            "total_deductions": round(total_deductions, 2),
            "total_net": round(total_net, 2),
        }
