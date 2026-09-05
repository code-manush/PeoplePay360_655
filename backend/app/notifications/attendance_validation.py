"""Check-in/out validation. Swap the demo implementation for office WiFi later."""
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Dict, Any, Optional


@dataclass
class ValidationResult:
    allowed: bool
    reason: Optional[str] = None


class AttendanceValidationService(ABC):
    @abstractmethod
    def validate_check_in(
        self, employee: Dict[str, Any], request_context: Dict[str, Any]
    ) -> ValidationResult:
        pass

    @abstractmethod
    def validate_check_out(
        self, employee: Dict[str, Any], attendance: Dict[str, Any], request_context: Dict[str, Any]
    ) -> ValidationResult:
        pass


class DemoAttendanceValidationService(AttendanceValidationService):
    def validate_check_in(self, employee, request_context) -> ValidationResult:
        return ValidationResult(allowed=True)

    def validate_check_out(self, employee, attendance, request_context) -> ValidationResult:
        return ValidationResult(allowed=True)


attendance_validation_service = DemoAttendanceValidationService()
