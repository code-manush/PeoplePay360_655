from fastapi import APIRouter, HTTPException, Query, Depends
from typing import Optional
from datetime import datetime, timezone, date as date_type
from app.repositories.postgres_repos import (
    PostgresLeaveRepository, PostgresEmployeeRepository, PostgresNotificationRepository
)
from app.core.response import success_response, error_response, paginated_response
from app.services.audit_service import audit_service
from app.api.deps import get_current_user, require_min_role
from app.core.security import role_at_least

types_router = APIRouter(prefix="/time-off", tags=["time-off"])
leave_router = APIRouter(prefix="/leave", tags=["leave"])

leave_repo = PostgresLeaveRepository()
emp_repo = PostgresEmployeeRepository()
notif_repo = PostgresNotificationRepository()


@types_router.get("/types")
def list_time_off_types(current: dict = Depends(get_current_user)):
    return success_response(leave_repo.find_types())


@types_router.get("/types/{type_id}")
def get_time_off_type(type_id: str):
    t = leave_repo.find_type_by_id(type_id)
    if not t:
        raise HTTPException(status_code=404, detail=error_response("NOT_FOUND", f"Time off type {type_id} not found"))
    return success_response(t)


@leave_router.get("/allocations")
def list_allocations(employee_id: Optional[str] = None, year: Optional[int] = None):
    filters = {}
    if employee_id:
        filters["employee_id"] = employee_id
    if year:
        filters["year"] = year
    allocations = leave_repo.find_allocations(filters)
    # Enrich with type info
    for alloc in allocations:
        t = leave_repo.find_type_by_id(alloc.get("time_off_type_id", ""))
        alloc["time_off_type"] = t
    return success_response(allocations)


@leave_router.get("/allocations/{employee_id}")
def get_employee_allocations(employee_id: str, year: Optional[int] = None):
    filters = {"employee_id": employee_id}
    if year:
        filters["year"] = year
    allocations = leave_repo.find_allocations(filters)
    for alloc in allocations:
        t = leave_repo.find_type_by_id(alloc.get("time_off_type_id", ""))
        alloc["time_off_type"] = t
    return success_response(allocations)


@leave_router.get("/requests")
def list_leave_requests(
    employee_id: Optional[str] = None,
    status: Optional[str] = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=1000),
    current: dict = Depends(get_current_user),
):
    filters = {}
    if not role_at_least(current.get("role"), "HR"):
        filters["employee_id"] = current.get("employee_id")
    elif employee_id:
        filters["employee_id"] = employee_id
    if status:
        filters["status"] = status
    all_requests = leave_repo.find_requests(filters)

    employees = {e["id"]: e for e in emp_repo.find_all()}
    types = {t["id"]: t for t in leave_repo.find_types()}
    enriched = []
    for r in all_requests:
        emp = employees.get(r.get("employee_id"))
        t = types.get(r.get("time_off_type_id"))
        enriched.append({
            **r,
            "employee": {"id": emp["id"], "first_name": emp["first_name"],
                         "last_name": emp["last_name"], "employee_code": emp["employee_code"]} if emp else None,
            "time_off_type": t,
        })

    enriched.sort(key=lambda r: r.get("created_at", ""), reverse=True)
    total = len(enriched)
    start = (page - 1) * page_size
    return paginated_response(enriched[start:start + page_size], page, page_size, total)


@leave_router.get("/requests/{request_id}")
def get_leave_request(request_id: str):
    r = leave_repo.find_request_by_id(request_id)
    if not r:
        raise HTTPException(status_code=404, detail=error_response("NOT_FOUND", f"Leave request {request_id} not found"))
    emp = emp_repo.find_by_id(r.get("employee_id", ""))
    t = leave_repo.find_type_by_id(r.get("time_off_type_id", ""))
    return success_response({**r, "employee": emp, "time_off_type": t})


