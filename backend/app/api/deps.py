from typing import Optional
from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
import jwt

from app.core.security import decode_access_token, role_at_least, normalize_app_role, ROLE_RANK
from app.core.response import error_response
from app.repositories.postgres_repos import PostgresUserRepository, PostgresEmployeeRepository

bearer = HTTPBearer(auto_error=False)
user_repo = PostgresUserRepository()
emp_repo = PostgresEmployeeRepository()


def get_current_user(credentials: Optional[HTTPAuthorizationCredentials] = Depends(bearer)) -> dict:
    if not credentials:
        raise HTTPException(status_code=401, detail=error_response("UNAUTHORIZED", "Missing access token"))
    try:
        payload = decode_access_token(credentials.credentials)
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail=error_response("TOKEN_EXPIRED", "Session expired. Please sign in again."))
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail=error_response("INVALID_TOKEN", "Invalid access token"))
    user = user_repo.find_by_id(payload.get("sub"))
    if not user or user.get("status") != "ACTIVE":
        raise HTTPException(status_code=401, detail=error_response("UNAUTHORIZED", "Account is not active"))
    employee = emp_repo.find_by_id(payload.get("employee_id")) if payload.get("employee_id") else emp_repo.find_by_user_id(user["id"])
    db_roles = user_repo.get_role_names(user["id"])
    token_roles = [payload.get("role"), *(payload.get("roles") or [])]
    jwt_role = normalize_app_role([r for r in token_roles if r])
    db_role = normalize_app_role(db_roles)
    app_role = max((jwt_role, db_role), key=lambda r: ROLE_RANK.get(r, 0))
    return {
        "sub": user["id"],
        "email": user.get("email"),
        "roles": db_roles,
        "user": user,
        "employee": employee,
        "role": app_role,
        "user_id": user["id"],
        "employee_id": employee["id"] if employee else None,
    }


def require_role(*roles: str):
    def checker(current: dict = Depends(get_current_user)) -> dict:
        if current.get("role") not in roles and not any(role_at_least(current.get("role"), r) for r in roles if r == "HR"):
            if current.get("role") not in roles:
                raise HTTPException(status_code=403, detail=error_response("FORBIDDEN", "You do not have access to this action"))
        return current
    return checker


def require_min_role(minimum: str):
    def checker(current: dict = Depends(get_current_user)) -> dict:
        if not role_at_least(current.get("role"), minimum):
            raise HTTPException(status_code=403, detail=error_response("FORBIDDEN", "Insufficient role"))
        return current
    return checker
