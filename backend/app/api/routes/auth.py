from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException

from app.core.response import success_response, error_response
from app.core.security import (
    verify_password, create_access_token, normalize_app_role, hash_password,
)
from app.core.config import settings
from app.repositories.postgres_repos import PostgresUserRepository, PostgresEmployeeRepository, PostgresLeaveRepository
from app.api.deps import get_current_user

router = APIRouter(prefix="/auth", tags=["auth"])
user_repo = PostgresUserRepository()
emp_repo = PostgresEmployeeRepository()
leave_repo = PostgresLeaveRepository()


@router.post("/login")
def login(body: dict):
    email = (body.get("email") or "").strip()
    password = body.get("password") or ""
    if not email or not password:
        raise HTTPException(status_code=422, detail=error_response("VALIDATION_ERROR", "Email and password are required"))

    user = user_repo.find_by_email(email)
    if not user or not verify_password(password, user.get("password_hash") or ""):
        raise HTTPException(status_code=401, detail=error_response("INVALID_CREDENTIALS", "Invalid email or password"))
    if user.get("status") != "ACTIVE":
        raise HTTPException(status_code=403, detail=error_response("ACCOUNT_INACTIVE", "This account is inactive"))

    if (user.get("password_hash") or "").startswith("$2b$12$DEMO_PASSWORD_HASH"):
        user_repo.update_password_hash(user["id"], hash_password(password))

    db_roles = user_repo.get_role_names(user["id"])
    app_role = normalize_app_role(db_roles)
    employee = emp_repo.find_by_user_id(user["id"])
    user_repo.update_last_login(user["id"])

    token = create_access_token({
        "sub": user["id"],
        "email": user["email"],
        "role": app_role,
        "roles": db_roles,
        "employee_id": employee["id"] if employee else None,
    })
    return success_response({
        "token": token,
        "token_type": "bearer",
        "role": app_role,
        "roles": db_roles,
        "user": {"id": user["id"], "email": user["email"], "status": user["status"]},
        "employee": employee,
        "expires_minutes": settings.JWT_EXPIRE_MINUTES,
    }, "Signed in")
@router.post("/register")
def register(body: dict):
    email = (body.get("email") or "").strip()
    password = body.get("password") or ""
    first_name = body.get("first_name") or ""
    last_name = body.get("last_name") or ""
    
    if not email or not password or not first_name or not last_name:
        raise HTTPException(status_code=422, detail=error_response("VALIDATION_ERROR", "Email, password, first name and last name are required"))

    try:
        user = user_repo.create_login_account(email, password, "EMPLOYEE")
        
        # Also create a basic employee record for the user
        emp_data = {
            "user_id": user["id"],
            "first_name": first_name,
            "last_name": last_name,
            "email": email,
            "employee_code": emp_repo.next_employee_code(),
            "status": "ACTIVE",
            "employment_type": "FULL_TIME",
            "joining_date": datetime.now(timezone.utc).date()
        }
        employee = emp_repo.create(emp_data)
        leave_repo.ensure_default_allocations(employee["id"])
        
        return success_response({
            "user": user,
            "employee": employee
        }, "Registered successfully")
    except ValueError as e:
        raise HTTPException(status_code=400, detail=error_response("REGISTRATION_ERROR", str(e)))


@router.get("/me")
def me(current: dict = Depends(get_current_user)):
    return success_response({
        "role": current.get("role"),
        "roles": current.get("roles") or [],
        "user": current.get("user"),
        "employee": current.get("employee"),
    })


@router.get("/demo-accounts")
def demo_accounts():
    return success_response([
        {"role": "ADMIN", "email": "anmolkj006@gmail.com", "password": "Anmol@Pay360", "name": "Anmol Kumar"},
        {"role": "HR", "email": "gauriborse1808@gmail.com", "password": "Gauri@Pay360", "name": "Gauri Borse"},
        {"role": "EMPLOYEE", "email": "manushpatel1002@gmail.com", "password": "Manush@Pay360", "name": "Manush Patel"},
        {"role": "ADMIN", "email": "employee0001@peoplepay360.demo", "password": settings.DEMO_PASSWORD, "name": "Employee1 Demo"},
        {"role": "HR", "email": "employee0002@peoplepay360.demo", "password": settings.DEMO_PASSWORD, "name": "Employee2 Demo"},
        {"role": "EMPLOYEE", "email": "employee0005@peoplepay360.demo", "password": settings.DEMO_PASSWORD, "name": "Employee5 Demo"},
    ])
