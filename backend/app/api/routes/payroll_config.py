import json
from fastapi import APIRouter, HTTPException, Depends
from datetime import date as date_type, datetime, timezone
from typing import Optional

from app.repositories.postgres_repos import PostgresPayrollRepository
from app.api.deps import get_current_user
from app.core.security import role_at_least
from app.core.response import success_response, error_response

router = APIRouter(prefix="/payroll-config", tags=["payroll_config"])

payroll_repo = PostgresPayrollRepository()


@router.post("/salary-structures")
def create_salary_structure(body: dict, current: dict = Depends(get_current_user)):
    if not role_at_least(current.get("role"), "HR"):
        raise HTTPException(status_code=403, detail=error_response("FORBIDDEN", "Not enough permissions"))
    
    if not body.get("name") or not body.get("code"):
        raise HTTPException(status_code=422, detail=error_response("VALIDATION_ERROR", "name and code are required"))
    
    structure = payroll_repo.create_structure({
        "name": body["name"],
        "code": body["code"],
        "description": body.get("description"),
        "currency": body.get("currency", "INR"),
        "status": body.get("status", "ACTIVE"),
    })
    return success_response(structure, "Salary structure created")


@router.put("/salary-structures/{structure_id}")
def update_salary_structure(structure_id: str, body: dict, current: dict = Depends(get_current_user)):
    if not role_at_least(current.get("role"), "HR"):
        raise HTTPException(status_code=403, detail=error_response("FORBIDDEN", "Not enough permissions"))
    
    updated = payroll_repo.update_structure(structure_id, {
        "name": body.get("name"),
        "code": body.get("code"),
        "description": body.get("description"),
        "currency": body.get("currency"),
        "status": body.get("status"),
        "updated_at": datetime.now(timezone.utc).isoformat(),
    })
    return success_response(updated, "Salary structure updated")


@router.get("/salary-rules")
def list_salary_rules(current: dict = Depends(get_current_user)):
    rules = payroll_repo.find_rules()
    return success_response(rules)


@router.post("/salary-rules")
def create_salary_rule(body: dict, current: dict = Depends(get_current_user)):
    if not role_at_least(current.get("role"), "HR"):
        raise HTTPException(status_code=403, detail=error_response("FORBIDDEN", "Not enough permissions"))
        
    if not body.get("code") or not body.get("name") or not body.get("category"):
        raise HTTPException(status_code=422, detail=error_response("VALIDATION_ERROR", "code, name, category are required"))
        
    calc_type = body.get("calculation_type", "FORMULA")
    percentage = body.get("percentage", 0.0)
    fixed_amount = body.get("fixed_amount", 0.0)
    base_code = body.get("base_code", "")
    formula = body.get("formula", "0")
    
    # Store settings in formula_expression as JSON string
    formula_json = json.dumps({
        "calculation_type": calc_type,
        "percentage": percentage,
        "fixed_amount": fixed_amount,
        "base_code": base_code,
        "formula": formula
    })

    version = payroll_repo.create_rule_version({
        "version_number": 1,
        "effective_from": date_type.today().isoformat(),
        "formula_expression": formula_json,
        "description": body.get("description"),
        "is_active": True,
    })

    rule = payroll_repo.create_rule({
        "code": body["code"],
        "name": body["name"],
        "category": body["category"],
        "description": body.get("description"),
        "version_id": version["id"],
        "is_active": body.get("is_active", True),
    })

    return success_response(rule, "Salary rule created")


@router.put("/salary-rules/{rule_id}")
def update_salary_rule(rule_id: str, body: dict, current: dict = Depends(get_current_user)):
    if not role_at_least(current.get("role"), "HR"):
        raise HTTPException(status_code=403, detail=error_response("FORBIDDEN", "Not enough permissions"))
        
    rule = payroll_repo.find_rule_by_id(rule_id)
    if not rule:
        raise HTTPException(status_code=404, detail=error_response("NOT_FOUND", "Rule not found"))
        
    calc_type = body.get("calculation_type", "FORMULA")
    percentage = body.get("percentage", 0.0)
    fixed_amount = body.get("fixed_amount", 0.0)
    base_code = body.get("base_code", "")
    formula = body.get("formula", "0")
    
    formula_json = json.dumps({
        "calculation_type": calc_type,
        "percentage": percentage,
        "fixed_amount": fixed_amount,
        "base_code": base_code,
        "formula": formula
    })

    version = payroll_repo.create_rule_version({
        "version_number": 1, # Just creating a new dummy version for updates
        "effective_from": date_type.today().isoformat(),
        "formula_expression": formula_json,
        "description": body.get("description"),
        "is_active": True,
    })
    
    updated = payroll_repo.update_rule(rule_id, {
        "code": body.get("code"),
        "name": body.get("name"),
        "category": body.get("category"),
        "description": body.get("description"),
        "version_id": version["id"],
        "is_active": body.get("is_active"),
    })
    
    return success_response(updated, "Salary rule updated")


@router.post("/salary-structures/{structure_id}/rules")
def add_rule_to_structure(structure_id: str, body: dict, current: dict = Depends(get_current_user)):
    if not role_at_least(current.get("role"), "HR"):
        raise HTTPException(status_code=403, detail=error_response("FORBIDDEN", "Not enough permissions"))
        
    if not body.get("salary_rule_id") or body.get("sequence") is None:
        raise HTTPException(status_code=422, detail=error_response("VALIDATION_ERROR", "salary_rule_id and sequence are required"))
        
    structure_rule = payroll_repo.add_rule_to_structure({
        "salary_structure_id": structure_id,
        "salary_rule_id": body["salary_rule_id"],
        "sequence": body["sequence"],
        "is_mandatory": body.get("is_mandatory", True),
    })
    return success_response(structure_rule, "Rule added to structure")