@leave_router.post("/requests")
def create_leave_request(body: dict, current: dict = Depends(get_current_user)):
    employee_id = body.get("employee_id") or current.get("employee_id")
    if not role_at_least(current.get("role"), "HR"):
        employee_id = current.get("employee_id")
    if not employee_id:
        raise HTTPException(status_code=422, detail=error_response("VALIDATION_ERROR", "employee_id required"))
    if not body.get("start_date") or not body.get("end_date"):
        raise HTTPException(status_code=422, detail=error_response("VALIDATION_ERROR", "start_date and end_date are required"))
    if body["end_date"] < body["start_date"]:
        raise HTTPException(status_code=422, detail=error_response("VALIDATION_ERROR", "end_date must be after start_date"))

    start = date_type.fromisoformat(str(body["start_date"])[:10])
    end = date_type.fromisoformat(str(body["end_date"])[:10])
    duration = float(body.get("duration_days") or body.get("requested_units") or ((end - start).days + 1))
    if duration <= 0:
        raise HTTPException(status_code=422, detail=error_response("VALIDATION_ERROR", "duration_days must be > 0"))

    type_id = body.get("time_off_type_id") or body.get("leave_type_id")
    if not type_id:
        raise HTTPException(status_code=422, detail=error_response("VALIDATION_ERROR", "Leave type is required"))
    leave_type = leave_repo.find_type_by_id(type_id)
    if not leave_type:
        raise HTTPException(status_code=422, detail=error_response("VALIDATION_ERROR", "Invalid leave type"))
    allocations = leave_repo.find_allocations({"employee_id": employee_id})
    matching = next((a for a in allocations if a.get("time_off_type_id") == type_id), None)
    if matching and float(matching.get("remaining_units") or 0) < duration:
        raise HTTPException(status_code=422, detail=error_response(
            "INSUFFICIENT_LEAVE_BALANCE",
            f"Insufficient balance. Available: {matching.get('remaining_units')} days, Requested: {duration} days."))

    request = leave_repo.create_request({
        "employee_id": employee_id,
        "leave_type_id": type_id,
        "time_off_type_id": type_id,
        "allocation_id": matching["id"] if matching else None,
        "start_date": body["start_date"],
        "end_date": body["end_date"],
        "requested_units": duration,
        "duration_days": duration,
        "reason": body.get("reason") or body.get("message"),
        "status": "PENDING",
        "approved_by": None,
        "approved_at": None,
        "rejection_reason": None,
        "created_at": datetime.now(timezone.utc),
        "updated_at": datetime.now(timezone.utc),
    })
    notif_repo.create({
        "title": "New leave request",
        "message": f"{(current.get('employee') or {}).get('first_name', 'An employee')} requested {duration} day(s) of leave: {body.get('reason') or ''}",
        "type": "LEAVE",
        "priority": "NORMAL",
        "target_type": "ROLE",
        "target_id": None,
        "created_by": current.get("employee_id"),
        "is_active": True,
        "published_at": datetime.now(timezone.utc).isoformat(),
    })
    return success_response(request, "Leave request submitted")


@leave_router.put("/requests/{request_id}")
def update_leave_request(request_id: str, body: dict):
    r = leave_repo.find_request_by_id(request_id)
    if not r:
        raise HTTPException(status_code=404, detail=error_response("NOT_FOUND", f"Leave request {request_id} not found"))
    if r["status"] != "PENDING":
        raise HTTPException(status_code=409, detail=error_response("INVALID_STATE", "Only pending requests can be edited"))
    updated = leave_repo.update_request(request_id, body)
    return success_response(updated)


