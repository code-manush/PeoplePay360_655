from typing import Optional
from fastapi import APIRouter, Query, Depends
from app.services.audit_service import audit_service
from app.core.response import paginated_response
from app.api.deps import require_min_role

router = APIRouter(prefix="/audit", tags=["audit"])


@router.get("")
def get_audit_logs(
    entity_id: Optional[str] = None,
    event_type: Optional[str] = None,
    entity_type: Optional[str] = None,
    search: Optional[str] = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    current: dict = Depends(require_min_role("HR")),
):
    filters = {}
    if entity_id:
        filters["entity_id"] = entity_id
    if event_type:
        filters["event_type"] = event_type
    if entity_type:
        filters["entity_type"] = entity_type
    if search:
        filters["search"] = search
    logs, total = audit_service.get_logs(filters, page, page_size)
    return paginated_response(logs, page, page_size, total)
