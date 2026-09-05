from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException

from app.repositories.postgres_repos import (
    PostgresNotificationRepository, PostgresEmployeeRepository, PostgresDepartmentRepository,
)
from app.core.response import success_response, error_response
from app.api.deps import get_current_user, require_min_role

router = APIRouter(prefix="/notifications", tags=["notifications"])
notif_repo = PostgresNotificationRepository()
emp_repo = PostgresEmployeeRepository()
dept_repo = PostgresDepartmentRepository()


@router.get("")
def list_notifications(current: dict = Depends(get_current_user)):
    employee = current.get("employee") or {}
    notifs = notif_repo.find_for_employee(employee, current.get("role"))
    return success_response(notifs)


@router.get("/inbox")
def my_inbox(current: dict = Depends(get_current_user)):
    employee = current.get("employee") or {}
    return success_response(notif_repo.find_for_employee(employee, current.get("role")))


@router.get("/{notif_id}")
def get_notification(notif_id: str, current: dict = Depends(get_current_user)):
    n = notif_repo.find_by_id(notif_id)
    if not n:
        raise HTTPException(status_code=404, detail=error_response("NOT_FOUND", f"Notification {notif_id} not found"))
    return success_response(n)


@router.post("")
@router.post("/")
def create_notification(body: dict, current: dict = Depends(require_min_role("HR"))):
    if not body.get("title") or not (body.get("message") or body.get("body")):
        raise HTTPException(status_code=422, detail=error_response("VALIDATION_ERROR", "title and message are required"))
    target_type = (body.get("target_type") or "ALL").upper()
    if target_type not in ("ALL", "ALL_EMPLOYEES", "ROLE", "DEPARTMENT", "EMPLOYEE"):
        raise HTTPException(status_code=422, detail=error_response("VALIDATION_ERROR", "Invalid target_type"))
    notif = notif_repo.create({
        "title": body["title"],
        "message": body.get("message") or body.get("body"),
        "type": body.get("type") or "ANNOUNCEMENT",
        "priority": body.get("priority") or "NORMAL",
        "target_type": target_type,
        "target_id": body.get("target_id") or None,
        "created_by": current.get("employee_id") or current.get("user_id") or None,
        "is_active": True,
        "published_at": datetime.now(timezone.utc).isoformat(),
    })
    return success_response(notif, "Notification sent")


@router.post("/{notif_id}/read")
def mark_read(notif_id: str, current: dict = Depends(get_current_user)):
    if current.get("employee_id"):
        notif_repo.mark_read(notif_id, current["employee_id"])
    return success_response(True, "Marked read")


@router.delete("/{notif_id}")
def deactivate_notification(notif_id: str, current: dict = Depends(require_min_role("HR"))):
    n = notif_repo.find_by_id(notif_id)
    if not n:
        raise HTTPException(status_code=404, detail=error_response("NOT_FOUND", f"Notification {notif_id} not found"))
    return success_response(notif_repo.update(notif_id, {"is_active": False}), "Notification deactivated")