@leave_router.post("/requests/{request_id}/approve")
def approve_leave_request(request_id: str, body: dict = {}, current: dict = Depends(require_min_role("HR"))):
    r = leave_repo.find_request_by_id(request_id)
    if not r:
        raise HTTPException(status_code=404, detail=error_response("NOT_FOUND", f"Leave request {request_id} not found"))
    if r["status"] != "PENDING":
        raise HTTPException(status_code=409, detail=error_response("INVALID_STATE", f"Cannot approve request in status '{r['status']}'"))

    leave_type = leave_repo.find_type_by_id(r.get("time_off_type_id", ""))
    allocation_id = r.get("allocation_id")
    if leave_type and leave_type.get("requires_allocation") and allocation_id:
        alloc = leave_repo.find_allocation_by_id(allocation_id)
        if alloc:
            requested = float(r.get("duration_days", 0))
            remaining = float(alloc.get("remaining_units", 0))
            if remaining < requested:
                raise HTTPException(status_code=422, detail=error_response(
                    "INSUFFICIENT_LEAVE_BALANCE",
                    f"Insufficient balance. Available: {remaining} days, Requested: {requested} days."))
            leave_repo.update_allocation(allocation_id, {
                "used_units": float(alloc.get("used_units", 0)) + requested,
            })

    now = datetime.now(timezone.utc).isoformat()
    approver_id = (current.get("user") or {}).get("id") or current.get("sub")
    updated = leave_repo.update_request(request_id, {
        "status": "APPROVED",
        "approved_by": approver_id,
        "approved_at": now,
    })

    # Notify employee
    emp = emp_repo.find_by_id(r.get("employee_id", ""))
    if emp:
        notif_repo.create({
            "title": "Leave Request Approved",
            "message": f"Your leave request from {r.get('start_date')} to {r.get('end_date')} ({r.get('duration_days')} days) has been approved.",
            "type": "LEAVE",
            "priority": "NORMAL",
            "target_type": "EMPLOYEE",
            "target_id": emp["id"],
            "published_at": now,
            "expires_at": None,
            "is_active": True,
            "created_by": current.get("employee_id"),
        })

    audit_service.log("LEAVE_APPROVED", "LEAVE_REQUEST", request_id,
                      description=f"Leave approved for employee {r.get('employee_id')}")
    return success_response(updated, "Leave request approved")


@leave_router.post("/requests/{request_id}/reject")
def reject_leave_request(request_id: str, body: dict = {}, current: dict = Depends(require_min_role("HR"))):
    r = leave_repo.find_request_by_id(request_id)
    if not r:
        raise HTTPException(status_code=404, detail=error_response("NOT_FOUND", f"Leave request {request_id} not found"))
    if r["status"] != "PENDING":
        raise HTTPException(status_code=409, detail=error_response("INVALID_STATE", f"Cannot reject request in status '{r['status']}'"))

    now = datetime.now(timezone.utc).isoformat()
    updated = leave_repo.update_request(request_id, {
        "status": "REJECTED",
        "approved_by": (current.get("user") or {}).get("id") or current.get("sub"),
        "approved_at": now,
        "rejection_reason": body.get("reason") or body.get("rejection_reason") or "Rejected by HR",
    })

    # Notify employee
    emp = emp_repo.find_by_id(r.get("employee_id", ""))
    if emp:
        notif_repo.create({
            "title": "Leave Request Rejected",
            "message": f"Your leave request from {r.get('start_date')} to {r.get('end_date')} has been rejected. Reason: {body.get('reason', '')}",
            "type": "LEAVE",
            "priority": "NORMAL",
            "target_type": "EMPLOYEE",
            "target_id": emp["id"],
            "published_at": now,
            "expires_at": None,
            "is_active": True,
            "created_by": current.get("employee_id"),
        })

    audit_service.log("LEAVE_REJECTED", "LEAVE_REQUEST", request_id,
                      description=f"Leave rejected. Reason: {body.get('reason', '')}")
    return success_response(updated, "Leave request rejected")


@leave_router.post("/requests/{request_id}/cancel")
def cancel_leave_request(request_id: str, body: dict = {}):
    r = leave_repo.find_request_by_id(request_id)
    if not r:
        raise HTTPException(status_code=404, detail=error_response("NOT_FOUND", f"Leave request {request_id} not found"))
    if r["status"] not in ("PENDING", "APPROVED"):
        raise HTTPException(status_code=409, detail=error_response("INVALID_STATE", f"Cannot cancel request in status '{r['status']}'"))

    was_approved = r["status"] == "APPROVED"
    updated = leave_repo.update_request(request_id, {"status": "CANCELLED"})

    # Restore balance if was approved
    if was_approved and r.get("allocation_id"):
        alloc = leave_repo.find_allocation_by_id(r["allocation_id"])
        if alloc:
            restored = float(r.get("duration_days", 0))
            leave_repo.update_allocation(r["allocation_id"], {
                "used_units": max(0.0, float(alloc.get("used_units", 0)) - restored),
            })

    return success_response(updated, "Leave request cancelled")
