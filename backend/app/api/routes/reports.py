from fastapi import APIRouter, Depends, Query
from typing import Optional
from collections import defaultdict

from app.api.deps import get_current_user, require_min_role
from app.core.response import success_response
from app.repositories.postgres_repos import (
    PostgresEmployeeRepository, PostgresPayrollRepository,
    PostgresAttendanceRepository, PostgresLeaveRepository,
    PostgresDepartmentRepository, PostgresContractRepository,
)

router = APIRouter(prefix="/reports", tags=["reports"])
emp_repo = PostgresEmployeeRepository()
payroll_repo = PostgresPayrollRepository()
att_repo = PostgresAttendanceRepository()
leave_repo = PostgresLeaveRepository()
dept_repo = PostgresDepartmentRepository()
contract_repo = PostgresContractRepository()


@router.get("")
def get_reports(
    department_id: Optional[str] = None,
    period_start: Optional[str] = Query(None),
    period_end: Optional[str] = Query(None),
    current: dict = Depends(require_min_role("HR")),
):
    employees = emp_repo.find_all()
    if department_id:
        employees = [e for e in employees if e.get("department_id") == department_id]
    emp_ids = {e["id"] for e in employees}
    depts = {d["id"]: d for d in dept_repo.find_all()}

    att_filters = {}
    if period_start:
        att_filters["date_from"] = period_start
    if period_end:
        att_filters["date_to"] = period_end
    attendance = [a for a in att_repo.find_all(att_filters) if a.get("employee_id") in emp_ids]
    leaves = [r for r in leave_repo.find_requests() if r.get("employee_id") in emp_ids]
    payruns = payroll_repo.find_payruns()
    payslips = [p for p in payroll_repo.find_payslips() if p.get("employee_id") in emp_ids]
    contracts = [c for c in contract_repo.find_all({"status": "ACTIVE"}) if c.get("employee_id") in emp_ids]

    present = sum(1 for a in attendance if a.get("status") in ("PRESENT", "LATE", "OVERTIME", "HALF_DAY"))
    absent = sum(1 for a in attendance if a.get("status") == "ABSENT")
    approved_leave = [r for r in leaves if r.get("status") == "APPROVED"]
    pending_leave = [r for r in leaves if r.get("status") == "PENDING"]

    dept_salary = defaultdict(float)
    dept_headcount = defaultdict(int)
    for e in employees:
        dept_headcount[e.get("department_id") or "unknown"] += 1
    for c in contracts:
        emp = next((e for e in employees if e["id"] == c.get("employee_id")), None)
        if emp:
            dept_salary[emp.get("department_id") or "unknown"] += float(c.get("base_salary") or 0)

    monthly = defaultdict(float)
    for p in payslips:
        month = (p.get("period_start") or "")[:7]
        monthly[month] += float(p.get("net") or 0)

    return success_response({
        "filters": {"department_id": department_id, "period_start": period_start, "period_end": period_end},
        "kpis": {
            "employees": len(employees),
            "active_employees": sum(1 for e in employees if e.get("is_active")),
            "active_contracts": len(contracts),
            "attendance_records": len(attendance),
            "present_count": present,
            "absent_count": absent,
            "attendance_health": round(present / len(attendance) * 100, 1) if attendance else 0,
            "approved_leave_days": sum(float(r.get("duration_days") or 0) for r in approved_leave),
            "pending_leave_requests": len(pending_leave),
            "payslips": len(payslips),
            "total_net_paid": round(sum(float(p.get("net") or 0) for p in payslips if p.get("status") == "PAID"), 2),
            "average_salary": round(sum(float(c.get("base_salary") or 0) for c in contracts) / len(contracts), 2) if contracts else 0,
        },
        "salaryByDepartment": [
            {
                "department_id": did,
                "department_name": (depts.get(did) or {}).get("name") or "Unknown",
                "headcount": dept_headcount.get(did, 0),
                "total_salary": round(amount, 2),
            }
            for did, amount in dept_salary.items()
        ],
        "monthlyNetTrend": [{"month": m, "total_net": round(monthly[m], 2)} for m in sorted(monthly.keys())],
        "recentPayruns": sorted(payruns, key=lambda p: p.get("period_start") or "", reverse=True)[:6],
        "pendingLeave": pending_leave[:10],
    })
