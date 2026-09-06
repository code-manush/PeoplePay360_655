from typing import Dict, Any, List, Optional
from datetime import date, datetime, timezone, time as time_type, timedelta
from decimal import Decimal
import uuid

from app.repositories.base import BaseRepository
from app.core.database import SessionLocal
from app.core.security import hash_password
from app.models.domain import (
    Employee, Department, JobPosition, Contract, AttendanceRecord,
    LeaveRequest, LeaveAllocation, LeaveType, Payrun, Payslip,
    Notification, NotificationRead, User, Role, UserRole, SalaryStructure,
    SalaryRule, SalaryRuleVersion, SalaryStructureRule, PayrunEmployee, PayslipLine, PayrollWarning, Payment,
    AuditLog, Schedule, EmployeeSchedule, EmploymentHistory, PayrunStatusHistory,
    PayslipCalculationTrace, PayslipDelivery, PayslipInput, PayslipSnapshot, PayslipWorkedDays,
)

WEEKDAYS = [
    ("monday", "MONDAY"),
    ("tuesday", "TUESDAY"),
    ("wednesday", "WEDNESDAY"),
    ("thursday", "THURSDAY"),
    ("friday", "FRIDAY"),
    ("saturday", "SATURDAY"),
    ("sunday", "SUNDAY"),
]
DEFAULT_LEAVE_UNITS = {
    "ANNUAL": 24, "SICK": 12, "CASUAL": 8, "MATERNITY": 182, "LWP": 30, "COMP_OFF": 12,
}


def _serialize(value):
    if isinstance(value, datetime):
        return value.isoformat()
    if isinstance(value, date):
        return value.isoformat()
    if isinstance(value, time_type):
        return value.strftime("%H:%M:%S")
    if isinstance(value, Decimal):
        return float(value)
    if isinstance(value, uuid.UUID):
        return str(value)
    return value


def _hours_between(start, end) -> float:
    if not start or not end:
        return 0.0
    try:
        if isinstance(start, str):
            start = datetime.strptime(start[:8], "%H:%M:%S" if len(start) >= 8 else "%H:%M").time()
        if isinstance(end, str):
            end = datetime.strptime(end[:8], "%H:%M:%S" if len(end) >= 8 else "%H:%M").time()
        s = datetime.combine(date.today(), start)
        e = datetime.combine(date.today(), end)
        return max(0.0, (e - s).total_seconds() / 3600.0)
    except Exception:
        return 0.0


def schedule_to_days(schedule: Optional[Dict[str, Any]]) -> List[Dict[str, Any]]:
    if not schedule:
        return []
    days = []
    for key, label in WEEKDAYS:
        start = schedule.get(f"{key}_start")
        end = schedule.get(f"{key}_end")
        working = bool(start and end)
        days.append({
            "day_of_week": label,
            "is_working": working,
            "start_time": start,
            "end_time": end,
            "expected_hours": round(_hours_between(start, end), 2) if working else 0.0,
        })
    return days


def default_weekday_days() -> List[Dict[str, Any]]:
    days = []
    for _, label in WEEKDAYS:
        working = label not in ("SATURDAY", "SUNDAY")
        days.append({
            "day_of_week": label,
            "is_working": working,
            "start_time": "09:00:00" if working else None,
            "end_time": "18:00:00" if working else None,
            "expected_hours": 9.0 if working else 0.0,
        })
    return days


def days_to_schedule_columns(days: List[Dict[str, Any]]) -> Dict[str, Any]:
    payload = {}
    by_label = {d.get("day_of_week"): d for d in days}
    for key, label in WEEKDAYS:
        day = by_label.get(label) or {}
        if day.get("is_working"):
            payload[f"{key}_start"] = day.get("start_time") or "09:00:00"
            payload[f"{key}_end"] = day.get("end_time") or "18:00:00"
        else:
            payload[f"{key}_start"] = None
            payload[f"{key}_end"] = None
    return payload


def _looks_uuid(value) -> bool:
    try:
        uuid.UUID(str(value))
        return True
    except Exception:
        return False


def _as_date(value):
    if value is None or value == "":
        return None
    if isinstance(value, date) and not isinstance(value, datetime):
        return value
    return date.fromisoformat(str(value)[:10])


