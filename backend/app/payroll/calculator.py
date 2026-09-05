"""
Payroll calculator — computes a single employee's payslip.
"""
from typing import Dict, List, Any, Tuple
from datetime import date, timedelta

from app.payroll.context import PayrollContext
from app.payroll.rules import calculate_rule
from app.payroll.trace import CalculationTrace, TraceEntry


DAY_OF_WEEK_MAP = {
    "MONDAY": 0, "TUESDAY": 1, "WEDNESDAY": 2,
    "THURSDAY": 3, "FRIDAY": 4, "SATURDAY": 5, "SUNDAY": 6,
}

DEDUCTION_CODES = {"PF_EMP", "PT", "TDS"}


def _count_working_days(start: date, end: date, schedule_days: List[Dict]) -> int:
    """Count working days in a period based on schedule."""
    working_weekdays = set()
    for day in schedule_days:
        if day.get("is_working"):
            dow = DAY_OF_WEEK_MAP.get(day["day_of_week"], -1)
            if dow >= 0:
                working_weekdays.add(dow)

    count = 0
    current = start
    while current <= end:
        if current.weekday() in working_weekdays:
            count += 1
        current += timedelta(days=1)
    return count


def _compute_attendance_metrics(
    attendance_records: List[Dict],
    approved_leaves: List[Dict],
    leave_types: Dict,
    start: date,
    end: date,
    total_working_days: int,
) -> Tuple[float, float, float, float]:
    """
    Returns: worked_days, paid_leave_days, unpaid_leave_days, overtime_hours
    """
    # Count worked days from attendance (PRESENT, LATE, OVERTIME, CORRECTED)
    attended_statuses = {"PRESENT", "LATE", "OVERTIME", "CORRECTED"}
    worked = 0.0
    overtime_hours = 0.0
    attendance_dates = set()

    for att in attendance_records:
        att_date = att.get("date", "")
        if start.isoformat() <= att_date <= end.isoformat():
            attendance_dates.add(att_date)
            status = att.get("status", "")
            if status in attended_statuses:
                worked += 1.0
            elif status == "HALF_DAY":
                worked += 0.5
            overtime_hours += float(att.get("overtime_hours") or 0.0)

    # Add paid leaves to effective worked days for Basic calculation
    paid_leave = 0.0
    unpaid_leave = 0.0

    for leave in approved_leaves:
        leave_start = leave.get("start_date", "")
        leave_end = leave.get("end_date", "")
        duration = float(leave.get("duration_days", 0))
        # Check overlap with payroll period
        if leave_end >= start.isoformat() and leave_start <= end.isoformat():
            ltype_id = leave.get("time_off_type_id")
            ltype = leave_types.get(ltype_id, {})
            if ltype.get("is_paid", True):
                paid_leave += duration
            else:
                unpaid_leave += duration

    return worked + paid_leave, paid_leave, unpaid_leave, overtime_hours


