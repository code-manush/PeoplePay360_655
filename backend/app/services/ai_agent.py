import httpx
import json
from datetime import date, datetime
from typing import Dict, Any

from sqlalchemy import func
from app.core.database import SessionLocal
from app.models.domain import (
    Employee,
    AttendanceRecord,
    LeaveRequest,
    Contract,
    Payslip
)

OLLAMA_URL = "http://localhost:11434/api/generate"
MODEL_NAME = "qwen3"

def _generate_mock_report(emp, metrics) -> dict:
    """Fallback programmatic report generator when Ollama is unreachable."""
    late = metrics.get("late_arrivals", 0)
    att = metrics.get("total_attendance", 0)
    ot = metrics.get("overtime_count", 0)
    
    if late > 5:
        rating = "65%"
        recommendation = "Not Recommended for Hike"
        remark = "Employee has a high number of late arrivals. Needs performance counseling."
        info = f"{emp.first_name} has been struggling with punctuality recently. Has arrived late {late} times."
    elif ot > 1 and att > 5:
        rating = "95%"
        recommendation = "Highly Recommended for Hike"
        remark = "Outstanding dedication and consistent overtime contributions."
        info = f"{emp.first_name} is a highly dedicated team member with excellent attendance and extra effort."
    else:
        rating = "85%"
        recommendation = "Standard Increment Recommended"
        remark = "Consistent performance with acceptable attendance."
        info = f"{emp.first_name} is performing at expected levels with standard attendance records."
        
    return {
        "brief_info": f"[AI Fallback Analysis] {info}",
        "rating": rating,
        "recommendation": recommendation,
        "remark": remark,
        "metrics": metrics
    }

def analyze_employee(employee_id: str) -> Dict[str, Any]:
    with SessionLocal() as db:
        emp = db.query(Employee).filter(Employee.id == employee_id).first()
        if not emp:
            raise ValueError("Employee not found")
        
        total_attendance = db.query(func.count(AttendanceRecord.id)).filter(
            AttendanceRecord.employee_id == employee_id,
            AttendanceRecord.status == "PRESENT"
        ).scalar()
        
        attendances = db.query(AttendanceRecord).filter(
            AttendanceRecord.employee_id == employee_id,
            AttendanceRecord.status == "PRESENT"
        ).all()
        
        late_count = 0
        total_late_minutes = 0
        overtime_count = 0
        total_overtime_hours = 0.0
        
        for att in attendances:
            if att.overtime_hours and att.overtime_hours > 0:
                overtime_count += 1
                total_overtime_hours += float(att.overtime_hours)
                
            if att.check_in:
                if att.check_in.hour > 9 or (att.check_in.hour == 9 and att.check_in.minute > 15):
                    late_count += 1
                    late_mins = (att.check_in.hour - 9) * 60 + att.check_in.minute
                    total_late_minutes += late_mins
                    
        avg_late_mins = round(total_late_minutes / late_count, 1) if late_count > 0 else 0
        avg_overtime = round(total_overtime_hours / overtime_count, 1) if overtime_count > 0 else 0

        approved_leaves = db.query(LeaveRequest).filter(
            LeaveRequest.employee_id == employee_id,
            LeaveRequest.status == "APPROVED"
        ).all()
        
        declined_leaves = db.query(LeaveRequest).filter(
            LeaveRequest.employee_id == employee_id,
            LeaveRequest.status == "REJECTED"
        ).all()
        
        contract = db.query(Contract).filter(
            Contract.employee_id == employee_id,
            Contract.status == "ACTIVE"
        ).first()
        
        payslips = db.query(Payslip).filter(
            Payslip.employee_id == employee_id
        ).order_by(Payslip.period_start.desc()).limit(3).all()
        
        metrics = {
            "total_attendance": total_attendance,
            "late_arrivals": late_count,
            "avg_late_mins": avg_late_mins,
            "overtime_count": overtime_count,
            "avg_overtime_hours": avg_overtime,
            "approved_leaves": len(approved_leaves),
            "declined_leaves": len(declined_leaves),
            "contract_salary": str(contract.basic_salary) if contract and contract.basic_salary else "N/A"
        }

        prompt = f"""
You are an HR AI Agent. Analyze the following employee data and generate an Employee Card.
Provide a brief info about the employee, give them a numerical value or percentage rating,
and suggest whether the admin should give a hike or increment to the employee along with a brief remark.

Employee Name: {emp.first_name} {emp.last_name}

Total Attendance: {total_attendance} days present.
Late Arrivals: {late_count} times. Average late time: {avg_late_mins} minutes.
Overtime: {overtime_count} times. Average overtime: {avg_overtime} hours.

Approved Leaves: {len(approved_leaves)}
Reasons for leaves: {[l.reason for l in approved_leaves if l.reason]}

Declined Leaves: {len(declined_leaves)}
Rejection Reasons (Tags): {[l.rejection_reason for l in declined_leaves if l.rejection_reason]}

Contract Basic Salary: {metrics["contract_salary"]}
Recent Payslips Net Salary: {[str(p.net_salary) for p in payslips]}

Format your output as a clean, structured JSON object:
{{
    "brief_info": "...",
    "rating": "...",
    "recommendation": "...",
    "remark": "..."
}}
Only return the JSON.
"""
        try:
            with httpx.Client(timeout=10.0) as client:
                response = client.post(
                    OLLAMA_URL,
                    json={
                        "model": MODEL_NAME,
                        "prompt": prompt,
                        "stream": False,
                        "format": "json"
                    }
                )
                response.raise_for_status()
                data = response.json()
                ai_result = json.loads(data.get("response", "{}"))
                
                # Merge the raw metrics directly into the response so the frontend can render the full report dashboard
                ai_result["metrics"] = metrics
                return ai_result

        except Exception as e:
            print(f"Ollama AI Error: {e}")
            # Instead of returning the ugly stack trace in brief_info, we gracefully fallback
            # to a programmatic analysis so the user gets a working report UI.
            return _generate_mock_report(emp, metrics)
