"""
Calculation trace — records the step-by-step explanation of payroll calculation.
Used for the "Explainable Payslip" feature.
"""
from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class TraceEntry:
    sequence: int
    rule_code: str
    rule_name: str
    category: str
    calculation_type: str
    base_code: Optional[str]
    base_value: Optional[float]
    percentage: Optional[float]
    formula: Optional[str]
    computed_amount: float
    explanation: str


@dataclass
class CalculationTrace:
    employee_id: str
    period: str
    contract_wage: float
    worked_days: float
    total_working_days: int
    paid_leave_days: float
    unpaid_leave_days: float
    overtime_hours: float
    entries: List[TraceEntry] = field(default_factory=list)

    def add(self, entry: TraceEntry):
        self.entries.append(entry)

    def to_dict(self) -> dict:
        return {
            "employee_id": self.employee_id,
            "period": self.period,
            "inputs": {
                "contract_wage": self.contract_wage,
                "worked_days": self.worked_days,
                "total_working_days": self.total_working_days,
                "paid_leave_days": self.paid_leave_days,
                "unpaid_leave_days": self.unpaid_leave_days,
                "overtime_hours": self.overtime_hours,
            },
            "entries": [
                {
                    "sequence": e.sequence,
                    "rule_code": e.rule_code,
                    "rule_name": e.rule_name,
                    "category": e.category,
                    "calculation_type": e.calculation_type,
                    "base_code": e.base_code,
                    "base_value": round(e.base_value, 2) if e.base_value is not None else None,
                    "percentage": e.percentage,
                    "formula": e.formula,
                    "computed_amount": round(e.computed_amount, 2),
                    "explanation": e.explanation,
                }
                for e in self.entries
            ],
        }
