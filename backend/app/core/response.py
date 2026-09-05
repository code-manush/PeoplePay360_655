from typing import Any, Optional, Dict
from pydantic import BaseModel


class ApiResponse(BaseModel):
    success: bool = True
    data: Any = None
    message: Optional[str] = None


class PaginatedMeta(BaseModel):
    page: int
    page_size: int
    total: int
    total_pages: int


class PaginatedResponse(BaseModel):
    success: bool = True
    data: Any = None
    meta: Optional[PaginatedMeta] = None


class ErrorDetail(BaseModel):
    code: str
    message: str
    field: Optional[str] = None


class ErrorResponse(BaseModel):
    success: bool = False
    error: ErrorDetail


def success_response(data: Any, message: Optional[str] = None) -> Dict:
    return {"success": True, "data": data, "message": message}


def paginated_response(data: Any, page: int, page_size: int, total: int) -> Dict:
    total_pages = (total + page_size - 1) // page_size
    return {
        "success": True,
        "data": data,
        "meta": {
            "page": page,
            "page_size": page_size,
            "total": total,
            "total_pages": total_pages,
        },
    }


def error_response(code: str, message: str, field: Optional[str] = None) -> Dict:
    return {
        "success": False,
        "error": {"code": code, "message": message, "field": field},
    }
