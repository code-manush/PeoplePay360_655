"""
Payslip PDF generator using ReportLab.
"""
from io import BytesIO
from typing import Dict, List, Optional
from datetime import datetime
import os
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    HRFlowable
)
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

FONT = "Helvetica"
FONT_BOLD = "Helvetica-Bold"
_FONTS_READY = False


def _register_unicode_fonts() -> None:
    """Helvetica has no ₹ glyph; embed a Unicode TTF when available."""
    global FONT, FONT_BOLD, _FONTS_READY
    if _FONTS_READY:
        return
    windir = Path(os.environ.get("WINDIR", r"C:\Windows")) / "Fonts"
    bundled = Path(__file__).resolve().parent / "fonts"
    candidates = [
        (windir / "segoeui.ttf", windir / "segoeuib.ttf"),
        (windir / "arial.ttf", windir / "arialbd.ttf"),
        (windir / "calibri.ttf", windir / "calibrib.ttf"),
        (windir / "nirmala.ttf", windir / "nirmalab.ttf"),
        (bundled / "DejaVuSans.ttf", bundled / "DejaVuSans-Bold.ttf"),
        (
            Path("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"),
            Path("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"),
        ),
    ]
    for regular, bold in candidates:
        if not regular.exists():
            continue
        try:
            pdfmetrics.registerFont(TTFont("PPSans", str(regular)))
            if bold.exists():
                pdfmetrics.registerFont(TTFont("PPSans-Bold", str(bold)))
                pdfmetrics.registerFontFamily(
                    "PPSans", normal="PPSans", bold="PPSans-Bold"
                )
                FONT_BOLD = "PPSans-Bold"
            else:
                FONT_BOLD = "PPSans"
            FONT = "PPSans"
            break
        except Exception:
            continue
    _FONTS_READY = True


def _fmt_currency(amount: float) -> str:
    return f"₹{float(amount or 0):,.2f}"


def _fmt_date(date_str: Optional[str]) -> str:
    if not date_str:
        return "—"
    try:
        dt = datetime.fromisoformat(date_str.replace("Z", "+00:00"))
        return dt.strftime("%d %b %Y")
    except Exception:
        return date_str


def _escape(text: str) -> str:
    return (
        str(text)
        .replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
    )


def _p(
    text: str,
    *,
    bold: bool = False,
    size: int = 8,
    align: int = TA_LEFT,
    color=colors.black,
    leading: Optional[float] = None,
):
    """Paragraph cell so ReportLab draws Unicode (₹) with the embedded TTF."""
    return Paragraph(
        _escape(text),
        ParagraphStyle(
            "ppcell",
            fontName=FONT_BOLD if bold else FONT,
            fontSize=size,
            leading=leading or (size + 3),
            alignment=align,
            textColor=color,
        ),
    )


