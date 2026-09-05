from fastapi import APIRouter, HTTPException, Query, Depends
from typing import Optional
from datetime import datetime, timezone, date as date_type
from app.repositories.postgres_repos import (
    PostgresAttendanceRepository, PostgresEmployeeRepository
)
from app.notifications.attendance_validation import attendance_validation_service
from app.core.response import success_response, error_response, paginated_response
from app.services.audit_service import audit_service
from app.api.deps import get_current_user
from app.core.security import role_at_least

router = APIRouter(prefix="/attendance", tags=["attendance"])
att_repo = PostgresAttendanceRepository()
emp_repo = PostgresEmployeeRepository()


def _employee_map():
    return {e["id"]: e for e in emp_repo.find_all()}


def _enrich_record(a: dict, employees=None) -> dict:
    emp = (employees or {}).get(a.get("employee_id")) if employees is not None else emp_repo.find_by_id(a.get("employee_id", ""))
    return {
        **a,
        "employee": {
            "id": emp["id"], "first_name": emp["first_name"], "last_name": emp["last_name"],
            "employee_code": emp["employee_code"], "department_id": emp.get("department_id")
        } if emp else None,
    }


def _calc_worked_hours(check_in: str, check_out: str) -> float:
    try:
        ci = datetime.fromisoformat(check_in.replace("Z", "+00:00"))
        co = datetime.fromisoformat(check_out.replace("Z", "+00:00"))
        return round((co - ci).total_seconds() / 3600, 2)
    except Exception:
        return 0.0


def _calc_status(check_in: str, scheduled_start: str = "09:00", worked_hours: float = 0, scheduled_hours: float = 8.0) -> str:
    if worked_hours < scheduled_hours * 0.6:
        return "HALF_DAY"
    return "PRESENT"


@router.get("")
def list_attendance(
    page: int = Query(1, ge=1),
    page_size: int = Query(30, ge=1, le=500),
    employee_id: Optional[str] = None,
    date: Optional[str] = None,
    date_from: Optional[str] = None,
    date_to: Optional[str] = None,
    status: Optional[str] = None,
    department_id: Optional[str] = None,
    current: dict = Depends(get_current_user),
):
    filters = {}
    if not role_at_least(current.get("role"), "HR"):
        filters["employee_id"] = current.get("employee_id")
    elif employee_id:
        filters["employee_id"] = employee_id
    if date:
        filters["date"] = date
    if date_from:
        filters["date_from"] = date_from
    if date_to:
        filters["date_to"] = date_to
    if status:
        filters["status"] = status

    records = att_repo.find_all(filters)

    if department_id:
        dept_emps = {e["id"] for e in emp_repo.find_all({"department_id": department_id})}
        records = [r for r in records if r.get("employee_id") in dept_emps]

    records.sort(key=lambda a: (str(a.get("date") or ""), str(a.get("check_in") or "")), reverse=True)
    total = len(records)
    start = (page - 1) * page_size
    employees = _employee_map()
    enriched = [_enrich_record(r, employees) for r in records[start:start + page_size]]
    return paginated_response(enriched, page, page_size, total)