class PostgresBaseRepository(BaseRepository):
    def __init__(self, model):
        self.model = model

    def _dict(self, obj):
        if obj is None:
            return None
        data = {c.name: _serialize(getattr(obj, c.name)) for c in obj.__table__.columns}
        return self._map(data)

    def _map(self, data: Dict[str, Any]) -> Dict[str, Any]:
        if self.model is Employee:
            data["date_joined"] = data.get("joining_date")
            data["employment_status"] = data.get("status")
            data["is_active"] = data.get("status") == "ACTIVE"
        if self.model is Department:
            data["manager_id"] = data.get("manager_employee_id")
            data["is_active"] = True
        if self.model is JobPosition:
            data["title"] = data.get("name")
            data["is_active"] = True
        if self.model is Schedule:
            data["days"] = schedule_to_days(data)
        if self.model is Contract:
            data["wage"] = data.get("basic_salary")
            data["base_salary"] = data.get("basic_salary")
            data["wage_type"] = "MONTHLY"
            data["employment_type"] = data.get("contract_type")
            data["is_active"] = data.get("status") == "ACTIVE"
        if self.model is AttendanceRecord:
            data["date"] = data.get("attendance_date")
        if self.model is LeaveType:
            data["requires_allocation"] = True
            data["is_active"] = True
        if self.model is LeaveAllocation:
            data["time_off_type_id"] = data.get("leave_type_id")
            data["year"] = int(str(data.get("allocation_period_start") or "2026")[:4])
        if self.model is LeaveRequest:
            data["time_off_type_id"] = data.get("leave_type_id")
            data["duration_days"] = data.get("requested_units")
        if self.model is Payrun:
            data["name"] = data.get("run_number")
            data["total_employees"] = data.get("employee_count")
        if self.model is Payslip:
            data["gross"] = data.get("gross_salary")
            data["net"] = data.get("net_salary")
        if self.model is Notification:
            data["body"] = data.get("message")
        if self.model is PayslipLine:
            data["computed_amount"] = data.get("amount")
            data["percentage"] = data.get("rate")
        if self.model is PayrollWarning:
            data["code"] = data.get("warning_code")
        return data

    def _model_kwargs(self, data: Dict[str, Any]) -> Dict[str, Any]:
        incoming = dict(data)
        if self.model is Employee:
            if "date_joined" in incoming and "joining_date" not in incoming:
                incoming["joining_date"] = incoming["date_joined"]
            if "employment_status" in incoming and "status" not in incoming:
                incoming["status"] = incoming["employment_status"]
        if self.model is JobPosition:
            if "title" in incoming and "name" not in incoming:
                incoming["name"] = incoming["title"]
        if self.model is Contract:
            if "wage" in incoming and "basic_salary" not in incoming:
                incoming["basic_salary"] = incoming["wage"]
            if "base_salary" in incoming and "basic_salary" not in incoming:
                incoming["basic_salary"] = incoming["base_salary"]
        if self.model is Payrun:
            if "total_employees" in incoming and "employee_count" not in incoming:
                incoming["employee_count"] = incoming["total_employees"]
            if "computed_at" in incoming and "started_at" not in incoming:
                incoming["started_at"] = incoming["computed_at"]
            if "validated_at" in incoming:
                incoming.pop("validated_at", None)
        if self.model is Payslip:
            if "gross" in incoming and "gross_salary" not in incoming:
                incoming["gross_salary"] = incoming["gross"]
            if "net" in incoming and "net_salary" not in incoming:
                incoming["net_salary"] = incoming["net"]
        if self.model is PayslipLine:
            if "rule_id" in incoming and "salary_rule_id" not in incoming:
                incoming["salary_rule_id"] = incoming["rule_id"]
            if "computed_amount" in incoming and "amount" not in incoming:
                incoming["amount"] = incoming["computed_amount"]
            if "percentage" in incoming and "rate" not in incoming:
                incoming["rate"] = incoming["percentage"]
            if "formula" in incoming and "calculation_expression" not in incoming:
                incoming["calculation_expression"] = incoming["formula"]
        if self.model is PayrollWarning:
            if "code" in incoming and "warning_code" not in incoming:
                incoming["warning_code"] = incoming["code"]
            resolved_by = incoming.get("resolved_by")
            if resolved_by and not _looks_uuid(resolved_by):
                incoming["resolved_by"] = None
        if self.model is AttendanceRecord:
            if "date" in incoming and "attendance_date" not in incoming:
                incoming["attendance_date"] = incoming["date"]
        if self.model is LeaveRequest:
            if "time_off_type_id" in incoming and "leave_type_id" not in incoming:
                incoming["leave_type_id"] = incoming["time_off_type_id"]
            if "duration_days" in incoming and "requested_units" not in incoming:
                incoming["requested_units"] = incoming["duration_days"]
        if self.model is LeaveAllocation:
            if "time_off_type_id" in incoming and "leave_type_id" not in incoming:
                incoming["leave_type_id"] = incoming["time_off_type_id"]
            incoming.pop("remaining_units", None)
        if self.model is Notification:
            if "body" in incoming and "message" not in incoming:
                incoming["message"] = incoming["body"]

        valid = {c.key for c in self.model.__table__.columns}
        cleaned = {}
        for k, v in incoming.items():
            if k not in valid:
                continue
            col = self.model.__table__.columns[k]
            if v == "":
                v = None
            type_name = str(col.type).upper()
            if v is not None and type_name.startswith("DATE") and "TIME" not in type_name:
                v = _as_date(v)
            if v is not None and "TIME" in type_name and "DATE" not in type_name and "STAMP" not in type_name and isinstance(v, str):
                parts = v.split(":")
                v = time_type(int(parts[0]), int(parts[1]), int(float(parts[2])) if len(parts) > 2 else 0)
            cleaned[k] = v
        return cleaned

    def find_all(self, filters: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        db = SessionLocal()
        try:
            query = db.query(self.model)
            extra = {"search", "date_from", "date_to", "date"}
            if filters:
                for k, v in filters.items():
                    if k in extra or v is None:
                        continue
                    attr = k
                    if self.model is LeaveRequest and k == "time_off_type_id":
                        attr = "leave_type_id"
                    if self.model is LeaveAllocation and k == "time_off_type_id":
                        attr = "leave_type_id"
                    if self.model is Employee and k == "employment_status":
                        attr = "status"
                    if self.model is Employee and k == "is_active":
                        query = query.filter(self.model.status == ("ACTIVE" if v else "INACTIVE"))
                        continue
                    if hasattr(self.model, attr):
                        query = query.filter(getattr(self.model, attr) == v)
                if self.model is AttendanceRecord:
                    if filters.get("date"):
                        query = query.filter(self.model.attendance_date == _as_date(filters["date"]))
                    if filters.get("date_from"):
                        query = query.filter(self.model.attendance_date >= _as_date(filters["date_from"]))
                    if filters.get("date_to"):
                        query = query.filter(self.model.attendance_date <= _as_date(filters["date_to"]))
            return [self._dict(r) for r in query.all()]
        finally:
            db.close()

    def find_by_id(self, id: str) -> Optional[Dict[str, Any]]:
        db = SessionLocal()
        try:
            result = db.query(self.model).filter(self.model.id == id).first()
            return self._dict(result)
        finally:
            db.close()

    def create(self, data: Dict[str, Any]) -> Dict[str, Any]:
        payload = dict(data)
        if not payload.get("id"):
            payload["id"] = str(uuid.uuid4())
        now = datetime.now(timezone.utc)
        if "created_at" not in payload or not payload.get("created_at"):
            payload["created_at"] = now
        if hasattr(self.model, "updated_at") and not payload.get("updated_at"):
            payload["updated_at"] = now
        db = SessionLocal()
        try:
            obj = self.model(**self._model_kwargs(payload))
            db.add(obj)
            db.commit()
            db.refresh(obj)
            return self._dict(obj)
        except Exception:
            db.rollback()
            raise
        finally:
            db.close()

    def update(self, id: str, data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        db = SessionLocal()
        try:
            obj = db.query(self.model).filter(self.model.id == id).first()
            if not obj:
                return None
            for k, v in self._model_kwargs(data).items():
                setattr(obj, k, v)
            if hasattr(obj, "updated_at"):
                obj.updated_at = datetime.now(timezone.utc)
            db.commit()
            db.refresh(obj)
            return self._dict(obj)
        except Exception:
            db.rollback()
            raise
        finally:
            db.close()

    def delete(self, id: str) -> bool:
        db = SessionLocal()
        try:
            obj = db.query(self.model).filter(self.model.id == id).first()
            if not obj:
                return False
            db.delete(obj)
            db.commit()
            return True
        except Exception:
            db.rollback()
            raise
        finally:
            db.close()


class PostgresEmployeeRepository(PostgresBaseRepository):
    def __init__(self):
        super().__init__(Employee)

    def find_all(self, filters: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        db = SessionLocal()
        try:
            query = db.query(self.model)
            if filters:
                if filters.get("search"):
                    search = f"%{filters['search']}%"
                    query = query.filter(
                        (self.model.first_name.ilike(search))
                        | (self.model.last_name.ilike(search))
                        | (self.model.employee_code.ilike(search))
                        | (self.model.email.ilike(search))
                    )
                for k, attr in [
                    ("department_id", "department_id"),
                    ("employment_type", "employment_type"),
                    ("employment_status", "status"),
                    ("manager_id", "manager_id"),
                ]:
                    if filters.get(k) is not None:
                        query = query.filter(getattr(self.model, attr) == filters[k])
                if filters.get("is_active") is not None:
                    query = query.filter(self.model.status == ("ACTIVE" if filters["is_active"] else "INACTIVE"))
            return [self._dict(r) for r in query.all()]
        finally:
            db.close()

    def find_by_user_id(self, user_id: str) -> Optional[Dict[str, Any]]:
        db = SessionLocal()
        try:
            result = db.query(self.model).filter(self.model.user_id == user_id).first()
            return self._dict(result)
        finally:
            db.close()

    def next_employee_code(self) -> str:
        db = SessionLocal()
        try:
            codes = [r[0] for r in db.query(self.model.employee_code).all() if r[0]]
            nums = []
            for c in codes:
                digits = "".join(ch for ch in c if ch.isdigit())
                if digits:
                    nums.append(int(digits))
            nxt = (max(nums) + 1) if nums else 1
            return f"EMP{nxt:04d}"
        finally:
            db.close()


class PostgresDepartmentRepository(PostgresBaseRepository):
    def __init__(self):
        super().__init__(Department)


class PostgresJobPositionRepository(PostgresBaseRepository):
    def __init__(self):
        super().__init__(JobPosition)


class PostgresContractRepository(PostgresBaseRepository):
    def __init__(self):
        super().__init__(Contract)


class PostgresAttendanceRepository(PostgresBaseRepository):
    def __init__(self):
        super().__init__(AttendanceRecord)

    def find_active(self) -> List[Dict[str, Any]]:
        db = SessionLocal()
        try:
            results = (
                db.query(self.model)
                .filter(self.model.check_in.isnot(None), self.model.check_out.is_(None))
                .all()
            )
            return [self._dict(r) for r in results]
        finally:
            db.close()

    def employee_ids_in_range(self, date_from: str, date_to: str, limit: Optional[int] = None) -> List[str]:
        db = SessionLocal()
        try:
            from sqlalchemy import func
            query = (
                db.query(AttendanceRecord.employee_id, func.count(AttendanceRecord.id).label("n"))
                .filter(
                    AttendanceRecord.attendance_date >= _as_date(date_from),
                    AttendanceRecord.attendance_date <= _as_date(date_to),
                )
                .group_by(AttendanceRecord.employee_id)
                .order_by(func.count(AttendanceRecord.id).desc())
            )
            if limit:
                query = query.limit(int(limit))
            return [str(r[0]) for r in query.all() if r[0]]
        finally:
            db.close()


class PostgresLeaveRepository:
    def find_types(self) -> List[Dict[str, Any]]:
        return PostgresBaseRepository(LeaveType).find_all()

    def find_type_by_id(self, id: str) -> Optional[Dict[str, Any]]:
        return PostgresBaseRepository(LeaveType).find_by_id(id)

    def find_allocations(self, filters: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        return PostgresBaseRepository(LeaveAllocation).find_all(filters)

    def find_allocation_by_id(self, id: str) -> Optional[Dict[str, Any]]:
        return PostgresBaseRepository(LeaveAllocation).find_by_id(id)

    def update_allocation(self, id: str, data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        return PostgresBaseRepository(LeaveAllocation).update(id, data)

    def create_allocation(self, data: Dict[str, Any]) -> Dict[str, Any]:
        return PostgresBaseRepository(LeaveAllocation).create(data)

    def ensure_default_allocations(self, employee_id: str, year: Optional[int] = None) -> List[Dict[str, Any]]:
        year = year or date.today().year
        existing = self.find_allocations({"employee_id": employee_id})
        existing_types = {a.get("leave_type_id") or a.get("time_off_type_id") for a in existing}
        created = list(existing)
        start = date(year, 1, 1)
        end = date(year, 12, 31)
        for leave_type in self.find_types():
            type_id = leave_type["id"]
            if type_id in existing_types:
                continue
            units = DEFAULT_LEAVE_UNITS.get((leave_type.get("code") or "").upper(), 12)
            created.append(self.create_allocation({
                "employee_id": employee_id,
                "leave_type_id": type_id,
                "allocation_period_start": start.isoformat(),
                "allocation_period_end": end.isoformat(),
                "allocated_units": units,
                "used_units": 0,
            }))
        return created

    def find_requests(self, filters: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        return PostgresBaseRepository(LeaveRequest).find_all(filters)

    def find_request_by_id(self, id: str) -> Optional[Dict[str, Any]]:
        return PostgresBaseRepository(LeaveRequest).find_by_id(id)

    def create_request(self, data: Dict[str, Any]) -> Dict[str, Any]:
        return PostgresBaseRepository(LeaveRequest).create(data)

    def update_request(self, id: str, data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        return PostgresBaseRepository(LeaveRequest).update(id, data)


class PostgresPayrollRepository:
    def find_structures(self, filters=None) -> List[Dict[str, Any]]:
        rows = PostgresBaseRepository(SalaryStructure).find_all()
        if filters and filters.get("is_active") is not None:
            rows = [s for s in rows if (s.get("status") == "ACTIVE") == bool(filters["is_active"])]
        return rows

    def find_structure_by_id(self, id: str) -> Optional[Dict[str, Any]]:
        return PostgresBaseRepository(SalaryStructure).find_by_id(id)

    def find_rules(self, filters=None) -> List[Dict[str, Any]]:
        return PostgresBaseRepository(SalaryRule).find_all(filters)

    def find_rule_by_id(self, id: str) -> Optional[Dict[str, Any]]:
        return PostgresBaseRepository(SalaryRule).find_by_id(id)

    def find_rule_versions(self, structure_id: str) -> List[Dict[str, Any]]:
        with SessionLocal() as session:
            rows = session.query(
                SalaryStructureRule.sequence,
                SalaryRule.code,
                SalaryRule.name,
                SalaryRule.category,
                SalaryRuleVersion.formula_expression,
                SalaryRuleVersion.id.label("version_id"),
                SalaryRule.id.label("rule_id")
            ).join(
                SalaryRule, SalaryStructureRule.salary_rule_id == SalaryRule.id
            ).join(
                SalaryRuleVersion, SalaryRule.version_id == SalaryRuleVersion.id
            ).filter(
                SalaryStructureRule.salary_structure_id == structure_id
            ).order_by(SalaryStructureRule.sequence).all()
            
            versions = []
            for r in rows:
                v = {
                    "rule_id": str(r.rule_id),
                    "version_id": str(r.version_id),
                    "sequence": r.sequence,
                    "rule_code": r.code,
                    "rule_name": r.name,
                    "category": r.category,
                    "formula": r.formula_expression,
                    # Fallback calc_type, parsing logic could go here if JSON is used
                }
                
                # If formula contains JSON, parse it
                if v["formula"].startswith("{"):
                    try:
                        import json
                        data = json.loads(v["formula"])
                        v["calculation_type"] = data.get("calculation_type", "FORMULA")
                        v["percentage"] = data.get("percentage", 0.0)
                        v["fixed_amount"] = data.get("fixed_amount", 0.0)
                        v["base_code"] = data.get("base_code")
                        v["formula"] = data.get("formula", "0")
                    except:
                        v["calculation_type"] = "FORMULA"
                else:
                    v["calculation_type"] = "FORMULA"
                
                versions.append(v)
            return versions

    def create_structure(self, data: Dict[str, Any]) -> Dict[str, Any]:
        return PostgresBaseRepository(SalaryStructure).create(data)

    def update_structure(self, id: str, data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        return PostgresBaseRepository(SalaryStructure).update(id, data)

    def create_rule(self, data: Dict[str, Any]) -> Dict[str, Any]:
        return PostgresBaseRepository(SalaryRule).create(data)

    def update_rule(self, id: str, data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        return PostgresBaseRepository(SalaryRule).update(id, data)
        
    def create_rule_version(self, data: Dict[str, Any]) -> Dict[str, Any]:
        return PostgresBaseRepository(SalaryRuleVersion).create(data)

    def add_rule_to_structure(self, data: Dict[str, Any]) -> Dict[str, Any]:
        return PostgresBaseRepository(SalaryStructureRule).create(data)

    def find_payruns(self, filters=None) -> List[Dict[str, Any]]:
        return PostgresBaseRepository(Payrun).find_all(filters)

    def find_payrun_by_id(self, id: str) -> Optional[Dict[str, Any]]:
        return PostgresBaseRepository(Payrun).find_by_id(id)

    def create_payrun(self, data: Dict[str, Any]) -> Dict[str, Any]:
        payload = dict(data)
        if "total_employees" in payload and "employee_count" not in payload:
            payload["employee_count"] = payload["total_employees"]
        return PostgresBaseRepository(Payrun).create(payload)

    def update_payrun(self, id: str, data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        payload = dict(data)
        if "total_employees" in payload and "employee_count" not in payload:
            payload["employee_count"] = payload["total_employees"]
        return PostgresBaseRepository(Payrun).update(id, payload)

    def find_payrun_employees(self, payrun_id: str) -> List[Dict[str, Any]]:
        return PostgresBaseRepository(PayrunEmployee).find_all({"payrun_id": payrun_id})

    def add_payrun_employee(self, data: Dict[str, Any]) -> Dict[str, Any]:
        return PostgresBaseRepository(PayrunEmployee).create(data)

    def add_payrun_employees_bulk(self, rows: List[Dict[str, Any]]) -> int:
        if not rows:
            return 0
        db = SessionLocal()
        try:
            objects = []
            valid = {c.key for c in PayrunEmployee.__table__.columns}
            for data in rows:
                payload = {k: v for k, v in dict(data).items() if k in valid}
                if not payload.get("id"):
                    payload["id"] = str(uuid.uuid4())
                objects.append(PayrunEmployee(**payload))
            db.add_all(objects)
            db.commit()
            return len(objects)
        except Exception:
            db.rollback()
            raise
        finally:
            db.close()

    def update_payrun_employee_status(self, id: str, status: str, error_message: Optional[str] = None) -> Optional[Dict[str, Any]]:
        payload = {"calculation_status": status}
        if error_message is not None:
            payload["error_message"] = error_message
        return PostgresBaseRepository(PayrunEmployee).update(id, payload)

    def find_payslips(self, filters=None) -> List[Dict[str, Any]]:
        repo = PostgresBaseRepository(Payslip)
        data = repo.find_all({k: v for k, v in (filters or {}).items() if k not in ("period_start", "period_end")})
        if filters and filters.get("period_start"):
            data = [p for p in data if (p.get("period_start") or "") >= filters["period_start"]]
        if filters and filters.get("period_end"):
            data = [p for p in data if (p.get("period_end") or "") <= filters["period_end"]]
        return data

    def find_payslip_by_id(self, id: str) -> Optional[Dict[str, Any]]:
        return PostgresBaseRepository(Payslip).find_by_id(id)

    def find_payslip_by_number(self, payslip_number: str) -> Optional[Dict[str, Any]]:
        rows = PostgresBaseRepository(Payslip).find_all({"payslip_number": payslip_number})
        return rows[0] if rows else None

    def create_payslip(self, data: Dict[str, Any]) -> Dict[str, Any]:
        payload = dict(data)
        if "gross" in payload and "gross_salary" not in payload:
            payload["gross_salary"] = payload["gross"]
        if "net" in payload and "net_salary" not in payload:
            payload["net_salary"] = payload["net"]
        if not payload.get("payslip_number"):
            emp_part = str(payload.get("employee_id") or "emp")[:8]
            payload["payslip_number"] = f"PS-{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}-{emp_part}"
        if not payload.get("generated_at"):
            payload["generated_at"] = datetime.now(timezone.utc).isoformat()
        if not payload.get("status"):
            payload["status"] = "CALCULATED"
        return PostgresBaseRepository(Payslip).create(payload)

    def update_payslip(self, id: str, data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        return PostgresBaseRepository(Payslip).update(id, data)

    def mark_payslips_status(self, payrun_id: str, status: str) -> int:
        db = SessionLocal()
        try:
            count = db.query(Payslip).filter(Payslip.payrun_id == payrun_id).update(
                {"status": status}, synchronize_session=False
            )
            db.commit()
            return count
        except Exception:
            db.rollback()
            raise
        finally:
            db.close()

    def mark_payslips_paid(self, payrun_id: str) -> int:
        return self.mark_payslips_status(payrun_id, "PAID")

    def find_payslip_lines(self, payslip_id: str) -> List[Dict[str, Any]]:
        lines = PostgresBaseRepository(PayslipLine).find_all({"payslip_id": payslip_id})
        return sorted(lines, key=lambda l: l.get("sequence") or 0)

    def create_payslip_line(self, data: Dict[str, Any]) -> Dict[str, Any]:
        payload = dict(data)
        if "rule_id" in payload and "salary_rule_id" not in payload:
            payload["salary_rule_id"] = payload["rule_id"]
        if "computed_amount" in payload and "amount" not in payload:
            payload["amount"] = payload["computed_amount"]
        if "percentage" in payload and "rate" not in payload:
            payload["rate"] = payload["percentage"]
        return PostgresBaseRepository(PayslipLine).create(payload)

    def delete_payslip_lines(self, payslip_id: str):
        db = SessionLocal()
        try:
            db.query(PayslipLine).filter(PayslipLine.payslip_id == payslip_id).delete(synchronize_session=False)
            db.commit()
        except Exception:
            db.rollback()
            raise
        finally:
            db.close()

    def find_warnings(self, filters=None) -> List[Dict[str, Any]]:
        return PostgresBaseRepository(PayrollWarning).find_all(filters)

    def create_warning(self, data: Dict[str, Any]) -> Dict[str, Any]:
        payload = dict(data)
        if "code" in payload and "warning_code" not in payload:
            payload["warning_code"] = payload["code"]
        return PostgresBaseRepository(PayrollWarning).create(payload)

    def update_warning(self, id: str, data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        return PostgresBaseRepository(PayrollWarning).update(id, data)

    def find_payments(self, filters=None) -> List[Dict[str, Any]]:
        return PostgresBaseRepository(Payment).find_all(filters)

    def create_payment(self, data: Dict[str, Any]) -> Dict[str, Any]:
        return PostgresBaseRepository(Payment).create(data)

    def find_deliveries(self, payrun_id: str) -> List[Dict[str, Any]]:
        payslips = self.find_payslips({"payrun_id": payrun_id})
        ids = {p["id"] for p in payslips}
        rows = PostgresBaseRepository(PayslipDelivery).find_all()
        return [r for r in rows if r.get("payslip_id") in ids]

    def create_delivery(self, data: Dict[str, Any]) -> Dict[str, Any]:
        return PostgresBaseRepository(PayslipDelivery).create(data)

    def update_delivery(self, id: str, data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        return PostgresBaseRepository(PayslipDelivery).update(id, data)

    def delete_payslip_artifacts(self, payslip_id: str):
        db = SessionLocal()
        try:
            db.query(PayslipCalculationTrace).filter(PayslipCalculationTrace.payslip_id == payslip_id).delete(synchronize_session=False)
            db.query(PayslipInput).filter(PayslipInput.payslip_id == payslip_id).delete(synchronize_session=False)
            db.query(PayslipWorkedDays).filter(PayslipWorkedDays.payslip_id == payslip_id).delete(synchronize_session=False)
            db.query(PayslipSnapshot).filter(PayslipSnapshot.payslip_id == payslip_id).delete(synchronize_session=False)
            db.commit()
        except Exception:
            db.rollback()
            raise
        finally:
            db.close()

    def save_payslip_trace(self, payslip_id: str, entries: List[Dict[str, Any]], inputs: Dict[str, Any]):
        db = SessionLocal()
        now = datetime.now(timezone.utc)
        try:
            db.query(PayslipCalculationTrace).filter(
                PayslipCalculationTrace.payslip_id == payslip_id
            ).delete(synchronize_session=False)
            db.flush()
            for idx, entry in enumerate(entries or [], start=1):
                db.add(PayslipCalculationTrace(
                    id=str(uuid.uuid4()),
                    payslip_id=payslip_id,
                    step_number=idx,
                    rule_id=entry.get("rule_id") if _looks_uuid(entry.get("rule_id")) else None,
                    rule_code=entry.get("rule_code") or "UNKNOWN",
                    rule_name=entry.get("rule_name"),
                    input_snapshot=inputs,
                    base_code=entry.get("base_code"),
                    base_value=entry.get("base_value"),
                    rate=entry.get("percentage"),
                    expression=entry.get("formula"),
                    result=entry.get("computed_amount") or 0,
                    explanation=entry.get("explanation"),
                    calculated_at=now,
                ))
            db.commit()
        except Exception:
            db.rollback()
            raise
        finally:
            db.close()

    def find_payslip_traces_by_payslip(self, payslip_id: str) -> List[Dict[str, Any]]:
        rows = PostgresBaseRepository(PayslipCalculationTrace).find_all({"payslip_id": payslip_id})
        return sorted(rows, key=lambda r: r.get("step_number") or 0)

    def save_payslip_snapshot(self, payslip_id: str, data: Dict[str, Any]) -> Dict[str, Any]:
        existing = self.find_payslip_snapshot_by_payslip_id(payslip_id)
        payload = {
            "payslip_id": payslip_id,
            "employee_snapshot": data.get("employee_snapshot") or {},
            "contract_snapshot": data.get("contract_snapshot") or {},
            "attendance_snapshot": data.get("attendance_snapshot"),
            "leave_snapshot": data.get("leave_snapshot"),
            "salary_structure_snapshot": data.get("salary_structure_snapshot"),
            "salary_rules_snapshot": data.get("salary_rules_snapshot"),
        }
        if existing:
            return PostgresBaseRepository(PayslipSnapshot).update(existing["id"], payload)
        return PostgresBaseRepository(PayslipSnapshot).create(payload)

    def find_payslip_snapshot_by_payslip_id(self, payslip_id: str) -> Optional[Dict[str, Any]]:
        rows = PostgresBaseRepository(PayslipSnapshot).find_all({"payslip_id": payslip_id})
        return rows[0] if rows else None

    def save_payslip_inputs(self, payslip_id: str, inputs: Dict[str, Any]):
        names = {
            "contract_wage": "Contract wage",
            "worked_days": "Worked days",
            "total_working_days": "Total working days",
            "paid_leave_days": "Paid leave days",
            "unpaid_leave_days": "Unpaid leave days",
            "overtime_hours": "Overtime hours",
            "CONTRACT_WAGE": "Contract wage",
            "WORKED_DAYS": "Worked days",
            "TOTAL_WORKING_DAYS": "Total working days",
            "PAID_LEAVE_DAYS": "Paid leave days",
            "UNPAID_LEAVE_DAYS": "Unpaid leave days",
            "OVERTIME_HOURS": "Overtime hours",
        }
        db = SessionLocal()
        try:
            db.query(PayslipInput).filter(PayslipInput.payslip_id == payslip_id).delete(synchronize_session=False)
            db.flush()
            for code, value in (inputs or {}).items():
                db.add(PayslipInput(
                    id=str(uuid.uuid4()),
                    payslip_id=payslip_id,
                    input_code=str(code)[:50],
                    input_name=names.get(code, str(code)),
                    input_type="NUMBER",
                    numeric_value=value,
                    source="PAYROLL_ENGINE",
                    created_at=datetime.now(timezone.utc),
                ))
            db.commit()
        except Exception:
            db.rollback()
            raise
        finally:
            db.close()

    def save_payslip_worked_days(self, payslip_id: str, metrics: Dict[str, Any]):
        rows = [
            ("WORKED", metrics.get("worked_days", 0), metrics.get("worked_hours", 0), "Attendance + paid leave"),
            ("PAID_LEAVE", metrics.get("paid_leave_days", 0), 0, "Approved paid leave"),
            ("UNPAID_LEAVE", metrics.get("unpaid_leave_days", 0), 0, "Approved unpaid leave"),
            ("OVERTIME", 0, metrics.get("overtime_hours", 0), "Overtime hours"),
            ("SCHEDULED", metrics.get("total_working_days", 0), 0, "Schedule working days"),
        ]
        db = SessionLocal()
        try:
            db.query(PayslipWorkedDays).filter(PayslipWorkedDays.payslip_id == payslip_id).delete(synchronize_session=False)
            db.flush()
            for category, days, hours, desc in rows:
                db.add(PayslipWorkedDays(
                    id=str(uuid.uuid4()),
                    payslip_id=payslip_id,
                    category=category,
                    number_of_days=days,
                    number_of_hours=hours,
                    source="PAYROLL_ENGINE",
                    description=desc,
                    created_at=datetime.now(timezone.utc),
                ))
            db.commit()
        except Exception:
            db.rollback()
            raise
        finally:
            db.close()

    def find_worked_days(self, payslip_id: str) -> List[Dict[str, Any]]:
        return PostgresBaseRepository(PayslipWorkedDays).find_all({"payslip_id": payslip_id})

    def find_payslip_inputs(self, payslip_id: str) -> List[Dict[str, Any]]:
        return PostgresBaseRepository(PayslipInput).find_all({"payslip_id": payslip_id})

    def add_status_history(self, payrun_id: str, old_status: Optional[str], new_status: str, changed_by: Optional[str] = None, reason: str = ""):
        return PostgresBaseRepository(PayrunStatusHistory).create({
            "payrun_id": payrun_id,
            "old_status": old_status,
            "new_status": new_status,
            "changed_by": changed_by if changed_by and _looks_uuid(changed_by) else None,
            "reason": reason,
        })

    def find_status_history(self, payrun_id: str) -> List[Dict[str, Any]]:
        rows = PostgresBaseRepository(PayrunStatusHistory).find_all({"payrun_id": payrun_id})
        return sorted(rows, key=lambda r: r.get("created_at") or "")

    def create_payment_for_payslip(self, payslip: Dict[str, Any], payment_date: Optional[str] = None) -> Dict[str, Any]:
        existing = self.find_payments({"payslip_id": payslip["id"]})
        if existing:
            return PostgresBaseRepository(Payment).update(existing[0]["id"], {
                "status": "COMPLETED",
                "payment_date": payment_date or date.today().isoformat(),
                "amount": payslip.get("net") or payslip.get("net_salary") or 0,
            })
        return self.create_payment({
            "payslip_id": payslip["id"],
            "payment_reference": f"PAY-{payslip.get('payslip_number') or payslip['id'][:8]}",
            "payment_date": payment_date or date.today().isoformat(),
            "amount": payslip.get("net") or payslip.get("net_salary") or 0,
            "payment_method": "BANK_TRANSFER",
            "status": "COMPLETED",
        })

    def mark_payslip_delivered(self, payslip: Dict[str, Any], employee: Optional[Dict[str, Any]] = None):
        return self.create_delivery({
            "payslip_id": payslip["id"],
            "delivery_method": "PORTAL",
            "recipient": (employee or {}).get("email"),
            "status": "SENT",
            "sent_at": datetime.now(timezone.utc).isoformat(),
        })


class PostgresNotificationRepository(PostgresBaseRepository):
    def __init__(self):
        super().__init__(Notification)

    def find_for_employee(self, employee: Dict[str, Any], app_role: str) -> List[Dict[str, Any]]:
        all_notes = [n for n in self.find_all() if n.get("is_active") is not False]
        emp_id = str(employee.get("id") or "") if employee else ""
        user_id = str(employee.get("user_id") or "") if employee else ""
        dept_id = str(employee.get("department_id") or "") if employee else ""
        role = str(app_role or "EMPLOYEE").strip().upper()
        is_hr = role in ("HR", "ADMIN")

        def same(left, right) -> bool:
            return bool(left) and bool(right) and str(left).lower() == str(right).lower()

        results = []
        for n in all_notes:
            target = (n.get("target_type") or "").upper()
            target_id = str(n.get("target_id") or "")
            ntype = (n.get("type") or "").upper()
            title = (n.get("title") or "").lower()
            leave_staff_only = (
                ntype == "LEAVE" or "leave request" in title or title.startswith("leave request")
            ) and target != "EMPLOYEE"

            if leave_staff_only or target == "ROLE":
                if is_hr:
                    results.append(n)
                continue
            if target == "EMPLOYEE":
                if same(target_id, emp_id) or same(target_id, user_id):
                    results.append(n)
                continue
            if target == "DEPARTMENT":
                if same(target_id, dept_id):
                    results.append(n)
                continue
            if target in ("ALL", "ALL_EMPLOYEES", ""):
                results.append(n)
        return sorted(results, key=lambda n: n.get("published_at") or n.get("created_at") or "", reverse=True)

    def mark_read(self, notification_id: str, employee_id: str):
        db = SessionLocal()
        try:
            existing = db.query(NotificationRead).filter(
                NotificationRead.notification_id == notification_id,
                NotificationRead.employee_id == employee_id,
            ).first()
            if not existing:
                db.add(NotificationRead(
                    notification_id=notification_id,
                    employee_id=employee_id,
                    read_at=datetime.now(timezone.utc),
                ))
                db.commit()
        finally:
            db.close()


class PostgresBankAccountRepository(PostgresBaseRepository):
    def __init__(self):
        super().__init__(Employee)

    def find_all(self, filters: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        return []

    def find_by_employee(self, employee_id: str) -> List[Dict[str, Any]]:
        return []

    def find_primary(self, employee_id: str) -> Optional[Dict[str, Any]]:
        return None


class PostgresScheduleRepository(PostgresBaseRepository):
    def __init__(self):
        super().__init__(Schedule)

    def find_days(self, schedule_id: str) -> List[Dict[str, Any]]:
        schedule = self.find_by_id(schedule_id) if schedule_id else None
        days = schedule_to_days(schedule)
        if days and any(d.get("is_working") for d in days):
            return days
        return default_weekday_days()

    def upsert_days(self, schedule_id: str, days: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        updated = self.update(schedule_id, days_to_schedule_columns(days))
        return schedule_to_days(updated) if updated else days

    def find_for_employee(self, employee_id: str, as_of: Optional[date] = None) -> Optional[Dict[str, Any]]:
        as_of = as_of or date.today()
        assignments = PostgresBaseRepository(EmployeeSchedule).find_all({"employee_id": employee_id})
        active = []
        for row in assignments:
            start = _as_date(row.get("effective_from"))
            end = _as_date(row.get("effective_to"))
            if start and start > as_of:
                continue
            if end and end < as_of:
                continue
            active.append(row)
        if not active:
            return None
        active.sort(key=lambda r: r.get("effective_from") or "", reverse=True)
        schedule = self.find_by_id(active[0].get("schedule_id"))
        if schedule:
            schedule["assignment"] = active[0]
        return schedule

    def assign_employee(self, employee_id: str, schedule_id: str, effective_from: Optional[str] = None) -> Dict[str, Any]:
        today = effective_from or date.today().isoformat()
        assignments = PostgresBaseRepository(EmployeeSchedule).find_all({"employee_id": employee_id})
        yesterday = (date.fromisoformat(str(today)[:10]) - timedelta(days=1)).isoformat()
        for row in assignments:
            if not row.get("effective_to"):
                PostgresBaseRepository(EmployeeSchedule).update(row["id"], {"effective_to": yesterday})
        return PostgresBaseRepository(EmployeeSchedule).create({
            "employee_id": employee_id,
            "schedule_id": schedule_id,
            "effective_from": today,
        })


class PostgresEmploymentHistoryRepository(PostgresBaseRepository):
    def __init__(self):
        super().__init__(EmploymentHistory)

    def record_change(self, employee: Dict[str, Any], reason: str = "UPDATE"):
        today = date.today()
        open_rows = [r for r in self.find_all({"employee_id": employee["id"]}) if not r.get("effective_to")]
        for row in open_rows:
            same = (
                row.get("department_id") == employee.get("department_id")
                and row.get("job_position_id") == employee.get("job_position_id")
                and row.get("manager_id") == employee.get("manager_id")
                and row.get("employment_type") == employee.get("employment_type")
            )
            if same:
                return row
            self.update(row["id"], {"effective_to": (today - timedelta(days=1)).isoformat()})
        return self.create({
            "employee_id": employee["id"],
            "department_id": employee.get("department_id"),
            "job_position_id": employee.get("job_position_id"),
            "manager_id": employee.get("manager_id"),
            "employment_type": employee.get("employment_type"),
            "effective_from": today.isoformat(),
            "reason": reason,
        })


class PostgresUserRepository:
    def find_by_email(self, email: str) -> Optional[Dict[str, Any]]:
        db = SessionLocal()
        try:
            user = db.query(User).filter(User.email.ilike(email.strip())).first()
            if not user:
                return None
            return {c.name: _serialize(getattr(user, c.name)) for c in user.__table__.columns}
        finally:
            db.close()

    def find_by_id(self, user_id: str) -> Optional[Dict[str, Any]]:
        db = SessionLocal()
        try:
            user = db.query(User).filter(User.id == user_id).first()
            if not user:
                return None
            return {c.name: _serialize(getattr(user, c.name)) for c in user.__table__.columns}
        finally:
            db.close()

    def get_role_names(self, user_id: str) -> List[str]:
        db = SessionLocal()
        try:
            uid = str(user_id)
            rows = (
                db.query(Role.name)
                .join(UserRole, UserRole.role_id == Role.id)
                .filter(UserRole.user_id.in_([uid, user_id]))
                .all()
            )
            return [r[0] for r in rows]
        finally:
            db.close()

    def update_last_login(self, user_id: str):
        db = SessionLocal()
        try:
            user = db.query(User).filter(User.id == user_id).first()
            if user:
                user.last_login_at = datetime.now(timezone.utc)
                db.commit()
        finally:
            db.close()

    def update_password_hash(self, user_id: str, password_hash: str):
        db = SessionLocal()
        try:
            user = db.query(User).filter(User.id == user_id).first()
            if user:
                user.password_hash = password_hash
                db.commit()
        finally:
            db.close()

    def create_login_account(self, email: str, password: str, role_name: str = "EMPLOYEE") -> Dict[str, Any]:
        existing = self.find_by_email(email)
        if existing:
            raise ValueError("An account with this email already exists")
        db = SessionLocal()
        try:
            user_id = str(uuid.uuid4())
            now = datetime.now(timezone.utc)
            user = User(
                id=user_id,
                email=email.strip(),
                password_hash=hash_password(password),
                status="ACTIVE",
                created_at=now,
                updated_at=now,
            )
            db.add(user)
            role = db.query(Role).filter(Role.name == role_name).first()
            if not role:
                role = db.query(Role).filter(Role.name == "EMPLOYEE").first()
            if role:
                db.add(UserRole(user_id=user_id, role_id=role.id, assigned_at=now))
            db.commit()
            return {"id": user_id, "email": email.strip(), "status": "ACTIVE"}
        except Exception:
            db.rollback()
            raise
        finally:
            db.close()

    def set_status(self, user_id: str, status: str):
        db = SessionLocal()
        try:
            user = db.query(User).filter(User.id == user_id).first()
            if user:
                user.status = status
                user.updated_at = datetime.now(timezone.utc)
                db.commit()
        finally:
            db.close()


class PostgresAuditRepository(PostgresBaseRepository):
    def __init__(self):
        super().__init__(AuditLog)

    def create(self, data: Dict[str, Any]) -> Dict[str, Any]:
        entity_type = data.get("entity_type") or data.get("entity_table")
        payload = {
            "id": str(uuid.uuid4()),
            "user_id": data.get("actor_id") if _looks_uuid(data.get("actor_id")) else None,
            "action": data.get("event_type") or data.get("action") or "UPDATE",
            "entity_schema": data.get("entity_schema"),
            "entity_table": entity_type,
            "entity_id": data.get("entity_id") if _looks_uuid(data.get("entity_id")) else None,
            "new_values": {
                "description": data.get("description"),
                "metadata": data.get("metadata") or data.get("event_metadata") or {},
                "actor_role": data.get("actor_role"),
            },
        }
        return super().create(payload)

    def find_page(self, filters: Optional[Dict[str, Any]] = None, page: int = 1, page_size: int = 50):
        filters = filters or {}
        db = SessionLocal()
        try:
            query = db.query(AuditLog)
            if filters.get("entity_id"):
                query = query.filter(AuditLog.entity_id == filters["entity_id"])
            if filters.get("event_type"):
                query = query.filter(AuditLog.action == filters["event_type"])
            if filters.get("entity_type"):
                query = query.filter(AuditLog.entity_table == filters["entity_type"])
            search = str(filters.get("search") or "").strip()
            if search:
                pattern = f"%{search}%"
                query = query.filter(
                    (AuditLog.action.ilike(pattern))
                    | (AuditLog.entity_table.ilike(pattern))
                )
            total = query.count()
            rows = (
                query.order_by(AuditLog.created_at.desc())
                .offset(max(page - 1, 0) * page_size)
                .limit(page_size)
                .all()
            )
            user_ids = [str(r.user_id) for r in rows if r.user_id]
            emails = {}
            if user_ids:
                for user in db.query(User).filter(User.id.in_(user_ids)).all():
                    emails[str(user.id)] = user.email
            base = PostgresBaseRepository(AuditLog)
            mapped = []
            for obj in rows:
                row = base._dict(obj)
                values = row.get("new_values") if isinstance(row.get("new_values"), dict) else {}
                mapped.append({
                    **row,
                    "event_type": row.get("action"),
                    "entity_type": row.get("entity_table"),
                    "actor_email": emails.get(str(row.get("user_id") or "")),
                    "actor_role": values.get("actor_role"),
                    "metadata": values.get("metadata") if isinstance(values, dict) else {},
                    "description": values.get("description") if isinstance(values, dict) else "",
                })
            return mapped, total
        finally:
            db.close()

    def find_all(self, filters: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        rows, _ = self.find_page(filters, page=1, page_size=500)
        return rows