BRAND_COLOR = colors.HexColor("#1e40af")
LIGHT_BG = colors.HexColor("#eff6ff")
DEDUCTION_COLOR = colors.HexColor("#dc2626")
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
    _register_unicode_fonts()
    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=15 * mm,
        leftMargin=15 * mm,
        topMargin=15 * mm,
        bottomMargin=15 * mm,
    )

    elements = []

    # ── Company Header ─────────────────────────────────────────────────────────
    header_data = [
        [
            _p("PeoplePay360", bold=True, size=20, color=BRAND_COLOR, leading=24),
            _p("PAYSLIP", bold=True, size=14, align=TA_RIGHT, color=BRAND_COLOR, leading=18),
        ],
        [
            _p("HR & Payroll Management System", size=9, color=colors.HexColor("#64748b")),
            _p(payrun.get("run_number", "") if payrun else "", size=9, align=TA_RIGHT, color=colors.HexColor("#64748b")),
        ],
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
    period_para = _p(
        f"Pay Period: {period_start} — {period_end}",
        bold=True,
        size=11,
        align=TA_CENTER,
        color=colors.white,
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
        [_p("Employee Name", bold=True), _p(emp_name), _p("Employee Code", bold=True), _p(employee.get("employee_code", "—"))],
        [_p("Department", bold=True), _p(dept_name), _p("Designation", bold=True), _p(pos_name)],
        [_p("Email", bold=True), _p(employee.get("email", "—")), _p("Date of Joining", bold=True), _p(_fmt_date(employee.get("date_joined")))],
        [_p("Employment Type", bold=True), _p(employee.get("employment_type", "—")), _p("Contract No.", bold=True), _p(contract.get("contract_number", "—") if contract else "—")],
    ]
    emp_table = Table(emp_data, colWidths=[35 * mm, 50 * mm, 35 * mm, 45 * mm])
    emp_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (0, -1), LIGHT_BG),
        ("BACKGROUND", (2, 0), (2, -1), LIGHT_BG),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("GRID", (0, 0), (-1, -1), 0.5, BORDER_COLOR),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
    ]))
    elements.append(emp_table)
    elements.append(Spacer(1, 4 * mm))

    # ── Attendance / Leave Summary ─────────────────────────────────────────────
    att_data = [
        [_p("Worked Days", bold=True), _p(f"{payslip.get('worked_days', 0):.1f}"), _p("Total Working Days", bold=True), _p(str(payslip.get("total_working_days", 0)))],
        [_p("Paid Leave Days", bold=True), _p(f"{payslip.get('paid_leave_days', 0):.1f}"), _p("Unpaid Leave Days", bold=True), _p(f"{payslip.get('unpaid_leave_days', 0):.1f}")],
        [_p("Overtime Hours", bold=True), _p(f"{payslip.get('overtime_hours', 0):.2f} hrs"), _p("Contract Wage", bold=True), _p(_fmt_currency(contract.get("wage", 0) if contract else 0), align=TA_LEFT)],
    ]
    att_table = Table(att_data, colWidths=[35 * mm, 50 * mm, 35 * mm, 45 * mm])
    att_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (0, -1), LIGHT_BG),
        ("BACKGROUND", (2, 0), (2, -1), LIGHT_BG),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("GRID", (0, 0), (-1, -1), 0.5, BORDER_COLOR),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
    ]))
    elements.append(_p("Attendance Summary", bold=True, size=10))
    elements.append(Spacer(1, 2 * mm))
    elements.append(att_table)
    elements.append(Spacer(1, 4 * mm))

    # ── Earnings / Deductions Table ────────────────────────────────────────────
    elements.append(_p("Salary Computation", bold=True, size=10))
    elements.append(Spacer(1, 2 * mm))

    sal_data = [[
        _p("#", bold=True, color=colors.white),
        _p("Description", bold=True, color=colors.white),
        _p("Category", bold=True, color=colors.white),
        _p("Amount", bold=True, color=colors.white, align=TA_RIGHT),
    ]]

    for line in sorted(payslip_lines, key=lambda l: l.get("sequence", 0)):
        cat = line.get("category", "")
        amount = line.get("computed_amount", 0)
        if cat in ("NET",):
            continue
        sal_data.append([
            _p(str(line.get("sequence", ""))),
            _p(line.get("rule_name", "")),
            _p(str(cat).title()),
            _p(_fmt_currency(abs(amount)), align=TA_RIGHT),
        ])

    sal_data.append([
        _p(""),
        _p("GROSS SALARY", bold=True),
        _p(""),
        _p(_fmt_currency(payslip.get("gross", 0)), bold=True, align=TA_RIGHT),
    ])
    sal_data.append([
        _p(""),
        _p("Total Deductions", bold=True, color=DEDUCTION_COLOR),
        _p(""),
        _p(f"- {_fmt_currency(payslip.get('total_deductions', 0))}", bold=True, color=DEDUCTION_COLOR, align=TA_RIGHT),
    ])
    sal_data.append([
        _p("", color=colors.white),
        _p("NET SALARY", bold=True, color=colors.white),
        _p("", color=colors.white),
        _p(_fmt_currency(payslip.get("net", 0)), bold=True, color=colors.white, align=TA_RIGHT),
    ])

    sal_table = Table(sal_data, colWidths=[10 * mm, 90 * mm, 35 * mm, 30 * mm])
    sal_style = [
        ("BACKGROUND", (0, 0), (-1, 0), BRAND_COLOR),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("GRID", (0, 0), (-1, -4), 0.5, BORDER_COLOR),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
        ("RIGHTPADDING", (3, 0), (3, -1), 6),
        ("BACKGROUND", (0, -3), (-1, -3), LIGHT_BG),
        ("BACKGROUND", (0, -1), (-1, -1), BRAND_COLOR),
    ]
    sal_table.setStyle(TableStyle(sal_style))
    elements.append(sal_table)
    elements.append(Spacer(1, 4 * mm))

    # ── Payment Status ─────────────────────────────────────────────────────────
    pay_status = payment.get("status", "PENDING") if payment else "PENDING"
    pay_ref = payment.get("transaction_reference", "—") if payment else "—"
    pay_method = payment.get("payment_method", "—") if payment else "—"

    pay_data = [
        [_p("Payment Status", bold=True), _p(pay_status), _p("Transaction Reference", bold=True), _p(pay_ref)],
        [_p("Payment Method", bold=True), _p(str(pay_method).replace("_", " ").title()), _p("Payment Date", bold=True),
         _p(_fmt_date(payment.get("completed_at")) if payment else "—")],
    ]
    pay_table = Table(pay_data, colWidths=[35 * mm, 50 * mm, 35 * mm, 45 * mm])
    pay_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (0, -1), LIGHT_BG),
        ("BACKGROUND", (2, 0), (2, -1), LIGHT_BG),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("GRID", (0, 0), (-1, -1), 0.5, BORDER_COLOR),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
    ]))
    elements.append(_p("Payment Information", bold=True, size=10))
    elements.append(Spacer(1, 2 * mm))
    elements.append(pay_table)
    elements.append(Spacer(1, 6 * mm))

    # ── Footer ─────────────────────────────────────────────────────────────────
    elements.append(HRFlowable(width="100%", thickness=0.5, color=BORDER_COLOR))
    elements.append(Spacer(1, 3 * mm))
    elements.append(_p(
        "This is a computer-generated payslip. "
        "No signature is required. Generated by PeoplePay360 HR & Payroll System.",
        size=7,
        align=TA_CENTER,
        color=colors.HexColor("#94a3b8"),
    ))

    doc.build(elements)
    return buffer.getvalue()
