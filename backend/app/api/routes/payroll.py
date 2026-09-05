from fastapi import APIRouter, HTTPException, Query, Depends
from fastapi.responses import StreamingResponse
from typing import Optional
from datetime import datetime, timezone, date as date_type
from app.repositories.postgres_repos import (
    PostgresPayrollRepository, PostgresEmployeeRepository,
    PostgresContractRepository, PostgresScheduleRepository,
    PostgresAttendanceRepository, PostgresLeaveRepository,
    PostgresBankAccountRepository, PostgresNotificationRepository
)
from app.payroll.engine import PayrollEngine
from app.reports.payslip_pdf import generate_payslip_pdf
from app.core.response import success_response, error_response, paginated_response
from app.services.audit_service import audit_service
from io import BytesIO
from app.api.deps import get_current_user
from app.core.security import role_at_least

router = APIRouter(prefix="/payroll", tags=["payroll"])

payroll_repo = PostgresPayrollRepository()
emp_repo = PostgresEmployeeRepository()
contract_repo = PostgresContractRepository()
schedule_repo = PostgresScheduleRepository()
att_repo = PostgresAttendanceRepository()
leave_repo = PostgresLeaveRepository()
bank_repo = PostgresBankAccountRepository()
notif_repo = PostgresNotificationRepository()


def _get_engine() -> PayrollEngine:
    return PayrollEngine(
        payroll_repo=payroll_repo,
        employee_repo=emp_repo,
        contract_repo=contract_repo,
        schedule_repo=schedule_repo,
        attendance_repo=att_repo,
        leave_repo=leave_repo,
        bank_repo=bank_repo,
    )


@router.get("/salary-structures")
def list_salary_structures():
    structures = payroll_repo.find_structures()
    for s in structures:
        s["rules_count"] = len(payroll_repo.find_rule_versions(s["id"]))
    return success_response(structures)


@router.get("/salary-structures/{structure_id}")
def get_salary_structure(structure_id: str):
    s = payroll_repo.find_structure_by_id(structure_id)
    if not s:
        raise HTTPException(status_code=404, detail=error_response("NOT_FOUND", f"Structure {structure_id} not found"))
    rules_raw = payroll_repo.find_rules()
    all_rules = {r["id"]: r for r in rules_raw}
    versions = payroll_repo.find_rule_versions(structure_id)
    enriched_versions = []
    for v in versions:
        rule = all_rules.get(v["rule_id"], {})
        enriched_versions.append({**v, "rule": rule})
    return success_response({**s, "rule_versions": enriched_versions})


@router.get("/payruns")
def list_payruns(
    status: Optional[str] = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=1000),
    current: dict = Depends(get_current_user),
):
    filters = {}
    if status:
        filters["status"] = status
    all_runs = payroll_repo.find_payruns(filters)
    all_runs.sort(key=lambda p: p.get("created_at", ""), reverse=True)
    total = len(all_runs)
    start = (page - 1) * page_size
    return paginated_response(all_runs[start:start + page_size], page, page_size, total)


@router.get("/payruns/{payrun_id}")
def get_payrun(payrun_id: str):
    payrun = payroll_repo.find_payrun_by_id(payrun_id)
    if not payrun:
        raise HTTPException(status_code=404, detail=error_response("NOT_FOUND", f"Payrun {payrun_id} not found"))
    payrun_emps = payroll_repo.find_payrun_employees(payrun_id)
    payslips = payroll_repo.find_payslips({"payrun_id": payrun_id})
    warnings = payroll_repo.find_warnings({"payrun_id": payrun_id})
    return success_response({
        **payrun,
        "employee_count": len(payrun_emps),
        "payslips": payslips,
        "warnings": warnings,
    })


@router.post("/payruns")
def create_payrun(body: dict, current: dict = Depends(get_current_user)):
    if not body.get("period_start") or not body.get("period_end"):
        raise HTTPException(status_code=422, detail=error_response("VALIDATION_ERROR", "period_start and period_end required"))
    if body["period_end"] < body["period_start"]:
        raise HTTPException(status_code=422, detail=error_response("VALIDATION_ERROR", "period_end must be after period_start"))

    run_number = f"PR-{date_type.today().year}-{datetime.now(timezone.utc).strftime('%m%d%H%M')}"
    payrun = payroll_repo.create_payrun({
        "run_number": run_number,
        "period_start": body["period_start"],
        "period_end": body["period_end"],
        "payment_date": body.get("payment_date") or body.get("period_end"),
        "status": "DRAFT",
        "created_by": current.get("employee_id") or current.get("user_id"),
        "employee_count": 0,
        "total_gross": None,
        "total_deductions": None,
        "total_net": None,
    })

    all_contracts = contract_repo.find_all({"status": "ACTIVE"})
    structure_id = body.get("salary_structure_id")
    added = 0
    seen = set()
    for contract in all_contracts:
        if structure_id and contract.get("salary_structure_id") != structure_id:
            continue
        emp_id = contract.get("employee_id")
        if emp_id in seen:
            continue
        emp = emp_repo.find_by_id(emp_id)
        if emp and emp.get("is_active"):
            payroll_repo.add_payrun_employee({
                "payrun_id": payrun["id"],
                "employee_id": emp_id,
                "contract_id": contract["id"],
                "calculation_status": "PENDING",
            })
            seen.add(emp_id)
            added += 1

    if body.get("employee_ids"):
        for emp_id in body["employee_ids"]:
            if emp_id in seen:
                continue
            emp = emp_repo.find_by_id(emp_id)
            contracts = contract_repo.find_all({"employee_id": emp_id, "status": "ACTIVE"})
            if emp and contracts:
                payroll_repo.add_payrun_employee({
                    "payrun_id": payrun["id"],
                    "employee_id": emp_id,
                    "contract_id": contracts[0]["id"],
                    "calculation_status": "PENDING",
                })
                seen.add(emp_id)
                added += 1

    payroll_repo.update_payrun(payrun["id"], {"employee_count": added})
    audit_service.log("PAYRUN_CREATED", "PAYRUN", payrun["id"],
                      description=f"Payrun {run_number} created")
    return success_response({**payrun, "employee_count": added, "total_employees": added}, "Payrun created")


