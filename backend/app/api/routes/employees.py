from fastapi import APIRouter, Query, HTTPException, Depends
from typing import Optional
from app.repositories.postgres_repos import (
    PostgresEmployeeRepository, PostgresDepartmentRepository,
    PostgresJobPositionRepository, PostgresContractRepository,
    PostgresAttendanceRepository, PostgresLeaveRepository,
    PostgresPayrollRepository, PostgresNotificationRepository,
    PostgresBankAccountRepository, PostgresUserRepository
)
from app.core.response import success_response, paginated_response, error_response
from app.core.exceptions import NotFoundException
from app.core.config import settings
from app.services.audit_service import audit_service
from app.services.recommendation_service import recommendation_service
from datetime import datetime, timezone
from app.api.deps import get_current_user, require_min_role

router = APIRouter(prefix="/employees", tags=["employees"])
emp_repo = PostgresEmployeeRepository()
dept_repo = PostgresDepartmentRepository()
pos_repo = PostgresJobPositionRepository()
contract_repo = PostgresContractRepository()
att_repo = PostgresAttendanceRepository()
leave_repo = PostgresLeaveRepository()
payroll_repo = PostgresPayrollRepository()
notif_repo = PostgresNotificationRepository()
bank_repo = PostgresBankAccountRepository()
user_repo = PostgresUserRepository()


def _lookup_maps():
    depts = {d["id"]: d for d in dept_repo.find_all()}
    positions = {p["id"]: p for p in pos_repo.find_all()}
    employees = {e["id"]: e for e in emp_repo.find_all()}
    contracts_by_emp = {}
    for c in contract_repo.find_all():
        contracts_by_emp.setdefault(c.get("employee_id"), []).append(c)
    return depts, positions, employees, contracts_by_emp


def _enrich_employee(emp: dict, maps=None) -> dict:
    depts, positions, employees, contracts_by_emp = maps or _lookup_maps()
    manager = employees.get(emp.get("manager_id")) if emp.get("manager_id") else None
    contracts = contracts_by_emp.get(emp["id"], [])
    active_contract = next((c for c in contracts if c.get("status") == "ACTIVE"), None)
    return {
        **emp,
        "department": depts.get(emp.get("department_id")),
        "job_position": positions.get(emp.get("job_position_id")),
        "manager": {"id": manager["id"], "first_name": manager["first_name"], "last_name": manager["last_name"]} if manager else None,
        "active_contract": active_contract,
    }


@router.get("")
def list_employees(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=500),
    search: Optional[str] = None,
    department_id: Optional[str] = None,
    employment_type: Optional[str] = None,
    employment_status: Optional[str] = None,
    is_active: Optional[bool] = None,
    current: dict = Depends(require_min_role("HR")),
):
    filters = {}
    if search:
        filters["search"] = search
    if department_id:
        filters["department_id"] = department_id
    if employment_type:
        filters["employment_type"] = employment_type
    if employment_status:
        filters["employment_status"] = employment_status
    if is_active is not None:
        filters["is_active"] = is_active

    all_emps = emp_repo.find_all(filters)
    total = len(all_emps)
    start = (page - 1) * page_size
    page_data = all_emps[start: start + page_size]
    maps = _lookup_maps()
    enriched = [_enrich_employee(e, maps) for e in page_data]
    return paginated_response(enriched, page, page_size, total)


@router.get("/{employee_id}")
def get_employee(employee_id: str):
    emp = emp_repo.find_by_id(employee_id)
    if not emp:
        raise HTTPException(status_code=404, detail=error_response("NOT_FOUND", f"Employee {employee_id} not found"))
    return success_response(_enrich_employee(emp))