@router.get("/active-employees")
def get_active_employees():
    """Employees currently checked in."""
    active = att_repo.find_active()
    now = datetime.now(timezone.utc)
    result = []
    for a in active:
        emp = emp_repo.find_by_id(a.get("employee_id", ""))
        if not emp:
            continue
        check_in_str = a.get("check_in", "")
        try:
            ci = datetime.fromisoformat(check_in_str.replace("Z", "+00:00"))
            duration_seconds = (now - ci).total_seconds()
            hours = int(duration_seconds // 3600)
            minutes = int((duration_seconds % 3600) // 60)
            duration_str = f"{hours:02d}h {minutes:02d}m"
        except Exception:
            duration_str = "—"
        result.append({
            "employee_id": emp["id"],
            "employee_code": emp["employee_code"],
            "first_name": emp["first_name"],
            "last_name": emp["last_name"],
            "department_id": emp.get("department_id"),
            "check_in": check_in_str,
            "duration": duration_str,
            "attendance_id": a["id"],
            "status": "WORKING",
        })
    return success_response(result)


@router.get("/employee/{employee_id}")
def get_employee_attendance_records(
    employee_id: str,
    date_from: Optional[str] = None,
    date_to: Optional[str] = None,
):
    filters = {"employee_id": employee_id}
    if date_from:
        filters["date_from"] = date_from
    if date_to:
        filters["date_to"] = date_to
    records = att_repo.find_all(filters)
    records.sort(key=lambda a: a.get("date", ""), reverse=True)
    return success_response(records)


@router.get("/{att_id}")
def get_attendance_record(att_id: str):
    record = att_repo.find_by_id(att_id)
    if not record:
        raise HTTPException(status_code=404, detail=error_response("NOT_FOUND", f"Attendance {att_id} not found"))
    return success_response(_enrich_record(record))


@router.post("/check-in")
def check_in(body: dict, current: dict = Depends(get_current_user)):
    employee_id = body.get("employee_id") or current.get("employee_id")
    if not role_at_least(current.get("role"), "HR"):
        employee_id = current.get("employee_id")
    if not employee_id:
        raise HTTPException(status_code=422, detail=error_response("VALIDATION_ERROR", "employee_id required"))

    emp = emp_repo.find_by_id(employee_id)
    if not emp:
        raise HTTPException(status_code=404, detail=error_response("NOT_FOUND", f"Employee {employee_id} not found"))

    today = date_type.today().isoformat()
    existing = att_repo.find_all({"employee_id": employee_id, "date": today})
    if existing:
        att = existing[0]
        if att.get("check_in") and not att.get("check_out"):
            return success_response(att, "Already checked in today")
        if att.get("check_in") and att.get("check_out"):
            raise HTTPException(status_code=409, detail=error_response("ALREADY_COMPLETE", "Already checked out today."))

    validation = attendance_validation_service.validate_check_in(emp, body.get("request_context", {}))
    if not validation.allowed:
        raise HTTPException(status_code=403, detail=error_response("CHECK_IN_DENIED", validation.reason or "Check-in not allowed"))

    now = datetime.now(timezone.utc).isoformat()
    payload = {
        "check_in": now,
        "check_out": None,
        "worked_hours": None,
        "overtime_hours": None,
        "scheduled_hours": 8.0,
        "status": "PRESENT",
        "notes": "Self check-in",
    }
    if existing:
        record = att_repo.update(existing[0]["id"], payload)
        return success_response(record, "Checked in successfully")
    record = att_repo.create({
        "employee_id": employee_id,
        "date": today,
        **payload,
    })
    return success_response(record, "Checked in successfully")


@router.post("/check-out")
def check_out_today(body: dict = {}, current: dict = Depends(get_current_user)):
    employee_id = current.get("employee_id")
    if not employee_id:
        raise HTTPException(status_code=422, detail=error_response("VALIDATION_ERROR", "No employee profile on this account"))
    today = date_type.today().isoformat()
    existing = att_repo.find_all({"employee_id": employee_id, "date": today})
    if not existing:
        raise HTTPException(status_code=422, detail=error_response("NOT_CHECKED_IN", "Check in first."))
    return check_out(existing[0]["id"], body)


@router.post("/{att_id}/check-out")
def check_out(att_id: str, body: dict = {}, current: dict = Depends(get_current_user)):
    record = att_repo.find_by_id(att_id)
    if not record:
        raise HTTPException(status_code=404, detail=error_response("NOT_FOUND", f"Attendance {att_id} not found"))
    if record.get("check_out"):
        raise HTTPException(status_code=409, detail=error_response("ALREADY_CHECKED_OUT", "Already checked out."))

    emp = emp_repo.find_by_id(record.get("employee_id", ""))
    validation = attendance_validation_service.validate_check_out(emp or {}, record, body.get("request_context", {}))
    if not validation.allowed:
        raise HTTPException(status_code=403, detail=error_response("CHECK_OUT_DENIED", validation.reason or "Check-out not allowed"))

    now = datetime.now(timezone.utc).isoformat()
    worked_hours = _calc_worked_hours(record["check_in"], now)
    scheduled_hours = float(record.get("scheduled_hours", 8.0))
    overtime = max(0.0, worked_hours - scheduled_hours)
    allowed_status = {"PRESENT", "ABSENT", "HALF_DAY", "LEAVE", "HOLIDAY", "WEEKEND"}
    status = _calc_status(record["check_in"], "09:00", worked_hours, scheduled_hours)
    if status not in allowed_status:
        status = "HALF_DAY" if worked_hours < scheduled_hours * 0.6 else "PRESENT"

    updated = att_repo.update(att_id, {
        "check_out": now,
        "worked_hours": worked_hours,
        "overtime_hours": overtime,
        "status": status,
    })
    return success_response(updated, "Checked out successfully")


@router.post("")
def create_attendance(body: dict, current: dict = Depends(get_current_user)):
    if not body.get("employee_id") or not body.get("date"):
        raise HTTPException(status_code=422, detail=error_response("VALIDATION_ERROR", "employee_id and date required"))
    record = att_repo.create(body)
    return success_response(record, "Attendance record created")


@router.put("/{att_id}")
def update_attendance(att_id: str, body: dict, current: dict = Depends(get_current_user)):
    record = att_repo.find_by_id(att_id)
    if not record:
        raise HTTPException(status_code=404, detail=error_response("NOT_FOUND", f"Attendance {att_id} not found"))
    updated = att_repo.update(att_id, body)
    return success_response(updated)


@router.delete("/{att_id}")
def delete_attendance(att_id: str):
    if not att_repo.delete(att_id):
        raise HTTPException(status_code=404, detail=error_response("NOT_FOUND", f"Attendance {att_id} not found"))
    return success_response(None, "Record deleted")


@router.post("/{att_id}/correct")
def correct_attendance(att_id: str, body: dict, current: dict = Depends(get_current_user)):
    record = att_repo.find_by_id(att_id)
    if not record:
        raise HTTPException(status_code=404, detail=error_response("NOT_FOUND", f"Attendance {att_id} not found"))
    if not body.get("correction_reason"):
        raise HTTPException(status_code=422, detail=error_response("VALIDATION_ERROR", "correction_reason is required"))

    ci = body.get("check_in", record["check_in"])
    co = body.get("check_out", record["check_out"])
    worked_hours = _calc_worked_hours(ci, co) if ci and co else record.get("worked_hours")
    updated = att_repo.update(att_id, {
        "check_in": ci,
        "check_out": co,
        "worked_hours": worked_hours,
        "overtime_hours": max(0.0, (worked_hours or 0) - float(record.get("scheduled_hours", 8.0))),
        "notes": body["correction_reason"],
        "status": body.get("status") or record.get("status") or "PRESENT",
    })
    audit_service.log("ATTENDANCE_CORRECTED", "ATTENDANCE", att_id,
                      description=f"Attendance corrected. Reason: {body['correction_reason']}")
    return success_response(updated, "Attendance corrected")


@router.post("/{att_id}/approve")
def approve_attendance(att_id: str, body: dict = {}):
    record = att_repo.find_by_id(att_id)
    if not record:
        raise HTTPException(status_code=404, detail=error_response("NOT_FOUND", f"Attendance {att_id} not found"))
    updated = att_repo.update(att_id, {"approved_by": body.get("approved_by", "HR")})
    return success_response(updated, "Attendance approved")


@router.post("/{att_id}/reject")
def reject_attendance(att_id: str, body: dict = {}):
    record = att_repo.find_by_id(att_id)
    if not record:
        raise HTTPException(status_code=404, detail=error_response("NOT_FOUND", f"Attendance {att_id} not found"))
    updated = att_repo.update(att_id, {"status": "ABSENT", "correction_reason": body.get("reason", "Rejected by HR")})
    return success_response(updated, "Attendance rejected")
