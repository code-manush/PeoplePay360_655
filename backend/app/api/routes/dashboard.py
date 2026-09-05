from fastapi import APIRouter, Depends
from app.repositories.postgres_repos import (
    PostgresEmployeeRepository, PostgresPayrollRepository,
    PostgresAttendanceRepository, PostgresLeaveRepository,
    PostgresContractRepository, PostgresNotificationRepository
)
from app.core.response import success_response
from app.api.deps import get_current_user
from datetime import date

router = APIRouter(prefix="/dashboard", tags=["dashboard"])
emp_repo = PostgresEmployeeRepository()
payroll_repo = PostgresPayrollRepository()
att_repo = PostgresAttendanceRepository()
leave_repo = PostgresLeaveRepository()
contract_repo = PostgresContractRepository()
notif_repo = PostgresNotificationRepository()


@router.get("")
def get_dashboard(current: dict = Depends(get_current_user)):
    all_emps = emp_repo.find_all()
    active_emps = [e for e in all_emps if e.get("is_active")]
    emp_by_type = {}
    for e in active_emps:
        t = e.get("employment_type", "FULL_TIME")
        emp_by_type[t] = emp_by_type.get(t, 0) + 1

    emp_by_dept = {}
    for e in active_emps:
        d = e.get("department_id", "Unknown")
        emp_by_dept[d] = emp_by_dept.get(d, 0) + 1

    today = date.today().isoformat()
    today_att = att_repo.find_all({"date_from": today, "date_to": today})
    present_today = sum(1 for a in today_att if a["status"] in ("PRESENT", "LATE", "OVERTIME", "CORRECTED", "MISSING_CHECKOUT", "HALF_DAY"))
    late_today = sum(1 for a in today_att if a["status"] == "LATE")

    pending_leaves = leave_repo.find_requests({"status": "PENDING"})

    all_payruns = payroll_repo.find_payruns()
    paid_runs = [p for p in all_payruns if p["status"] == "PAID"]
    latest_run = max(paid_runs, key=lambda p: p.get("paid_at", ""), default=None)
    total_payroll_disbursed = sum(p.get("total_net", 0) or 0 for p in paid_runs)

    from datetime import date as date_type, timedelta
    today_dt = date_type.today()
    active_contracts = contract_repo.find_all({"status": "ACTIVE"})
    expiring_30 = [c for c in active_contracts if c.get("end_date") and
                   0 <= (date_type.fromisoformat(c["end_date"]) - today_dt).days <= 30]
    expiring_60 = [c for c in active_contracts if c.get("end_date") and
                   31 <= (date_type.fromisoformat(c["end_date"]) - today_dt).days <= 60]
    expiring_90 = [c for c in active_contracts if c.get("end_date") and
                   61 <= (date_type.fromisoformat(c["end_date"]) - today_dt).days <= 90]

    all_warnings = payroll_repo.find_warnings({"is_resolved": False})
    critical_warnings = [w for w in all_warnings if w.get("severity") in ("ERROR", "BLOCKER")]

    from datetime import datetime
    thirty_days_ago = (today_dt - timedelta(days=30)).isoformat()
    recent_att = att_repo.find_all({"date_from": thirty_days_ago, "date_to": today})
    recent_present = sum(1 for a in recent_att if a["status"] in ("PRESENT", "LATE", "OVERTIME", "CORRECTED", "HALF_DAY"))
    recent_att_rate = round(recent_present / len(recent_att) * 100, 1) if recent_att else 0

    from collections import defaultdict
    monthly_payroll = defaultdict(float)
    for p in paid_runs:
        month = p.get("period_start", "")[:7]
        monthly_payroll[month] += p.get("total_net", 0) or 0
    payroll_trend = [{"month": m, "total_net": round(monthly_payroll[m], 2)}
                     for m in sorted(monthly_payroll.keys())[-6:]]

    from app.repositories.postgres_repos import PostgresDepartmentRepository
    dept_repo = PostgresDepartmentRepository()
    depts = dept_repo.find_all()
    emps_by_dept = {}
    for e in all_emps:
        emps_by_dept.setdefault(e.get("department_id"), set()).add(e["id"])
    dept_att = []
    for dept in depts:
        dept_emps = emps_by_dept.get(dept["id"], set())
        dept_records = [a for a in recent_att if a["employee_id"] in dept_emps]
        dept_present = sum(1 for a in dept_records if a["status"] in ("PRESENT", "LATE", "OVERTIME", "CORRECTED"))
        dept_att.append({
            "department_id": dept["id"],
            "department_name": dept.get("name"),
            "attendance_rate": round(dept_present / len(dept_records) * 100, 1) if dept_records else 0,
            "employee_count": len(dept_emps),
        })

    active_notifs = notif_repo.find_all({"is_active": True})

    return success_response({
        "kpis": {
            "total_employees": len(all_emps),
            "active_employees": len(active_emps),
            "new_this_month": sum(1 for e in all_emps if (e.get("date_joined") or "")[:7] == today[:7]),
            "present_today": present_today,
            "late_today": late_today,
            "attendance_rate_30d": recent_att_rate,
            "pending_leave_requests": len(pending_leaves),
            "contracts_expiring_30d": len(expiring_30),
            "unresolved_warnings": len(all_warnings),
            "critical_warnings": len(critical_warnings),
            "last_payrun_total": latest_run.get("total_net") if latest_run else 0,
            "total_payroll_disbursed": round(total_payroll_disbursed, 2),
        },
        "employeesByType": [{"type": k, "count": v} for k, v in emp_by_type.items()],
        "employeesByDept": [
            {**{"department_id": k, "count": v},
             **{"department_name": next((d["name"] for d in depts if d["id"] == k), k)}}
            for k, v in emp_by_dept.items()
        ],
        "attendanceByDept": dept_att,
        "payrollTrend": payroll_trend,
        "recentPayruns": sorted(all_payruns, key=lambda p: p.get("created_at", ""), reverse=True)[:5],
        "pendingLeaveRequests": pending_leaves[:5],
        "expiringContracts": {
            "critical": len(expiring_30),
            "warning": len(expiring_60),
            "notice": len(expiring_90),
        },
        "warnings": {
            "total_unresolved": len(all_warnings),
            "critical": len(critical_warnings),
            "latest": sorted(all_warnings, key=lambda w: w.get("created_at", ""), reverse=True)[:5],
        },
        "activeNotifications": active_notifs[:10],
        "lastUpdated": datetime.now().isoformat(),
    })


stats_router = APIRouter(prefix="/stats", tags=["dashboard"])

@stats_router.get("")
def get_stats(current: dict = Depends(get_current_user)):
    return get_dashboard(current)