@router.post("")
def create_employee(body: dict, current: dict = Depends(require_min_role("HR"))):
    # Basic validation
    if not body.get("email"):
        raise HTTPException(status_code=422, detail=error_response("VALIDATION_ERROR", "Email is required", "email"))
    if not body.get("first_name"):
        raise HTTPException(status_code=422, detail=error_response("VALIDATION_ERROR", "First name is required", "first_name"))
    try:
        account = user_repo.create_login_account(body["email"], settings.DEMO_PASSWORD, "EMPLOYEE")
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=error_response("EMAIL_EXISTS", str(exc)))
    emp = emp_repo.create({
        **body,
        "user_id": account["id"],
        "employee_code": body.get("employee_code") or emp_repo.next_employee_code(),
        "joining_date": body.get("joining_date") or body.get("date_joined") or datetime.now(timezone.utc).date().isoformat(),
        "employment_type": body.get("employment_type") or "FULL_TIME",
        "status": body.get("employment_status") or body.get("status") or "ACTIVE",
        "employment_status": body.get("employment_status", "ACTIVE"),
        "is_active": True,
    })
    audit_service.log("EMPLOYEE_CREATED", "EMPLOYEE", emp["id"],
                      description=f"Employee {emp.get('first_name')} {emp.get('last_name')} created")
    return success_response(emp, "Employee created successfully")


@router.put("/{employee_id}")
def update_employee(employee_id: str, body: dict, current: dict = Depends(require_min_role("HR"))):
    emp = emp_repo.find_by_id(employee_id)
    if not emp:
        raise HTTPException(status_code=404, detail=error_response("NOT_FOUND", f"Employee {employee_id} not found"))
    updated = emp_repo.update(employee_id, body)
    audit_service.log("EMPLOYEE_UPDATED", "EMPLOYEE", employee_id,
                      description=f"Employee {employee_id} updated")
    return success_response(updated)


@router.patch("/{employee_id}/deactivate")
def deactivate_employee(employee_id: str, current: dict = Depends(require_min_role("HR"))):
    emp = emp_repo.find_by_id(employee_id)
    if not emp:
        raise HTTPException(status_code=404, detail=error_response("NOT_FOUND", f"Employee {employee_id} not found"))
    updated = emp_repo.update(employee_id, {"is_active": False, "status": "INACTIVE", "employment_status": "INACTIVE"})
    if emp.get("user_id"):
        user_repo.set_status(emp["user_id"], "INACTIVE")
    return success_response(updated, "Employee deactivated")


@router.get("/{employee_id}/contracts")
def get_employee_contracts(employee_id: str):
    emp = emp_repo.find_by_id(employee_id)
    if not emp:
        raise HTTPException(status_code=404, detail=error_response("NOT_FOUND", f"Employee {employee_id} not found"))
    contracts = contract_repo.find_all({"employee_id": employee_id})
    return success_response(contracts)


@router.get("/{employee_id}/attendance")
def get_employee_attendance(
    employee_id: str,
    date_from: Optional[str] = None,
    date_to: Optional[str] = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(30, ge=1, le=1000),
):
    filters = {"employee_id": employee_id}
    if date_from:
        filters["date_from"] = date_from
    if date_to:
        filters["date_to"] = date_to
    all_att = att_repo.find_all(filters)
    all_att.sort(key=lambda a: str(a.get("date") or ""), reverse=True)
    total = len(all_att)
    start = (page - 1) * page_size
    return paginated_response(all_att[start: start + page_size], page, page_size, total)


@router.get("/{employee_id}/leave")
def get_employee_leave(employee_id: str):
    requests = leave_repo.find_requests({"employee_id": employee_id})
    allocations = leave_repo.find_allocations({"employee_id": employee_id})
    return success_response({"requests": requests, "allocations": allocations})


@router.get("/{employee_id}/payroll")
def get_employee_payroll(employee_id: str):
    payslips = payroll_repo.find_payslips({"employee_id": employee_id})
    payslips.sort(key=lambda p: p.get("period_start", ""), reverse=True)
    return success_response(payslips)


@router.get("/{employee_id}/notifications")
def get_employee_notifications(employee_id: str):
    notifs = notif_repo.find_for_employee(employee_id)
    return success_response(notifs)


