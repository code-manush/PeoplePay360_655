import os
import sys
import json
from pathlib import Path

from sqlalchemy import text

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.core.database import engine, Base, SessionLocal
from app.models.domain import (  # noqa: F401 — register all models on Base
    Employee, Department, JobPosition, Contract, AttendanceRecord,
    LeaveRequest, LeaveAllocation, TimeOffType, Payrun, Payslip,
    Notification, WorkingSchedule, WorkingScheduleDay, EmployeeBankAccount,
    SalaryStructure, SalaryRule, SalaryRuleVersion, PayrunEmployee,
    PayslipLine, PayrollWarning, Payment, PayslipDelivery, AuditLog,
)

DATA_DIR = Path(__file__).parent.parent / "app" / "data"

SEED_PLAN = [
    ("departments.json", Department, {"manager_id": None, "parent_id": None}),
    ("job_positions.json", JobPosition, None),
    ("employees.json", Employee, {"manager_id": None}),
    ("working_schedules.json", WorkingSchedule, None),
    ("working_schedule_days.json", WorkingScheduleDay, None),
    ("salary_structures.json", SalaryStructure, None),
    ("salary_rules.json", SalaryRule, None),
    ("salary_rule_versions.json", SalaryRuleVersion, None),
    ("employee_bank_accounts.json", EmployeeBankAccount, None),
    ("contracts.json", Contract, None),
    ("time_off_types.json", TimeOffType, None),
    ("leave_allocations.json", LeaveAllocation, None),
    ("leave_requests.json", LeaveRequest, None),
    ("attendance_records.json", AttendanceRecord, None),
    ("payruns.json", Payrun, None),
    ("payrun_employees.json", PayrunEmployee, None),
    ("payslips.json", Payslip, None),
    ("payslip_lines.json", PayslipLine, None),
    ("payroll_warnings.json", PayrollWarning, None),
    ("payments.json", Payment, None),
    ("payslip_deliveries.json", PayslipDelivery, None),
    ("notifications.json", Notification, None),
    ("audit_logs.json", AuditLog, None),
]


def load_json(filename):
    path = DATA_DIR / filename
    if not path.exists():
        print(f"Warning: {filename} not found.")
        return []
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def clean_dict(data, model):
    valid_keys = [c.key for c in model.__table__.columns]
    cleaned = {k: v for k, v in data.items() if k in valid_keys}
    if model is AuditLog and "metadata" in data and "event_metadata" in valid_keys:
        cleaned["event_metadata"] = data.get("metadata")
    return cleaned


def drop_public_tables():
    print("Dropping existing public tables...")
    with engine.connect() as conn:
        rows = conn.execute(text(
            "SELECT tablename FROM pg_tables WHERE schemaname = 'public'"
        )).fetchall()
        for (name,) in rows:
            conn.execute(text(f'DROP TABLE IF EXISTS "{name}" CASCADE'))
        conn.commit()


def seed():
    drop_public_tables()
    print("Creating tables from PeoplePay360 schema...")
    Base.metadata.create_all(bind=engine)

    db = SessionLocal()
    try:
        for filename, model, overrides in SEED_PLAN:
            items = load_json(filename)
            print(f"Seeding {len(items)} {model.__tablename__}...")
            for item in items:
                clean = clean_dict(item, model)
                if overrides:
                    clean.update(overrides)
                if model is Contract:
                    clean["base_salary"] = item.get("base_salary", item.get("wage"))
                    clean["contract_type"] = item.get("contract_type") or item.get("employment_type")
                    clean.setdefault("wage_type", "MONTHLY")
                if model is Notification:
                    clean.setdefault("body", item.get("message"))
                    clean.setdefault("is_active", item.get("is_active", True))
                db.add(model(**clean))
            db.commit()

        # Restore department managers now that employees exist
        departments = load_json("departments.json")
        for item in departments:
            if item.get("manager_id"):
                dept = db.query(Department).filter(Department.id == item["id"]).first()
                if dept:
                    dept.manager_id = item["manager_id"]
        db.commit()

        employees = load_json("employees.json")
        for item in employees:
            if item.get("manager_id"):
                emp = db.query(Employee).filter(Employee.id == item["id"]).first()
                if emp:
                    emp.manager_id = item["manager_id"]
        db.commit()

        print("Database seeded successfully!")
    except Exception as e:
        db.rollback()
        print(f"Error seeding database: {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    seed()