def calculate_payslip(ctx: PayrollContext) -> Tuple[Dict, CalculationTrace, List[Dict]]:
    """
    Main payroll calculation for one employee.
    Returns: (payslip_dict, trace, list_of_line_dicts)
    """
    ctx.total_working_days = _count_working_days(
        ctx.period_start, ctx.period_end, ctx.schedule_days
    )
    worked_effective, paid_leave, unpaid_leave, overtime_hours = _compute_attendance_metrics(
        ctx.attendance_records,
        ctx.approved_leave_requests,
        ctx.leave_types,
        ctx.period_start,
        ctx.period_end,
        ctx.total_working_days,
    )
    ctx.worked_days = min(worked_effective, float(ctx.total_working_days))
    ctx.paid_leave_days = paid_leave
    ctx.unpaid_leave_days = unpaid_leave
    ctx.overtime_hours = overtime_hours
    ctx.contract_wage = float(ctx.contract.get("wage", 0.0))

    trace = CalculationTrace(
        employee_id=ctx.employee["id"],
        period=f"{ctx.period_start.isoformat()} to {ctx.period_end.isoformat()}",
        contract_wage=ctx.contract_wage,
        worked_days=ctx.worked_days,
        total_working_days=ctx.total_working_days,
        paid_leave_days=ctx.paid_leave_days,
        unpaid_leave_days=ctx.unpaid_leave_days,
        overtime_hours=ctx.overtime_hours,
    )

    lines = []
    gross = 0.0
    total_deductions = 0.0
    net = 0.0
    basic = 0.0
    hra = 0.0
    transport = 0.0
    overtime_pay = 0.0
    pf_emp = 0.0
    pt_val = 0.0
    pf_employer = 0.0

    rule_code_map = {}
    for rv in ctx.salary_rule_versions:
        if rv.get("is_active"):
            rule_code_map[rv["rule_id"]] = rv

    sorted_versions = sorted(
        [rv for rv in ctx.salary_rule_versions if rv.get("is_active", True)],
        key=lambda rv: rv.get("sequence", 0) if hasattr(rv, "get") else 0
    )

    for seq_idx, rv in enumerate(sorted_versions):
        rule_id = rv.get("rule_id")
        rule_code = rv.get("rule_code", "")
        rule_name = rv.get("rule_name", rule_code)
        category = rv.get("category", "")
        calc_type = rv.get("calculation_type", "FIXED")

        # Attach category/code from rule if not on version
        # (versions are joined with rules in the repo layer normally)
        computed = calculate_rule(rv, ctx)
        ctx.computed_values[rule_code] = computed

        # Generate explanation
        explanation = rv.get("explanation", "")
        base_code = rv.get("base_code")
        base_value = ctx.computed_values.get(base_code, None) if base_code else None
        percentage = rv.get("percentage")
        formula = rv.get("formula")

        entry = TraceEntry(
            sequence=rv.get("sequence", seq_idx * 10),
            rule_code=rule_code,
            rule_name=rule_name,
            category=category,
            calculation_type=calc_type,
            base_code=base_code,
            base_value=base_value,
            percentage=percentage,
            formula=formula,
            computed_amount=computed,
            explanation=explanation or f"{rule_code} = {computed:.2f}",
        )
        trace.add(entry)

        # Track key values
        if category == "GROSS":
            gross = computed
        elif category == "NET":
            net = computed
        elif rule_code == "BASIC":
            basic = computed
        elif rule_code == "HRA":
            hra = computed
        elif rule_code == "TRANSPORT":
            transport = computed
        elif rule_code == "OVERTIME":
            overtime_pay = computed
        elif rule_code == "PF_EMP":
            pf_emp = computed
        elif rule_code == "PT":
            pt_val = computed
        elif rule_code == "PF_EMP_CONTRIB":
            pf_employer = computed

        line = {
            "payslip_id": None,  # set later
            "rule_id": rule_id,
            "rule_code": rule_code,
            "rule_name": rule_name,
            "category": category,
            "sequence": rv.get("sequence", seq_idx * 10),
            "base_amount": round(base_value, 2) if base_value is not None else None,
            "percentage": percentage,
            "computed_amount": round(computed if category not in DEDUCTION_CODES else -abs(computed), 2),
            "explanation": explanation,
        }
        lines.append(line)

    total_deductions = pf_emp + pt_val

    payslip = {
        "payrun_id": None,  # set by caller
        "employee_id": ctx.employee["id"],
        "contract_id": ctx.contract["id"],
        "period_start": ctx.period_start.isoformat(),
        "period_end": ctx.period_end.isoformat(),
        "status": "COMPUTED",
        "worked_days": round(ctx.worked_days, 2),
        "total_working_days": ctx.total_working_days,
        "paid_leave_days": round(ctx.paid_leave_days, 2),
        "unpaid_leave_days": round(ctx.unpaid_leave_days, 2),
        "overtime_hours": round(ctx.overtime_hours, 2),
        "basic": round(basic, 2),
        "hra": round(hra, 2),
        "transport": round(transport, 2),
        "overtime_pay": round(overtime_pay, 2),
        "gross": round(gross, 2),
        "pf_emp": round(pf_emp, 2),
        "pt": round(pt_val, 2),
        "total_deductions": round(total_deductions, 2),
        "pf_employer": round(pf_employer, 2),
        "net": round(net, 2),
        "currency": "INR",
        "notes": None,
    }

    return payslip, trace, lines
