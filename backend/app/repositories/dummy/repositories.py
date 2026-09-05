"""
Dummy repository implementations backed by in-memory JSON data.

INTEGRATION BOUNDARY:
When your teammate integrates Aiven PostgreSQL, they should:
1. Create `aiven/` folder next to `dummy/`
2. Implement AivenEmployeeRepository(EmployeeRepository)
3. Update the dependency injection in app/api/dependencies.py
"""
from typing import Any, Dict, List, Optional
from datetime import datetime, timezone

from app.repositories.dummy import store


class DummyEmployeeRepository:
    def find_all(self, filters: Optional[Dict[str, Any]] = None) -> List[Dict]:
        data = list(store.employees)
        if not filters:
            return data
        if filters.get("department_id"):
            data = [e for e in data if e.get("department_id") == filters["department_id"]]
        if filters.get("employment_type"):
            data = [e for e in data if e.get("employment_type") == filters["employment_type"]]
        if filters.get("employment_status"):
            data = [e for e in data if e.get("employment_status") == filters["employment_status"]]
        if filters.get("manager_id"):
            data = [e for e in data if e.get("manager_id") == filters["manager_id"]]
        if filters.get("is_active") is not None:
            data = [e for e in data if e.get("is_active") == filters["is_active"]]
        if filters.get("search"):
            q = filters["search"].lower()
            data = [e for e in data if
                    q in e.get("first_name", "").lower() or
                    q in e.get("last_name", "").lower() or
                    q in e.get("email", "").lower() or
                    q in e.get("employee_code", "").lower()]
        return data

    def find_by_id(self, id: str) -> Optional[Dict]:
        return next((e for e in store.employees if e["id"] == id), None)

    def create(self, data: Dict[str, Any]) -> Dict:
        data["id"] = store.next_id("emp", store.employees)
        data["created_at"] = datetime.now(timezone.utc).isoformat()
        data["updated_at"] = datetime.now(timezone.utc).isoformat()
        store.employees.append(data)
        return data

    def update(self, id: str, data: Dict[str, Any]) -> Optional[Dict]:
        for i, emp in enumerate(store.employees):
            if emp["id"] == id:
                store.employees[i] = {**emp, **data, "updated_at": datetime.now(timezone.utc).isoformat()}
                return store.employees[i]
        return None

    def delete(self, id: str) -> bool:
        for i, emp in enumerate(store.employees):
            if emp["id"] == id:
                store.employees.pop(i)
                return True
        return False


class DummyDepartmentRepository:
    def find_all(self, filters=None) -> List[Dict]:
        data = list(store.departments)
        if filters and filters.get("is_active") is not None:
            data = [d for d in data if d.get("is_active") == filters["is_active"]]
        return data

    def find_by_id(self, id: str) -> Optional[Dict]:
        return next((d for d in store.departments if d["id"] == id), None)

    def create(self, data: Dict) -> Dict:
        data["id"] = store.next_id("dept", store.departments)
        store.departments.append(data)
        return data

    def update(self, id: str, data: Dict) -> Optional[Dict]:
        for i, dept in enumerate(store.departments):
            if dept["id"] == id:
                store.departments[i] = {**dept, **data}
                return store.departments[i]
        return None

    def delete(self, id: str) -> bool:
        for i, dept in enumerate(store.departments):
            if dept["id"] == id:
                store.departments.pop(i)
                return True
        return False


class DummyJobPositionRepository:
    def find_all(self, filters=None) -> List[Dict]:
        data = list(store.job_positions)
        if filters and filters.get("department_id"):
            data = [p for p in data if p.get("department_id") == filters["department_id"]]
        return data

    def find_by_id(self, id: str) -> Optional[Dict]:
        return next((p for p in store.job_positions if p["id"] == id), None)

    def create(self, data: Dict) -> Dict:
        data["id"] = store.next_id("pos", store.job_positions)
        store.job_positions.append(data)
        return data

    def update(self, id: str, data: Dict) -> Optional[Dict]:
        for i, pos in enumerate(store.job_positions):
            if pos["id"] == id:
                store.job_positions[i] = {**pos, **data}
                return store.job_positions[i]
        return None

    def delete(self, id: str) -> bool:
        for i, pos in enumerate(store.job_positions):
            if pos["id"] == id:
                store.job_positions.pop(i)
                return True
        return False