@router.post("/payruns/{payrun_id}/compute")
def compute_payrun(payrun_id: str):
    payrun = payroll_repo.find_payrun_by_id(payrun_id)
    if not payrun:
        raise HTTPException(status_code=404, detail=error_response("NOT_FOUND", f"Payrun {payrun_id} not found"))
    if payrun["status"] not in ("DRAFT", "COMPUTED"):
        raise HTTPException(status_code=409, detail=error_response(
            "INVALID_STATE", f"Cannot compute payrun in status '{payrun['status']}'. Must be DRAFT or COMPUTED."))

    engine = _get_engine()
    try:
        period_start = date_type.fromisoformat(payrun["period_start"])
        period_end = date_type.fromisoformat(payrun["period_end"])
        result = engine.compute_payrun(payrun, period_start, period_end)
    except Exception as e:
        raise HTTPException(status_code=500, detail=error_response("COMPUTATION_ERROR", str(e)))

    now = datetime.now(timezone.utc).isoformat()
    updated = payroll_repo.update_payrun(payrun_id, {
        "status": "COMPUTED",
        "computed_at": now,
        "total_employees": len(result["payslips"]),
        "total_gross": result["total_gross"],
        "total_deductions": result["total_deductions"],
        "total_net": result["total_net"],
    })
    audit_service.log("PAYRUN_COMPUTED", "PAYRUN", payrun_id,
                      description=f"Payrun computed. Net: ₹{result['total_net']:,.2f}",
                      metadata={"total_net": result["total_net"], "warnings": len(result["warnings"])})
    return success_response({**updated, "warnings": result["warnings"]}, "Payrun computed successfully")


@router.post("/payruns/{payrun_id}/validate")
def validate_payrun(payrun_id: str):
    payrun = payroll_repo.find_payrun_by_id(payrun_id)
    if not payrun:
        raise HTTPException(status_code=404, detail=error_response("NOT_FOUND", f"Payrun {payrun_id} not found"))
    if payrun["status"] != "COMPUTED":
        raise HTTPException(status_code=409, detail=error_response(
            "INVALID_STATE", f"Cannot validate payrun in status '{payrun['status']}'. Must be COMPUTED first."))
    now = datetime.now(timezone.utc).isoformat()
    updated = payroll_repo.update_payrun(payrun_id, {"status": "VALIDATED", "validated_at": now})
    audit_service.log("PAYRUN_VALIDATED", "PAYRUN", payrun_id, description="Payrun validated")
    return success_response(updated, "Payrun validated")


@router.post("/payruns/{payrun_id}/pay")
def pay_payrun(payrun_id: str, current: dict = Depends(get_current_user)):
    payrun = payroll_repo.find_payrun_by_id(payrun_id)
    if not payrun:
        raise HTTPException(status_code=404, detail=error_response("NOT_FOUND", f"Payrun {payrun_id} not found"))
    if payrun["status"] == "PAID":
        return success_response(payrun, "Payrun is already paid")
    if payrun["status"] not in ("VALIDATED", "COMPUTED"):
        raise HTTPException(status_code=409, detail=error_response(
            "INVALID_STATE", f"Cannot pay payrun in status '{payrun['status']}'. Validate it first."))

    payslips_count = payroll_repo.mark_payslips_paid(payrun_id)
    now = datetime.now(timezone.utc).isoformat()

    notif_repo.create({
        "title": f"Salary credited - {payrun.get('run_number')}",
        "message": f"Payroll {payrun.get('run_number')} has been paid. Net total: ₹{payrun.get('total_net') or 0:,.2f}.",
        "type": "PAYROLL",
        "priority": "HIGH",
        "target_type": "ALL",
        "target_id": None,
        "published_at": now,
        "is_active": True,
        "created_by": current.get("user_id"),
    })

    updated = payroll_repo.update_payrun(payrun_id, {"status": "PAID"})
    audit_service.log("PAYRUN_PAID", "PAYRUN", payrun_id, description=f"Payrun paid. {payslips_count} payslips")
    return success_response({**updated, "success_count": payslips_count, "failed_count": 0}, "Payrun paid")