@router.get("/{employee_id}/analytics")
def get_employee_analytics(employee_id: str):
    emp = emp_repo.find_by_id(employee_id)
    if not emp:
        raise HTTPException(status_code=404, detail=error_response("NOT_FOUND", f"Employee {employee_id} not found"))

    att_records = att_repo.find_all({"employee_id": employee_id})
    leave_requests = leave_repo.find_requests({"employee_id": employee_id, "status": "APPROVED"})
    allocations = leave_repo.find_allocations({"employee_id": employee_id})
    payslips = payroll_repo.find_payslips({"employee_id": employee_id})

    total = len(att_records)
    present_count = sum(1 for a in att_records if a["status"] in ("PRESENT", "OVERTIME", "CORRECTED"))
    late_count = sum(1 for a in att_records if a["status"] == "LATE")
    absent_count = sum(1 for a in att_records if a["status"] == "ABSENT")
    half_day_count = sum(1 for a in att_records if a["status"] == "HALF_DAY")
    total_worked_hours = sum(float(a.get("worked_hours") or 0) for a in att_records)
    total_overtime = sum(float(a.get("overtime_hours") or 0) for a in att_records)
    attendance_rate = round((present_count + late_count) / total * 100, 1) if total > 0 else 0

    # Monthly working hours trend (last 6 months)
    from collections import defaultdict
    monthly_hours = defaultdict(float)
    monthly_ot = defaultdict(float)
    for a in att_records:
        month = a.get("date", "")[:7]
        monthly_hours[month] += float(a.get("worked_hours") or 0)
        monthly_ot[month] += float(a.get("overtime_hours") or 0)

    sorted_months = sorted(monthly_hours.keys())[-6:]
    working_hours_trend = [
        {"month": m, "worked_hours": round(monthly_hours[m], 2), "overtime_hours": round(monthly_ot[m], 2)}
        for m in sorted_months
    ]

    # Leave usage
    total_leave_used = sum(float(l.get("duration_days", 0)) for l in leave_requests)
    total_allocated = sum(float(a.get("allocated_units", 0)) for a in allocations)
    total_remaining = sum(float(a.get("remaining_units", 0)) for a in allocations)

    # Payroll trend
    payslip_trend = [
        {"period": p.get("period_start", "")[:7], "gross": p.get("gross", 0), "net": p.get("net", 0)}
        for p in sorted(payslips, key=lambda p: p.get("period_start", ""))[-6:]
    ]

    return success_response({
        "attendanceMetrics": {
            "total_records": total,
            "present_count": present_count,
            "late_count": late_count,
            "absent_count": absent_count,
            "half_day_count": half_day_count,
            "attendance_rate": attendance_rate,
        },
        "workingHours": {
            "total_worked_hours": round(total_worked_hours, 2),
            "average_daily_hours": round(total_worked_hours / total, 2) if total > 0 else 0,
            "trend": working_hours_trend,
        },
        "overtime": {
            "total_overtime_hours": round(total_overtime, 2),
            "trend": [{"month": m, "hours": round(monthly_ot[m], 2)} for m in sorted_months],
        },
        "leaveUsage": {
            "total_leave_used": total_leave_used,
            "total_allocated": total_allocated,
            "total_remaining": total_remaining,
            "leave_requests": len(leave_requests),
        },
        "monthlyTrend": working_hours_trend,
        "payrollTrend": payslip_trend,
    })