class DummyContractRepository:
    def find_all(self, filters=None) -> List[Dict]:
        data = list(store.contracts)
        if not filters:
            return data
        if filters.get("employee_id"):
            data = [c for c in data if c.get("employee_id") == filters["employee_id"]]
        if filters.get("status"):
            data = [c for c in data if c.get("status") == filters["status"]]
        if filters.get("department_id"):
            data = [c for c in data if c.get("department_id") == filters["department_id"]]
        return data

    def find_by_id(self, id: str) -> Optional[Dict]:
        return next((c for c in store.contracts if c["id"] == id), None)

    def create(self, data: Dict) -> Dict:
        data["id"] = store.next_id("con", store.contracts)
        data["created_at"] = datetime.now(timezone.utc).isoformat()
        data["updated_at"] = datetime.now(timezone.utc).isoformat()
        store.contracts.append(data)
        return data

    def update(self, id: str, data: Dict) -> Optional[Dict]:
        for i, con in enumerate(store.contracts):
            if con["id"] == id:
                store.contracts[i] = {**con, **data, "updated_at": datetime.now(timezone.utc).isoformat()}
                return store.contracts[i]
        return None

    def delete(self, id: str) -> bool:
        for i, con in enumerate(store.contracts):
            if con["id"] == id:
                store.contracts.pop(i)
                return True
        return False


class DummyScheduleRepository:
    def find_all(self, filters=None) -> List[Dict]:
        return list(store.working_schedules)

    def find_by_id(self, id: str) -> Optional[Dict]:
        return next((s for s in store.working_schedules if s["id"] == id), None)

    def find_days(self, schedule_id: str) -> List[Dict]:
        return [d for d in store.working_schedule_days if d["schedule_id"] == schedule_id]

    def create(self, data: Dict) -> Dict:
        data["id"] = store.next_id("sched", store.working_schedules)
        data["created_at"] = datetime.now(timezone.utc).isoformat()
        store.working_schedules.append(data)
        return data

    def update(self, id: str, data: Dict) -> Optional[Dict]:
        for i, s in enumerate(store.working_schedules):
            if s["id"] == id:
                store.working_schedules[i] = {**s, **data}
                return store.working_schedules[i]
        return None

    def delete(self, id: str) -> bool:
        for i, s in enumerate(store.working_schedules):
            if s["id"] == id:
                store.working_schedules.pop(i)
                # Also delete schedule days
                store.working_schedule_days[:] = [
                    d for d in store.working_schedule_days if d["schedule_id"] != id
                ]
                return True
        return False

    def upsert_days(self, schedule_id: str, days: List[Dict]) -> List[Dict]:
        store.working_schedule_days[:] = [
            d for d in store.working_schedule_days if d["schedule_id"] != schedule_id
        ]
        for i, day in enumerate(days):
            day["id"] = store.next_id("sd", store.working_schedule_days)
            day["schedule_id"] = schedule_id
            store.working_schedule_days.append(day)
        return days


class DummyAttendanceRepository:
    def find_all(self, filters=None) -> List[Dict]:
        data = list(store.attendance_records)
        if not filters:
            return data
        if filters.get("employee_id"):
            data = [a for a in data if a.get("employee_id") == filters["employee_id"]]
        if filters.get("date"):
            data = [a for a in data if a.get("date") == filters["date"]]
        if filters.get("status"):
            data = [a for a in data if a.get("status") == filters["status"]]
        if filters.get("date_from"):
            data = [a for a in data if a.get("date", "") >= filters["date_from"]]
        if filters.get("date_to"):
            data = [a for a in data if a.get("date", "") <= filters["date_to"]]
        return data

    def find_by_id(self, id: str) -> Optional[Dict]:
        return next((a for a in store.attendance_records if a["id"] == id), None)

    def find_active(self) -> List[Dict]:
        """Employees currently checked in (no checkout)."""
        return [a for a in store.attendance_records
                if a.get("check_in") and not a.get("check_out")]

    def create(self, data: Dict) -> Dict:
        data["id"] = store.next_id("att", store.attendance_records)
        store.attendance_records.append(data)
        return data

    def update(self, id: str, data: Dict) -> Optional[Dict]:
        for i, att in enumerate(store.attendance_records):
            if att["id"] == id:
                store.attendance_records[i] = {**att, **data}
                return store.attendance_records[i]
        return None

    def delete(self, id: str) -> bool:
        for i, att in enumerate(store.attendance_records):
            if att["id"] == id:
                store.attendance_records.pop(i)
                return True
        return False


