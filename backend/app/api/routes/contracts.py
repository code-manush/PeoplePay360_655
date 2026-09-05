from fastapi import APIRouter, HTTPException, Query, Depends
from typing import Optional
from datetime import datetime, timezone, date as date_type, timedelta
from app.repositories.postgres_repos import (
    PostgresContractRepository, PostgresEmployeeRepository,
    PostgresNotificationRepository
)
from app.core.response import success_response, error_response, paginated_response
from app.core.config import settings
from app.services.audit_service import audit_service
from app.api.deps import require_min_role

router = APIRouter(prefix="/contracts", tags=["contracts"])
contract_repo = PostgresContractRepository()
emp_repo = PostgresEmployeeRepository()
notif_repo = PostgresNotificationRepository()


def _employee_map():
    return {e["id"]: e for e in emp_repo.find_all()}


def _enrich_contract(c: dict, employees=None) -> dict:
    emp = (employees or {}).get(c.get("employee_id")) if employees is not None else emp_repo.find_by_id(c.get("employee_id", ""))
    today = date_type.today()
    raw_end = c.get("end_date")
    if hasattr(raw_end, "isoformat"):
        raw_end = raw_end.isoformat()
    end_date = date_type.fromisoformat(str(raw_end)[:10]) if raw_end else None
    days_remaining = (end_date - today).days if end_date else None
    expiry_status = None
    if days_remaining is not None and c.get("status") == "ACTIVE":
        if days_remaining <= 7:
            expiry_status = "CRITICAL"
        elif days_remaining <= 30:
            expiry_status = "URGENT"
        elif days_remaining <= 60:
            expiry_status = "WARNING"
        elif days_remaining <= 90:
            expiry_status = "NOTICE"
    return {
        **c,
        "employee": {"id": emp["id"], "first_name": emp["first_name"], "last_name": emp["last_name"],
                     "employee_code": emp["employee_code"]} if emp else None,
        "days_remaining": days_remaining,
        "expiry_status": expiry_status,
    }


@router.get("")
def list_contracts(
    status: Optional[str] = None,
    employee_id: Optional[str] = None,
    department_id: Optional[str] = None,
    expiring_within_days: Optional[int] = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=500),
    current: dict = Depends(require_min_role("HR")),
):
    filters = {}
    if status:
        filters["status"] = status
    if employee_id:
        filters["employee_id"] = employee_id
    if department_id:
        filters["department_id"] = department_id
    all_contracts = contract_repo.find_all(filters)
    employees = _employee_map()
    enriched = [_enrich_contract(c, employees) for c in all_contracts]

    if expiring_within_days is not None:
        enriched = [c for c in enriched
                    if c.get("days_remaining") is not None
                    and 0 <= c["days_remaining"] <= expiring_within_days
                    and c.get("status") == "ACTIVE"]

    enriched.sort(key=lambda c: c.get("start_date", ""), reverse=True)
    total = len(enriched)
    start = (page - 1) * page_size
    return paginated_response(enriched[start:start + page_size], page, page_size, total)


@router.get("/expiring")
def get_expiring_contracts():
    max_days = max(settings.expiry_warning_days)
    all_contracts = contract_repo.find_all({"status": "ACTIVE"})
    employees = _employee_map()
    enriched = [_enrich_contract(c, employees) for c in all_contracts]
    expiring = [c for c in enriched
                if c.get("days_remaining") is not None
                and 0 <= c["days_remaining"] <= max_days]
    expiring.sort(key=lambda c: c.get("days_remaining", 999))
    return success_response(expiring)


@router.get("/{contract_id}")
def get_contract(contract_id: str):
    contract = contract_repo.find_by_id(contract_id)
    if not contract:
        raise HTTPException(status_code=404, detail=error_response("NOT_FOUND", f"Contract {contract_id} not found"))
    return success_response(_enrich_contract(contract))


@router.post("")
def create_contract(body: dict, current: dict = Depends(require_min_role("HR"))):
    if not body.get("employee_id"):
        raise HTTPException(status_code=422, detail=error_response("VALIDATION_ERROR", "employee_id is required"))
    if body.get("start_date") and body.get("end_date"):
        if body["end_date"] < body["start_date"]:
            raise HTTPException(status_code=422, detail=error_response("VALIDATION_ERROR", "End date must be after start date"))
    if body.get("wage", -1) < 0:
        raise HTTPException(status_code=422, detail=error_response("VALIDATION_ERROR", "Wage must be >= 0"))
    contract = contract_repo.create({
        **body,
        "contract_number": body.get("contract_number") or f"CON{int(datetime.now(timezone.utc).timestamp())}",
        "contract_type": body.get("contract_type") or body.get("employment_type") or "FULL_TIME",
        "basic_salary": body.get("basic_salary") or body.get("wage") or body.get("base_salary") or 0,
        "working_hours_per_week": body.get("working_hours_per_week") or 40,
        "status": body.get("status", "ACTIVE"),
    })
    audit_service.log("CONTRACT_CREATED", "CONTRACT", contract["id"],
                      description=f"Contract {contract.get('contract_number')} created")
    return success_response(contract, "Contract created")


@router.put("/{contract_id}")
def update_contract(contract_id: str, body: dict):
    existing = contract_repo.find_by_id(contract_id)
    if not existing:
        raise HTTPException(status_code=404, detail=error_response("NOT_FOUND", f"Contract {contract_id} not found"))
    updated = contract_repo.update(contract_id, body)
    return success_response(updated)


@router.patch("/{contract_id}/renew")
def renew_contract(contract_id: str, body: dict):
    old = contract_repo.find_by_id(contract_id)
    if not old:
        raise HTTPException(status_code=404, detail=error_response("NOT_FOUND", f"Contract {contract_id} not found"))

    contract_repo.update(contract_id, {"status": "EXPIRED"})

    new_contract_data = {
        **old,
        "contract_number": f"{old['contract_number']}-R",
        "start_date": body.get("start_date", old["end_date"]),
        "end_date": body.get("end_date"),
        "wage": body.get("wage", old["wage"]),
        "status": "ACTIVE",
        "previous_contract_id": contract_id,
        "notes": f"Renewed from {old['contract_number']}",
    }
    del new_contract_data["id"]
    new_contract = contract_repo.create(new_contract_data)

    emp = emp_repo.find_by_id(old.get("employee_id", ""))
    if emp:
        notif_repo.create({
            "title": "Contract Renewed",
            "message": f"Your contract has been renewed. New contract period: {body.get('start_date')} to {body.get('end_date')}.",
            "type": "CONTRACT",
            "priority": "NORMAL",
            "target_type": "EMPLOYEE",
            "target_id": emp["id"],
            "published_at": datetime.now(timezone.utc).isoformat(),
            "expires_at": None,
            "is_active": True,
            "created_by": None,
        })

    audit_service.log("CONTRACT_RENEWED", "CONTRACT", new_contract["id"],
                      description=f"Contract renewed. Previous: {contract_id}")
    return success_response(new_contract, "Contract renewed successfully")


@router.delete("/{contract_id}")
def delete_contract(contract_id: str):
    existing = contract_repo.find_by_id(contract_id)
    if not existing:
        raise HTTPException(status_code=404, detail=error_response("NOT_FOUND", f"Contract {contract_id} not found"))
    updated = contract_repo.update(contract_id, {"status": "TERMINATED"})
    return success_response(updated, "Contract terminated")
