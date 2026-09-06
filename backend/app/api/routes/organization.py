from fastapi import APIRouter, HTTPException, Depends
from app.repositories.postgres_repos import PostgresDepartmentRepository, PostgresJobPositionRepository
from app.core.response import success_response, error_response
from app.api.deps import get_current_user

dept_router = APIRouter(prefix="/departments", tags=["departments"])
pos_router = APIRouter(prefix="/job-positions", tags=["job-positions"])

dept_repo = PostgresDepartmentRepository()
pos_repo = PostgresJobPositionRepository()


@dept_router.get("")
def list_departments(current: dict = Depends(get_current_user)):
    depts = dept_repo.find_all()
    return success_response(depts)


@dept_router.get("/{dept_id}")
def get_department(dept_id: str):
    dept = dept_repo.find_by_id(dept_id)
    if not dept:
        raise HTTPException(status_code=404, detail=error_response("NOT_FOUND", f"Department {dept_id} not found"))
    return success_response(dept)


@dept_router.post("")
def create_department(body: dict):
    if not body.get("name"):
        raise HTTPException(status_code=422, detail=error_response("VALIDATION_ERROR", "Name is required", "name"))
    payload = {**body, "is_active": True}
    if not payload.get("code"):
        payload["code"] = str(body.get("name") or "DEPT").upper().replace(" ", "_")[:30]
    dept = dept_repo.create(payload)
    return success_response(dept, "Department created")


@dept_router.put("/{dept_id}")
def update_department(dept_id: str, body: dict):
    dept = dept_repo.find_by_id(dept_id)
    if not dept:
        raise HTTPException(status_code=404, detail=error_response("NOT_FOUND", f"Department {dept_id} not found"))
    return success_response(dept_repo.update(dept_id, body))


@dept_router.delete("/{dept_id}")
def delete_department(dept_id: str):
    if not dept_repo.delete(dept_id):
        raise HTTPException(status_code=404, detail=error_response("NOT_FOUND", f"Department {dept_id} not found"))
    return success_response(None, "Department deleted")


@pos_router.get("")
def list_positions(department_id: str = None, current: dict = Depends(get_current_user)):
    filters = {}
    if department_id:
        filters["department_id"] = department_id
    return success_response(pos_repo.find_all(filters))


@pos_router.get("/{pos_id}")
def get_position(pos_id: str):
    pos = pos_repo.find_by_id(pos_id)
    if not pos:
        raise HTTPException(status_code=404, detail=error_response("NOT_FOUND", f"Position {pos_id} not found"))
    return success_response(pos)


@pos_router.post("")
def create_position(body: dict):
    if not body.get("title") and not body.get("name"):
        raise HTTPException(status_code=422, detail=error_response("VALIDATION_ERROR", "Title is required", "title"))
    pos = pos_repo.create({**body, "name": body.get("name") or body.get("title"), "is_active": True})
    return success_response(pos, "Position created")


@pos_router.put("/{pos_id}")
def update_position(pos_id: str, body: dict):
    pos = pos_repo.find_by_id(pos_id)
    if not pos:
        raise HTTPException(status_code=404, detail=error_response("NOT_FOUND", f"Position {pos_id} not found"))
    return success_response(pos_repo.update(pos_id, body))


@pos_router.delete("/{pos_id}")
def delete_position(pos_id: str):
    if not pos_repo.delete(pos_id):
        raise HTTPException(status_code=404, detail=error_response("NOT_FOUND", f"Position {pos_id} not found"))
    return success_response(None, "Position deleted")
