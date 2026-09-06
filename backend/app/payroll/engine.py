"""
Payroll Engine — orchestrates payrun computation.
Coordinates data assembly → calculation → validation → persistence.
"""
from typing import Dict, Any
from datetime import date, datetime, timezone


from app.payroll.context import PayrollContext
from app.payroll.calculator import calculate_payslip
from app.payroll.validators import validate_pre_compute, validate_post_compute


class PayrollEngine:
    def __init__(self, payroll_repo, employee_repo, contract_repo, schedule_repo,
                 attendance_repo, leave_repo, bank_repo=None):
        self.payroll_repo = payroll_repo
        self.employee_repo = employee_repo
        self.contract_repo = contract_repo
        self.schedule_repo = schedule_repo
        self.attendance_repo = attendance_repo
        self.leave_repo = leave_repo
        self.bank_repo = bank_repo

    def _structure_for_contract(self, contract: Dict[str, Any], cache: Dict[str, Any]):
        structure_id = contract.get("salary_structure_id")
        if not structure_id:
            return None, []
        if structure_id in cache:
            return cache[structure_id]
        structure = self.payroll_repo.find_structure_by_id(structure_id)
        raw_versions = self.payroll_repo.find_rule_versions(structure_id)
        all_rules = {r["id"]: r for r in self.payroll_repo.find_rules()}
        versions = []
        for rv in raw_versions:
            rule = all_rules.get(rv["rule_id"], {})
            versions.append({
                **rv,
                "rule_code": rv.get("rule_code") or rule.get("code", ""),
                "rule_name": rv.get("rule_name") or rule.get("name", ""),
                "category": rv.get("category") or rule.get("category", ""),
                "sequence": rv.get("sequence", 10),
                "is_active": rule.get("is_active", True),
            })
        versions.sort(key=lambda v: v.get("sequence", 0))
        cache[structure_id] = (structure, versions)
        return structure, versions

    def compute_payrun(self, payrun: Dict, period_start: date, period_end: date) -> Dict:
        payrun_id = payrun["id"]
        leave_types = {t["id"]: t for t in self.leave_repo.find_types()}
        structure_cache: Dict[str, Any] = {}

        payrun_emps = self.payroll_repo.find_payrun_employees(payrun_id)
        all_warnings = []
        total_gross = 0.0
        total_deductions = 0.0
        total_net = 0.0
        computed_payslips = []

        for pe in payrun_emps:
            emp_id = pe["employee_id"]
            contract_id = pe.get("contract_id")
            employee = self.employee_repo.find_by_id(emp_id)
            contract = self.contract_repo.find_by_id(contract_id) if contract_id else None
            if not employee or not contract:
                self.payroll_repo.update_payrun_employee_status(pe["id"], "ERROR", "Missing employee or contract")
                continue

            structure, versions = self._structure_for_contract(contract, structure_cache)
            if not structure or not versions:
                warning = self.payroll_repo.create_warning({
                    "payrun_id": payrun_id,
                    "employee_id": emp_id,
                    "warning_code": "MISSING_SALARY_STRUCTURE",
                    "severity": "ERROR",
                    "message": f"{employee.get('first_name')} {employee.get('last_name')} has no salary structure on the active contract.",
                    "is_resolved": False,
                })
                all_warnings.append(warning)
                self.payroll_repo.update_payrun_employee_status(pe["id"], "ERROR", "No salary structure")
                continue

            schedule = None
            if hasattr(self.schedule_repo, "find_for_employee"):
                schedule = self.schedule_repo.find_for_employee(emp_id, period_end)
            if not schedule and contract.get("schedule_id"):
                schedule = self.schedule_repo.find_by_id(contract.get("schedule_id"))
            schedule_days = self.schedule_repo.find_days((schedule or {}).get("id", ""))

            all_existing = self.payroll_repo.find_payslips({"employee_id": emp_id})
            existing = [p for p in all_existing if str(p.get("payrun_id")) == str(payrun_id)]
            pre_warns = validate_pre_compute(
                employee, contract, None,
                [p for p in all_existing if str(p.get("payrun_id")) != str(payrun_id)],
                period_start.isoformat(), period_end.isoformat()
            )
            for w in pre_warns:
                w["payrun_id"] = payrun_id
                all_warnings.append(self.payroll_repo.create_warning(w))

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
            payslip_data["payslip_number"] = f"PS-{payrun.get('run_number')}-{employee.get('employee_code') or emp_id[:8]}"
            payslip_data["generated_at"] = datetime.now(timezone.utc).isoformat()

            created_payslip = None
            for ps in existing:
                if ps.get("status") not in ("CANCELLED",):
                    created_payslip = self.payroll_repo.update_payslip(ps["id"], payslip_data)
                    break

            if not created_payslip:
                try:
                    created_payslip = self.payroll_repo.create_payslip(payslip_data)
                except Exception:
                    reused = None
                    if hasattr(self.payroll_repo, "find_payslip_by_number"):
                        reused = self.payroll_repo.find_payslip_by_number(payslip_data["payslip_number"])
                    if not reused:
                        raise
                    created_payslip = self.payroll_repo.update_payslip(reused["id"], payslip_data)

            ps_id = created_payslip["id"]
            self.payroll_repo.delete_payslip_lines(ps_id)
            if hasattr(self.payroll_repo, "delete_payslip_artifacts"):
                self.payroll_repo.delete_payslip_artifacts(ps_id)

            for line in lines:
                line["payslip_id"] = ps_id
                self.payroll_repo.create_payslip_line(line)

            inputs = trace.to_dict()["inputs"]
            self.payroll_repo.save_payslip_trace(ps_id, trace.to_dict()["entries"], inputs)
            self.payroll_repo.save_payslip_inputs(ps_id, inputs)
            self.payroll_repo.save_payslip_worked_days(ps_id, {
                **inputs,
                "worked_hours": float(ctx.worked_days) * 8.0,
            })
            self.payroll_repo.save_payslip_snapshot(ps_id, {
                "employee_snapshot": employee,
                "contract_snapshot": contract,
                "attendance_snapshot": att_records,
                "leave_snapshot": all_leaves,
                "salary_structure_snapshot": structure,
                "salary_rules_snapshot": versions,
            })

            post_warns = validate_post_compute(created_payslip)
            for w in post_warns:
                w["payrun_id"] = payrun_id
                all_warnings.append(self.payroll_repo.create_warning(w))

            self.payroll_repo.update_payrun_employee_status(pe["id"], "CALCULATED")
            total_gross += float(created_payslip.get("gross") or created_payslip.get("gross_salary") or 0)
            total_deductions += float(created_payslip.get("total_deductions") or 0)
            total_net += float(created_payslip.get("net") or created_payslip.get("net_salary") or 0)
            computed_payslips.append(created_payslip)

        return {
            "payslips": computed_payslips,
            "warnings": all_warnings,
            "total_gross": round(total_gross, 2),
            "total_deductions": round(total_deductions, 2),
            "total_net": round(total_net, 2),
        }
