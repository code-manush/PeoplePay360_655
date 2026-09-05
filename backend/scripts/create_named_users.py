"""Create the three named PeoplePay360 logins."""
import os
import sys
from datetime import datetime, timezone

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.core.database import SessionLocal
from app.core.security import hash_password
from app.models.domain import User, Role, UserRole, Employee, Department, JobPosition
import uuid

USERS = [
    {"email": "anmolkj006@gmail.com", "password": "Anmol@Pay360", "role": "ADMIN", "first_name": "Anmol", "last_name": "Kumar"},
    {"email": "manushpatel1002@gmail.com", "password": "Manush@Pay360", "role": "EMPLOYEE", "first_name": "Manush", "last_name": "Patel"},
    {"email": "gauriborse1808@gmail.com", "password": "Gauri@Pay360", "role": "HR_MANAGER", "first_name": "Gauri", "last_name": "Borse"},
]


def upsert_user(db, spec, department_id, position_id):
    now = datetime.now(timezone.utc)
    user = db.query(User).filter(User.email.ilike(spec["email"])).first()
    if not user:
        user = User(
            id=str(uuid.uuid4()),
            email=spec["email"],
            password_hash=hash_password(spec["password"]),
            status="ACTIVE",
            created_at=now,
            updated_at=now,
        )
        db.add(user)
        db.flush()
    else:
        user.password_hash = hash_password(spec["password"])
        user.status = "ACTIVE"
        user.updated_at = now

    role = db.query(Role).filter(Role.name == spec["role"]).first()
    if spec["role"] != "EMPLOYEE":
        emp_role = db.query(Role).filter(Role.name == "EMPLOYEE").first()
        roles = [r for r in [role, emp_role] if r]
    else:
        roles = [role] if role else []

    for r in roles:
        exists = db.query(UserRole).filter(UserRole.user_id == user.id, UserRole.role_id == r.id).first()
        if not exists:
            db.add(UserRole(user_id=user.id, role_id=r.id, assigned_at=now))

    emp = db.query(Employee).filter(Employee.user_id == user.id).first()
    if not emp:
        emp = db.query(Employee).filter(Employee.email.ilike(spec["email"])).first()
        if not emp:
            codes = [r[0] for r in db.query(Employee.employee_code).all() if r[0]]
            nums = []
            for c in codes:
                digits = "".join(ch for ch in c if ch.isdigit())
                if digits:
                    nums.append(int(digits))
            nxt = (max(nums) + 1) if nums else 1
            emp = Employee(
                id=str(uuid.uuid4()),
                user_id=user.id,
                employee_code=f"EMP{nxt:04d}",
                first_name=spec["first_name"],
                last_name=spec["last_name"],
                email=spec["email"],
                joining_date=now.date(),
                department_id=department_id,
                job_position_id=position_id,
                employment_type="FULL_TIME",
                status="ACTIVE",
                created_at=now,
                updated_at=now,
            )
            db.add(emp)
            db.flush()
    else:
        emp.user_id = user.id
        emp.email = spec["email"]
        emp.status = "ACTIVE"
        emp.updated_at = now
    return user.email, spec["password"], spec["role"]


def main():
    db = SessionLocal()
    try:
        dept = db.query(Department).first()
        pos = db.query(JobPosition).first()
        created = []
        for spec in USERS:
            created.append(upsert_user(db, spec, dept.id if dept else None, pos.id if pos else None))
        db.commit()
        print("Created/updated logins:")
        for email, password, role in created:
            print(f"  {email}  role={role}  password={password}")
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    main()