class DummyLeaveRepository:
    def find_types(self) -> List[Dict]:
        return list(store.time_off_types)

    def find_type_by_id(self, id: str) -> Optional[Dict]:
        return next((t for t in store.time_off_types if t["id"] == id), None)

    def find_allocations(self, filters=None) -> List[Dict]:
        data = list(store.leave_allocations)
        if filters and filters.get("employee_id"):
            data = [a for a in data if a.get("employee_id") == filters["employee_id"]]
        if filters and filters.get("year"):
            data = [a for a in data if a.get("year") == filters["year"]]
        return data

    def find_allocation_by_id(self, id: str) -> Optional[Dict]:
        return next((a for a in store.leave_allocations if a["id"] == id), None)

    def update_allocation(self, id: str, data: Dict) -> Optional[Dict]:
        for i, alloc in enumerate(store.leave_allocations):
            if alloc["id"] == id:
                store.leave_allocations[i] = {**alloc, **data}
                return store.leave_allocations[i]
        return None

    def find_requests(self, filters=None) -> List[Dict]:
        data = list(store.leave_requests)
        if not filters:
            return data
        if filters.get("employee_id"):
            data = [r for r in data if r.get("employee_id") == filters["employee_id"]]
        if filters.get("status"):
            data = [r for r in data if r.get("status") == filters["status"]]
        if filters.get("time_off_type_id"):
            data = [r for r in data if r.get("time_off_type_id") == filters["time_off_type_id"]]
        return data

    def find_request_by_id(self, id: str) -> Optional[Dict]:
        return next((r for r in store.leave_requests if r["id"] == id), None)

    def create_request(self, data: Dict) -> Dict:
        data["id"] = store.next_id("lr", store.leave_requests)
        data["created_at"] = datetime.now(timezone.utc).isoformat()
        store.leave_requests.append(data)
        return data

    def update_request(self, id: str, data: Dict) -> Optional[Dict]:
        for i, req in enumerate(store.leave_requests):
            if req["id"] == id:
                store.leave_requests[i] = {**req, **data}
                return store.leave_requests[i]
        return None


