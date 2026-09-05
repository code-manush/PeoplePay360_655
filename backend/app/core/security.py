from datetime import datetime, timedelta, timezone
from typing import Optional
import bcrypt
import jwt

from app.core.config import settings

ROLE_RANK = {"EMPLOYEE": 1, "HR": 2, "ADMIN": 3}
DB_ROLE_TO_APP = {
    "ADMIN": "ADMIN",
    "HR_MANAGER": "HR",
    "HR_PAYROLL_USER": "HR",
    "HR_PAYROLL_MANAGER": "HR",
    "EMPLOYEE": "EMPLOYEE",
}


def normalize_app_role(db_roles: list[str]) -> str:
    mapped = [DB_ROLE_TO_APP.get(str(r).strip().upper(), "EMPLOYEE") for r in (db_roles or [])]
    if not mapped:
        return "EMPLOYEE"
    return max(mapped, key=lambda r: ROLE_RANK.get(r, 0))


def role_at_least(role: str, required: str) -> bool:
    return ROLE_RANK.get(str(role or "EMPLOYEE").strip().upper(), 0) >= ROLE_RANK.get(str(required or "EMPLOYEE").strip().upper(), 0)


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def verify_password(password: str, password_hash: str) -> bool:
    if not password_hash:
        return False
    if password_hash.startswith("$2b$12$DEMO_PASSWORD_HASH"):
        return password == settings.DEMO_PASSWORD
    try:
        return bcrypt.checkpw(password.encode("utf-8"), password_hash.encode("utf-8"))
    except ValueError:
        return password == settings.DEMO_PASSWORD and "DEMO_PASSWORD" in password_hash


def create_access_token(payload: dict, expires_minutes: Optional[int] = None) -> str:
    data = dict(payload)
    expire = datetime.now(timezone.utc) + timedelta(
        minutes=expires_minutes or settings.JWT_EXPIRE_MINUTES
    )
    data["exp"] = expire
    data["sub"] = str(data.get("sub") or "")
    return jwt.encode(data, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM)


def decode_access_token(token: str) -> dict:
    return jwt.decode(token, settings.JWT_SECRET, algorithms=[settings.JWT_ALGORITHM])
