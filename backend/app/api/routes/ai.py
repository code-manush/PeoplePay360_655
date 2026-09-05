from fastapi import APIRouter, HTTPException, Depends
from typing import Dict, Any

from app.core.response import success_response, error_response
from app.api.deps import get_current_user, require_role
from app.services.ai_agent import analyze_employee
from app.repositories.postgres_repos import PostgresEmployeeRepository

router = APIRouter(prefix="/ai", tags=["ai"])
emp_repo = PostgresEmployeeRepository()

@router.get("/employee-analysis/{employee_id}")
def get_employee_analysis(employee_id: str, current_user: dict = Depends(require_role("ADMIN", "HR"))):
    # Ensure employee exists
    emp = emp_repo.find_by_id(employee_id)
    if not emp:
        raise HTTPException(status_code=404, detail=error_response("NOT_FOUND", "Employee not found"))
        
    try:
        analysis = analyze_employee(employee_id)
        return success_response(analysis, "Employee analysis generated successfully")
    except Exception as e:
        raise HTTPException(status_code=500, detail=error_response("AI_ERROR", str(e)))