class DummyPayrollRepository:
    # ── Salary Structures ──────────────────────────────────────────────────────
    def find_structures(self, filters=None) -> List[Dict]:
        data = list(store.salary_structures)
        if filters and filters.get("is_active") is not None:
            data = [s for s in data if s.get("is_active") == filters["is_active"]]
        return data

    def find_structure_by_id(self, id: str) -> Optional[Dict]:
        return next((s for s in store.salary_structures if s["id"] == id), None)

    # ── Salary Rules ───────────────────────────────────────────────────────────
    def find_rules(self, filters=None) -> List[Dict]:
        return list(store.salary_rules)

    def find_rule_by_id(self, id: str) -> Optional[Dict]:
        return next((r for r in store.salary_rules if r["id"] == id), None)

    # ── Salary Rule Versions ───────────────────────────────────────────────────
    def find_rule_versions(self, structure_id: str) -> List[Dict]:
        return sorted(
            [v for v in store.salary_rule_versions if v["structure_id"] == structure_id],
            key=lambda v: v.get("sequence", 0)
        )

    # ── Payruns ───────────────────────────────────────────────────────────────
    def find_payruns(self, filters=None) -> List[Dict]:
        data = list(store.payruns)
        if filters and filters.get("status"):
            data = [p for p in data if p.get("status") == filters["status"]]
        return data

    def find_payrun_by_id(self, id: str) -> Optional[Dict]:
        return next((p for p in store.payruns if p["id"] == id), None)

    def create_payrun(self, data: Dict) -> Dict:
        data["id"] = store.next_id("pr", store.payruns)
        data["created_at"] = datetime.now(timezone.utc).isoformat()
        store.payruns.append(data)
        return data

    def update_payrun(self, id: str, data: Dict) -> Optional[Dict]:
        for i, pr in enumerate(store.payruns):
            if pr["id"] == id:
                store.payruns[i] = {**pr, **data}
                return store.payruns[i]
        return None

    # ── Payrun Employees ───────────────────────────────────────────────────────
    def find_payrun_employees(self, payrun_id: str) -> List[Dict]:
        return [e for e in store.payrun_employees if e["payrun_id"] == payrun_id]

    def add_payrun_employee(self, data: Dict) -> Dict:
        data["id"] = store.next_id("pre", store.payrun_employees)
        store.payrun_employees.append(data)
        return data

    # ── Payslips ───────────────────────────────────────────────────────────────
    def find_payslips(self, filters=None) -> List[Dict]:
        data = list(store.payslips)
        if not filters:
            return data
        if filters.get("employee_id"):
            data = [p for p in data if p.get("employee_id") == filters["employee_id"]]
        if filters.get("payrun_id"):
            data = [p for p in data if p.get("payrun_id") == filters["payrun_id"]]
        if filters.get("status"):
            data = [p for p in data if p.get("status") == filters["status"]]
        if filters.get("period_start"):
            data = [p for p in data if p.get("period_start", "") >= filters["period_start"]]
        if filters.get("period_end"):
            data = [p for p in data if p.get("period_end", "") <= filters["period_end"]]
        return data

    def find_payslip_by_id(self, id: str) -> Optional[Dict]:
        return next((p for p in store.payslips if p["id"] == id), None)

    def create_payslip(self, data: Dict) -> Dict:
        data["id"] = store.next_id("ps", store.payslips)
        data["created_at"] = datetime.now(timezone.utc).isoformat()
        store.payslips.append(data)
        return data

    def update_payslip(self, id: str, data: Dict) -> Optional[Dict]:
        for i, ps in enumerate(store.payslips):
            if ps["id"] == id:
                store.payslips[i] = {**ps, **data}
                return store.payslips[i]
        return None

    # ── Payslip Lines ──────────────────────────────────────────────────────────
    def find_payslip_lines(self, payslip_id: str) -> List[Dict]:
        return sorted(
            [l for l in store.payslip_lines if l["payslip_id"] == payslip_id],
            key=lambda l: l.get("sequence", 0)
        )

    def create_payslip_line(self, data: Dict) -> Dict:
        data["id"] = store.next_id("psl", store.payslip_lines)
        store.payslip_lines.append(data)
        return data

    def delete_payslip_lines(self, payslip_id: str):
        store.payslip_lines[:] = [l for l in store.payslip_lines if l["payslip_id"] != payslip_id]

    # ── Warnings ───────────────────────────────────────────────────────────────
    def find_warnings(self, filters=None) -> List[Dict]:
        data = list(store.payroll_warnings)
        if not filters:
            return data
        if filters.get("employee_id"):
            data = [w for w in data if w.get("employee_id") == filters["employee_id"]]
        if filters.get("payrun_id"):
            data = [w for w in data if w.get("payrun_id") == filters["payrun_id"]]
        if filters.get("is_resolved") is not None:
            data = [w for w in data if w.get("is_resolved") == filters["is_resolved"]]
        return data

    def create_warning(self, data: Dict) -> Dict:
        data["id"] = store.next_id("warn", store.payroll_warnings)
        data["created_at"] = datetime.now(timezone.utc).isoformat()
        store.payroll_warnings.append(data)
        return data

    def update_warning(self, id: str, data: Dict) -> Optional[Dict]:
        for i, w in enumerate(store.payroll_warnings):
            if w["id"] == id:
                store.payroll_warnings[i] = {**w, **data}
                return store.payroll_warnings[i]
        return None

    # ── Payments ───────────────────────────────────────────────────────────────
    def find_payments(self, filters=None) -> List[Dict]:
        data = list(store.payments)
        if filters and filters.get("payslip_id"):
            data = [p for p in data if p.get("payslip_id") == filters["payslip_id"]]
        if filters and filters.get("employee_id"):
            data = [p for p in data if p.get("employee_id") == filters["employee_id"]]
        return data

    def create_payment(self, data: Dict) -> Dict:
        data["id"] = store.next_id("pay", store.payments)
        data["initiated_at"] = datetime.now(timezone.utc).isoformat()
        store.payments.append(data)
        return data

    # ── Deliveries ─────────────────────────────────────────────────────────────
    def find_deliveries(self, payrun_id: str) -> List[Dict]:
        return [d for d in store.payslip_deliveries if d["payrun_id"] == payrun_id]

    def create_delivery(self, data: Dict) -> Dict:
        data["id"] = store.next_id("del", store.payslip_deliveries)
        store.payslip_deliveries.append(data)
        return data

    def update_delivery(self, id: str, data: Dict) -> Optional[Dict]:
        for i, d in enumerate(store.payslip_deliveries):
            if d["id"] == id:
                store.payslip_deliveries[i] = {**d, **data}
                return store.payslip_deliveries[i]
        return None


