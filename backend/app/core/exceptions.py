from fastapi import HTTPException
from typing import Optional


class AppException(Exception):
    def __init__(self, code: str, message: str, status_code: int = 400, field: Optional[str] = None):
        self.code = code
        self.message = message
        self.status_code = status_code
        self.field = field
        super().__init__(message)


class NotFoundException(AppException):
    def __init__(self, resource: str, id: str):
        super().__init__(
            code="NOT_FOUND",
            message=f"{resource} with id '{id}' not found.",
            status_code=404,
        )


class ValidationException(AppException):
    def __init__(self, message: str, field: Optional[str] = None):
        super().__init__(
            code="VALIDATION_ERROR",
            message=message,
            status_code=422,
            field=field,
        )


class InsufficientLeaveBalanceException(AppException):
    def __init__(self, available: float, requested: float):
        super().__init__(
            code="INSUFFICIENT_LEAVE_BALANCE",
            message=f"Insufficient leave balance. Available: {available} days, Requested: {requested} days.",
            status_code=422,
        )


class PayrollImmutableException(AppException):
    def __init__(self):
        super().__init__(
            code="PAYROLL_IMMUTABLE",
            message="This payroll record is finalized (PAID) and cannot be modified. Create an adjustment instead.",
            status_code=409,
        )


class InvalidStateTransitionException(AppException):
    def __init__(self, current: str, target: str):
        super().__init__(
            code="INVALID_STATE_TRANSITION",
            message=f"Cannot transition payrun from '{current}' to '{target}'.",
            status_code=409,
        )


class DuplicatePayslipException(AppException):
    def __init__(self, employee_id: str, period: str):
        super().__init__(
            code="DUPLICATE_PAYSLIP",
            message=f"A payslip already exists for employee {employee_id} for period {period}.",
            status_code=409,
        )
