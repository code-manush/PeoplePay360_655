from fastapi import APIRouter
from app.services.audit_service import audit_service
from app.core.response import success_response

router = APIRouter(prefix="/audit", tags=["audit"])


@router.get("")
def get_audit_logs(entity_id: str = None, event_type: str = None):
    filters = {}
    if entity_id:
        filters["entity_id"] = entity_id
    if event_type:
        filters["event_type"] = event_type
    logs = audit_service.get_logs(filters)
    return success_response(logs)