class DummyNotificationRepository:
    def find_all(self, filters=None) -> List[Dict]:
        data = list(store.notifications)
        if filters and filters.get("is_active") is not None:
            data = [n for n in data if n.get("is_active") == filters["is_active"]]
        return data

    def find_for_employee(self, employee_id: str) -> List[Dict]:
        notifs = []
        for n in store.notifications:
            if not n.get("is_active"):
                continue
            target_type = n.get("target_type")
            target_id = n.get("target_id")
            if target_type == "ALL_EMPLOYEES":
                notifs.append(n)
            elif target_type == "EMPLOYEE" and target_id == employee_id:
                notifs.append(n)
            elif target_type == "DEPARTMENT":
                # Get employee's department
                emp = next((e for e in store.employees if e["id"] == employee_id), None)
                if emp and emp.get("department_id") == target_id:
                    notifs.append(n)
        return sorted(notifs, key=lambda n: n.get("published_at", ""), reverse=True)

    def find_by_id(self, id: str) -> Optional[Dict]:
        return next((n for n in store.notifications if n["id"] == id), None)

    def create(self, data: Dict) -> Dict:
        data["id"] = store.next_id("notif", store.notifications)
        data["created_at"] = datetime.now(timezone.utc).isoformat()
        store.notifications.append(data)
        return data

    def update(self, id: str, data: Dict) -> Optional[Dict]:
        for i, n in enumerate(store.notifications):
            if n["id"] == id:
                store.notifications[i] = {**n, **data}
                return store.notifications[i]
        return None


class DummyAuditRepository:
    def find_all(self, filters=None) -> List[Dict]:
        data = list(store.audit_logs)
        if filters and filters.get("entity_id"):
            data = [a for a in data if a.get("entity_id") == filters["entity_id"]]
        if filters and filters.get("event_type"):
            data = [a for a in data if a.get("event_type") == filters["event_type"]]
        return sorted(data, key=lambda a: a.get("created_at", ""), reverse=True)

    def create(self, data: Dict) -> Dict:
        data["id"] = store.next_id("audit", store.audit_logs)
        data["created_at"] = datetime.now(timezone.utc).isoformat()
        store.audit_logs.append(data)
        return data


class DummyBankAccountRepository:
    def find_by_employee(self, employee_id: str) -> List[Dict]:
        return [b for b in store.employee_bank_accounts if b.get("employee_id") == employee_id]

    def find_primary(self, employee_id: str) -> Optional[Dict]:
        return next(
            (b for b in store.employee_bank_accounts
             if b.get("employee_id") == employee_id and b.get("is_primary")),
            None
        )

    def create(self, data: Dict) -> Dict:
        data["id"] = store.next_id("bank", store.employee_bank_accounts)
        store.employee_bank_accounts.append(data)
        return data

    def update(self, id: str, data: Dict) -> Optional[Dict]:
        for i, b in enumerate(store.employee_bank_accounts):
            if b["id"] == id:
                store.employee_bank_accounts[i] = {**b, **data}
                return store.employee_bank_accounts[i]
        return None