@router.get("/{employee_id}/recommendations")
def get_employee_recommendations(employee_id: str):
    emp = emp_repo.find_by_id(employee_id)
    if not emp:
        raise HTTPException(status_code=404, detail=error_response("NOT_FOUND", f"Employee {employee_id} not found"))

    att_records = att_repo.find_all({"employee_id": employee_id})
    allocations = leave_repo.find_allocations({"employee_id": employee_id})
    total = len(att_records)
    present = sum(1 for a in att_records if a["status"] in ("PRESENT", "OVERTIME", "CORRECTED"))
    late = sum(1 for a in att_records if a["status"] == "LATE")
    ot_hours = sum(float(a.get("overtime_hours") or 0) for a in att_records)
    leave_used = sum(float(r.get("duration_days", 0)) for r in leave_repo.find_requests({"employee_id": employee_id, "status": "APPROVED"}))
    leave_remaining = sum(float(a.get("remaining_units", 0)) for a in allocations)
    att_rate = round((present + late) / total * 100, 1) if total > 0 else 0

    recs = recommendation_service.get_recommendations(employee_id, {
        "metrics": {
            "attendance_rate": att_rate,
            "total_overtime_hours": ot_hours,
            "late_count": late,
            "leave_used": leave_used,
            "leave_remaining": leave_remaining,
        }
    })
    return success_response(recs)


@router.get("/{employee_id}/report")
def get_employee_report(employee_id: str):
    emp = emp_repo.find_by_id(employee_id)
    if not emp:
        raise HTTPException(status_code=404, detail=error_response("NOT_FOUND", f"Employee {employee_id} not found"))

    enriched = _enrich_employee(emp)
    att_records = att_repo.find_all({"employee_id": employee_id})
    leave_requests = leave_repo.find_requests({"employee_id": employee_id})
    allocations = leave_repo.find_allocations({"employee_id": employee_id})
    payslips = payroll_repo.find_payslips({"employee_id": employee_id})
    contracts = contract_repo.find_all({"employee_id": employee_id})

    total = len(att_records)
    present = sum(1 for a in att_records if a["status"] in ("PRESENT", "OVERTIME", "CORRECTED"))
    late = sum(1 for a in att_records if a["status"] == "LATE")
    absent = sum(1 for a in att_records if a["status"] == "ABSENT")
    ot_hours = sum(float(a.get("overtime_hours") or 0) for a in att_records)
    worked_hours = sum(float(a.get("worked_hours") or 0) for a in att_records)
    att_rate = round((present + late) / total * 100, 1) if total > 0 else 0

    approved_leaves = [r for r in leave_requests if r["status"] == "APPROVED"]
    leave_taken = sum(float(r.get("duration_days", 0)) for r in approved_leaves)
    leave_remaining = sum(float(a.get("remaining_units", 0)) for a in allocations)

    latest_payslip = max(payslips, key=lambda p: p.get("period_start", ""), default=None)
    active_contract = next((c for c in contracts if c["status"] == "ACTIVE"), None)

    recs = recommendation_service.get_recommendations(employee_id, {
        "metrics": {
            "attendance_rate": att_rate,
            "total_overtime_hours": ot_hours,
            "late_count": late,
            "leave_used": leave_taken,
            "leave_remaining": leave_remaining,
        }
    })

    return success_response({
        "employee": enriched,
        "attendanceMetrics": {
            "total_records": total,
            "present": present,
            "late": late,
            "absent": absent,
            "attendance_rate": att_rate,
            "total_worked_hours": round(worked_hours, 2),
            "total_overtime_hours": round(ot_hours, 2),
            "avg_daily_hours": round(worked_hours / total, 2) if total > 0 else 0,
        },
        "leaveMetrics": {
            "total_requests": len(leave_requests),
            "approved": len(approved_leaves),
            "pending": sum(1 for r in leave_requests if r["status"] == "PENDING"),
            "leave_taken": leave_taken,
            "leave_remaining": leave_remaining,
        },
        "payrollMetrics": {
            "total_payslips": len(payslips),
            "latest_net": latest_payslip.get("net") if latest_payslip else 0,
            "latest_gross": latest_payslip.get("gross") if latest_payslip else 0,
            "latest_period": latest_payslip.get("period_start") if latest_payslip else None,
        },
        "contractInfo": active_contract,
        "recommendations": recs,
    })
