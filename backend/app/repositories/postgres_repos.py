from typing import Dict, Any, List, Optional
from datetime import date, datetime, timezone
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
    AuditLog, Schedule,
)


def _serialize(value):
    if isinstance(value, datetime):
        return value.isoformat()
    if isinstance(value, date):
        return value.isoformat()
    if isinstance(value, Decimal):
        return float(value)
    if isinstance(value, uuid.UUID):
        return str(value)
    return value


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
        if self.model is Contract:
            if "wage" in incoming and "basic_salary" not in incoming:
                incoming["basic_salary"] = incoming["wage"]
            if "base_salary" in incoming and "basic_salary" not in incoming:
                incoming["basic_salary"] = incoming["base_salary"]
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
            if v is not None and str(col.type).upper().startswith("DATE") and "TIME" not in str(col.type).upper():
                v = _as_date(v)
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

    def create_payslip(self, data: Dict[str, Any]) -> Dict[str, Any]:
        return PostgresBaseRepository(Payslip).create(data)

    def update_payslip(self, id: str, data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        return PostgresBaseRepository(Payslip).update(id, data)

    def mark_payslips_paid(self, payrun_id: str) -> int:
        db = SessionLocal()
        try:
            count = db.query(Payslip).filter(Payslip.payrun_id == payrun_id).update(
                {"status": "PAID"}, synchronize_session=False
            )
            db.commit()
            return count
        except Exception:
            db.rollback()
            raise
        finally:
            db.close()

    def find_payslip_lines(self, payslip_id: str) -> List[Dict[str, Any]]:
        lines = PostgresBaseRepository(PayslipLine).find_all({"payslip_id": payslip_id})
        return sorted(lines, key=lambda l: l.get("sequence") or 0)

    def create_payslip_line(self, data: Dict[str, Any]) -> Dict[str, Any]:
        return PostgresBaseRepository(PayslipLine).create(data)

    def delete_payslip_lines(self, payslip_id: str):
        db = SessionLocal()
        try:
            db.query(PayslipLine).filter(PayslipLine.payslip_id == payslip_id).delete()
            db.commit()
        except Exception:
            db.rollback()
            raise
        finally:
            db.close()

    def find_warnings(self, filters=None) -> List[Dict[str, Any]]:
        return PostgresBaseRepository(PayrollWarning).find_all(filters)

    def create_warning(self, data: Dict[str, Any]) -> Dict[str, Any]:
        return PostgresBaseRepository(PayrollWarning).create(data)

    def update_warning(self, id: str, data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        return PostgresBaseRepository(PayrollWarning).update(id, data)

    def find_payments(self, filters=None) -> List[Dict[str, Any]]:
        return PostgresBaseRepository(Payment).find_all(filters)

    def create_payment(self, data: Dict[str, Any]) -> Dict[str, Any]:
        return PostgresBaseRepository(Payment).create(data)

    def find_deliveries(self, payrun_id: str) -> List[Dict[str, Any]]:
        return []

    def create_delivery(self, data: Dict[str, Any]) -> Dict[str, Any]:
        return data

    def update_delivery(self, id: str, data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        return data


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
        return []

    def upsert_days(self, schedule_id: str, days: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        return days


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
        payload = {
            "id": str(uuid.uuid4()),
            "user_id": data.get("actor_id") if data.get("actor_id") != "SYSTEM" else None,
            "action": data.get("event_type") or data.get("action") or "UPDATE",
            "entity_schema": None,
            "entity_table": data.get("entity_type"),
            "entity_id": data.get("entity_id") if _looks_uuid(data.get("entity_id")) else None,
            "new_values": {
                "description": data.get("description"),
                "metadata": data.get("metadata") or data.get("event_metadata") or {},
            },
        }
        return super().create(payload)

    def find_all(self, filters: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        rows = super().find_all()
        mapped = []
        for row in rows:
            mapped.append({
                **row,
                "event_type": row.get("action"),
                "entity_type": row.get("entity_table"),
                "metadata": (row.get("new_values") or {}).get("metadata") if isinstance(row.get("new_values"), dict) else {},
                "description": (row.get("new_values") or {}).get("description") if isinstance(row.get("new_values"), dict) else "",
            })
        if filters and filters.get("entity_id"):
            mapped = [a for a in mapped if a.get("entity_id") == filters["entity_id"]]
        if filters and filters.get("event_type"):
            mapped = [a for a in mapped if a.get("event_type") == filters["event_type"]]
        return sorted(mapped, key=lambda a: a.get("created_at") or "", reverse=True)


def _looks_uuid(value) -> bool:
    try:
        uuid.UUID(str(value))
        return True
    except Exception:
        return False
