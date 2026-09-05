"""
Payslip PDF generator using ReportLab.
"""
from io import BytesIO
from typing import Dict, List, Optional, Any
from datetime import datetime

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    HRFlowable
)
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT


def _fmt_currency(amount: float) -> str:
    return f"₹{amount:,.2f}"


def _fmt_date(date_str: Optional[str]) -> str:
    if not date_str:
        return "—"
    try:
        dt = datetime.fromisoformat(date_str.replace("Z", "+00:00"))
        return dt.strftime("%d %b %Y")
    except Exception:
        return date_str


BRAND_COLOR = colors.HexColor("#1e40af")
ACCENT_COLOR = colors.HexColor("#3b82f6")
LIGHT_BG = colors.HexColor("#eff6ff")
DEDUCTION_COLOR = colors.HexColor("#dc2626")
POSITIVE_COLOR = colors.HexColor("#16a34a")
LIGHT_GRAY = colors.HexColor("#f8fafc")
BORDER_COLOR = colors.HexColor("#e2e8f0")


def generate_payslip_pdf(
    payslip: Dict,
    employee: Dict,
    department: Optional[Dict],
    job_position: Optional[Dict],
    contract: Optional[Dict],
    payrun: Optional[Dict],
    payslip_lines: List[Dict],
    payment: Optional[Dict],
) -> bytes:
    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=15 * mm,
        leftMargin=15 * mm,
        topMargin=15 * mm,
        bottomMargin=15 * mm,
    )

    styles = getSampleStyleSheet()
    elements = []

    # ── Company Header ─────────────────────────────────────────────────────────
    header_data = [
        [
            Paragraph(
                '<font size="20" color="#1e40af"><b>PeoplePay360</b></font><br/>'
                '<font size="9" color="#64748b">HR &amp; Payroll Management System</font>',
                ParagraphStyle("comp", alignment=TA_LEFT)
            ),
            Paragraph(
                f'<font size="14" color="#1e40af"><b>PAYSLIP</b></font><br/>'
                f'<font size="9" color="#64748b">{payrun.get("run_number", "") if payrun else ""}</font>',
                ParagraphStyle("slip_no", alignment=TA_RIGHT)
            ),
        ]
    ]
    header_table = Table(header_data, colWidths=[100 * mm, 65 * mm])
    header_table.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("BACKGROUND", (0, 0), (-1, -1), LIGHT_BG),
        ("TOPPADDING", (0, 0), (-1, -1), 8),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
        ("LEFTPADDING", (0, 0), (-1, -1), 10),
        ("RIGHTPADDING", (0, 0), (-1, -1), 10),
        ("ROUNDEDCORNERS", [5]),
    ]))
    elements.append(header_table)
    elements.append(Spacer(1, 6 * mm))

    # ── Pay Period Banner ──────────────────────────────────────────────────────
    period_start = _fmt_date(payslip.get("period_start"))
    period_end = _fmt_date(payslip.get("period_end"))
    period_para = Paragraph(
        f'<font size="11" color="white"><b>Pay Period: {period_start} — {period_end}</b></font>',
        ParagraphStyle("period", alignment=TA_CENTER, backColor=BRAND_COLOR)
    )
    period_table = Table([[period_para]], colWidths=[165 * mm])
    period_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), BRAND_COLOR),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
    ]))
    elements.append(period_table)
    elements.append(Spacer(1, 4 * mm))

    # ── Employee Details ───────────────────────────────────────────────────────
    emp_name = f"{employee.get('first_name', '')} {employee.get('last_name', '')}"
    dept_name = department.get("name", "—") if department else "—"
    pos_name = job_position.get("title", "—") if job_position else "—"
    emp_data = [
        ["Employee Name", emp_name, "Employee Code", employee.get("employee_code", "—")],
        ["Department", dept_name, "Designation", pos_name],
        ["Email", employee.get("email", "—"), "Date of Joining", _fmt_date(employee.get("date_joined"))],
        ["Employment Type", employee.get("employment_type", "—"), "Contract No.", contract.get("contract_number", "—") if contract else "—"],
    ]
    emp_table = Table(emp_data, colWidths=[35 * mm, 50 * mm, 35 * mm, 45 * mm])
    emp_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (0, -1), LIGHT_BG),
        ("BACKGROUND", (2, 0), (2, -1), LIGHT_BG),
        ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
        ("FONTNAME", (2, 0), (2, -1), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 8),
        ("GRID", (0, 0), (-1, -1), 0.5, BORDER_COLOR),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
    ]))
    elements.append(emp_table)
    elements.append(Spacer(1, 4 * mm))

    # ── Attendance / Leave Summary ─────────────────────────────────────────────
    att_data = [
        ["Worked Days", f"{payslip.get('worked_days', 0):.1f}", "Total Working Days", str(payslip.get("total_working_days", 0))],
        ["Paid Leave Days", f"{payslip.get('paid_leave_days', 0):.1f}", "Unpaid Leave Days", f"{payslip.get('unpaid_leave_days', 0):.1f}"],
        ["Overtime Hours", f"{payslip.get('overtime_hours', 0):.2f} hrs", "Contract Wage", _fmt_currency(contract.get("wage", 0) if contract else 0)],
    ]
    att_table = Table(att_data, colWidths=[35 * mm, 50 * mm, 35 * mm, 45 * mm])
    att_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (0, -1), LIGHT_BG),
        ("BACKGROUND", (2, 0), (2, -1), LIGHT_BG),
        ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
        ("FONTNAME", (2, 0), (2, -1), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 8),
        ("GRID", (0, 0), (-1, -1), 0.5, BORDER_COLOR),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
    ]))
    elements.append(Paragraph('<b><font size="10">Attendance Summary</font></b>',
                               ParagraphStyle("h3", spaceAfter=3)))
    elements.append(att_table)
    elements.append(Spacer(1, 4 * mm))

    # ── Earnings / Deductions Table ────────────────────────────────────────────
    elements.append(Paragraph('<b><font size="10">Salary Computation</font></b>',
                               ParagraphStyle("h3", spaceAfter=3)))

    earnings_lines = [l for l in payslip_lines if l.get("category") in ("BASIC", "ALLOWANCE")]
    deduction_lines = [l for l in payslip_lines if l.get("category") == "DEDUCTION"]
    contribution_lines = [l for l in payslip_lines if l.get("category") == "CONTRIBUTION"]
    gross_lines = [l for l in payslip_lines if l.get("category") == "GROSS"]
    net_lines = [l for l in payslip_lines if l.get("category") == "NET"]

    sal_data = [["#", "Description", "Category", "Amount"]]

    for line in sorted(payslip_lines, key=lambda l: l.get("sequence", 0)):
        cat = line.get("category", "")
        amount = line.get("computed_amount", 0)
        if cat in ("NET",):
            continue
        color_marker = "+" if amount >= 0 else "−"
        sal_data.append([
            str(line.get("sequence", "")),
            line.get("rule_name", ""),
            cat.title(),
            _fmt_currency(abs(amount)),
        ])

    # Gross
    sal_data.append(["", "GROSS SALARY", "", _fmt_currency(payslip.get("gross", 0))])
    # Deductions total
    sal_data.append(["", "Total Deductions", "", f"- {_fmt_currency(payslip.get('total_deductions', 0))}"])
    # Net
    sal_data.append(["", "NET SALARY", "", _fmt_currency(payslip.get("net", 0))])

    sal_table = Table(sal_data, colWidths=[10 * mm, 90 * mm, 35 * mm, 30 * mm])
    sal_style = [
        ("BACKGROUND", (0, 0), (-1, 0), BRAND_COLOR),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 8),
        ("GRID", (0, 0), (-1, -4), 0.5, BORDER_COLOR),
        ("ALIGN", (3, 0), (3, -1), "RIGHT"),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
        # Gross row
        ("BACKGROUND", (0, -3), (-1, -3), LIGHT_BG),
        ("FONTNAME", (0, -3), (-1, -3), "Helvetica-Bold"),
        # Deductions row
        ("TEXTCOLOR", (0, -2), (-1, -2), DEDUCTION_COLOR),
        ("FONTNAME", (0, -2), (-1, -2), "Helvetica-Bold"),
        # Net row
        ("BACKGROUND", (0, -1), (-1, -1), BRAND_COLOR),
        ("TEXTCOLOR", (0, -1), (-1, -1), colors.white),
        ("FONTNAME", (0, -1), (-1, -1), "Helvetica-Bold"),
        ("FONTSIZE", (0, -1), (-1, -1), 9),
    ]
    sal_table.setStyle(TableStyle(sal_style))
    elements.append(sal_table)
    elements.append(Spacer(1, 4 * mm))

    # ── Payment Status ─────────────────────────────────────────────────────────
    pay_status = payment.get("status", "PENDING") if payment else "PENDING"
    pay_ref = payment.get("transaction_reference", "—") if payment else "—"
    pay_method = payment.get("payment_method", "—") if payment else "—"
    status_color = POSITIVE_COLOR if pay_status == "SUCCESS" else (DEDUCTION_COLOR if pay_status == "FAILED" else ACCENT_COLOR)

    pay_data = [
        ["Payment Status", pay_status, "Transaction Reference", pay_ref],
        ["Payment Method", pay_method.replace("_", " ").title(), "Payment Date",
         _fmt_date(payment.get("completed_at")) if payment else "—"],
    ]
    pay_table = Table(pay_data, colWidths=[35 * mm, 50 * mm, 35 * mm, 45 * mm])
    pay_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (0, -1), LIGHT_BG),
        ("BACKGROUND", (2, 0), (2, -1), LIGHT_BG),
        ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
        ("FONTNAME", (2, 0), (2, -1), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 8),
        ("GRID", (0, 0), (-1, -1), 0.5, BORDER_COLOR),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
    ]))
    elements.append(Paragraph('<b><font size="10">Payment Information</font></b>',
                               ParagraphStyle("h3", spaceAfter=3)))
    elements.append(pay_table)
    elements.append(Spacer(1, 6 * mm))

    # ── Footer ─────────────────────────────────────────────────────────────────
    elements.append(HRFlowable(width="100%", thickness=0.5, color=BORDER_COLOR))
    elements.append(Spacer(1, 3 * mm))
    elements.append(Paragraph(
        '<font size="7" color="#94a3b8">This is a computer-generated payslip. '
        'No signature is required. Generated by PeoplePay360 HR &amp; Payroll System.</font>',
        ParagraphStyle("footer", alignment=TA_CENTER)
    ))

    doc.build(elements)
    return buffer.getvalue()