@router.post("/payruns/{payrun_id}/cancel")
def cancel_payrun(payrun_id: str):
    payrun = payroll_repo.find_payrun_by_id(payrun_id)
    if not payrun:
        raise HTTPException(status_code=404, detail=error_response("NOT_FOUND", f"Payrun {payrun_id} not found"))
    if payrun["status"] == "PAID":
        raise HTTPException(status_code=409, detail=error_response("INVALID_STATE", "Cannot cancel a paid payrun"))
    updated = payroll_repo.update_payrun(payrun_id, {"status": "CANCELLED"})
    return success_response(updated, "Payrun cancelled")


@router.get("/payslips")
def list_payslips(
    employee_id: Optional[str] = None,
    payrun_id: Optional[str] = None,
    status: Optional[str] = None,
    period_start: Optional[str] = None,
    period_end: Optional[str] = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=500),
    current: dict = Depends(get_current_user),
):
    filters = {}
    if not role_at_least(current.get("role"), "HR"):
        filters["employee_id"] = current.get("employee_id")
    elif employee_id:
        filters["employee_id"] = employee_id
    if payrun_id:
        filters["payrun_id"] = payrun_id
    if status:
        filters["status"] = status
    if period_start:
        filters["period_start"] = period_start
    if period_end:
        filters["period_end"] = period_end

    all_ps = payroll_repo.find_payslips(filters)
    all_ps.sort(key=lambda p: p.get("period_start", ""), reverse=True)
    total = len(all_ps)
    start = (page - 1) * page_size
    return paginated_response(all_ps[start:start + page_size], page, page_size, total)


@router.get("/payslips/{payslip_id}")
def get_payslip(payslip_id: str):
    ps = payroll_repo.find_payslip_by_id(payslip_id)
    if not ps:
        raise HTTPException(status_code=404, detail=error_response("NOT_FOUND", f"Payslip {payslip_id} not found"))
    lines = payroll_repo.find_payslip_lines(payslip_id)
    payments = payroll_repo.find_payments({"payslip_id": payslip_id})
    emp = emp_repo.find_by_id(ps.get("employee_id", ""))
    return success_response({**ps, "lines": lines, "payments": payments, "employee": emp})


@router.get("/payslips/{payslip_id}/pdf")
def download_payslip_pdf(payslip_id: str):
    ps = payroll_repo.find_payslip_by_id(payslip_id)
    if not ps:
        raise HTTPException(status_code=404, detail=error_response("NOT_FOUND", f"Payslip {payslip_id} not found"))

    emp = emp_repo.find_by_id(ps.get("employee_id", ""))
    if not emp:
        raise HTTPException(status_code=404, detail=error_response("NOT_FOUND", "Employee not found"))

    contract = contract_repo.find_by_id(ps.get("contract_id", ""))
    payrun = payroll_repo.find_payrun_by_id(ps.get("payrun_id", ""))
    lines = payroll_repo.find_payslip_lines(payslip_id)
    payments = payroll_repo.find_payments({"payslip_id": payslip_id})
    payment = payments[0] if payments else None

    from app.repositories.postgres_repos import PostgresDepartmentRepository, PostgresJobPositionRepository
    dept_repo = PostgresDepartmentRepository()
    pos_repo = PostgresJobPositionRepository()
    department = dept_repo.find_by_id(emp.get("department_id", ""))
    job_position = pos_repo.find_by_id(emp.get("job_position_id", ""))

    pdf_bytes = generate_payslip_pdf(
        payslip=ps,
        employee=emp,
        department=department,
        job_position=job_position,
        contract=contract,
        payrun=payrun,
        payslip_lines=lines,
        payment=payment,
    )

    filename = f"payslip_{emp.get('employee_code', emp['id'])}_{ps.get('period_start', '')[:7]}.pdf"
    return StreamingResponse(
        BytesIO(pdf_bytes),
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.get("/warnings")
def list_warnings(
    payrun_id: Optional[str] = None,
    employee_id: Optional[str] = None,
    is_resolved: Optional[bool] = None,
):
    filters = {}
    if payrun_id:
        filters["payrun_id"] = payrun_id
    if employee_id:
        filters["employee_id"] = employee_id
    if is_resolved is not None:
        filters["is_resolved"] = is_resolved
    warnings = payroll_repo.find_warnings(filters)
    return success_response(warnings)


@router.post("/warnings/{warning_id}/resolve")
def resolve_warning(warning_id: str, body: dict = {}):
    now = datetime.now(timezone.utc).isoformat()
    updated = payroll_repo.update_warning(warning_id, {
        "is_resolved": True,
        "resolved_by": body.get("resolved_by", "HR"),
        "resolved_at": now,
    })
    return success_response(updated, "Warning resolved")
