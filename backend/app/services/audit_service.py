"""
AuditService — records audit events for important operations.
"""
from typing import Dict, Any, Optional, Tuple, List

from app.repositories.postgres_repos import PostgresAuditRepository

audit_repo = PostgresAuditRepository()

ENTITY_SCHEMA = {
    "PAYRUN": "payroll",
    "PAYRUNS": "payroll",
    "EMPLOYEE": "hr",
    "CONTRACT": "hr",
    "LEAVE_REQUEST": "leave_management",
    "ATTENDANCE": "attendance",
}


class AuditService:
    def log(
        self,
        event_type: str,
        entity_type: str,
        entity_id: str,
        actor_id: str = "SYSTEM",
        actor_role: str = "SYSTEM",
        description: str = "",
        metadata: Optional[Dict] = None,
    ) -> Dict:
        try:
            return audit_repo.create({
                "event_type": event_type,
                "entity_type": entity_type,
                "entity_schema": ENTITY_SCHEMA.get(str(entity_type or "").upper()),
                "entity_id": entity_id,
                "actor_id": actor_id,
                "actor_role": actor_role,
                "description": description,
                "metadata": metadata or {},
            })
        except Exception:
            return {}

    def log_for(
        self,
        current: Optional[Dict],
        event_type: str,
        entity_type: str,
        entity_id: str,
        description: str = "",
        metadata: Optional[Dict] = None,
    ) -> Dict:
        current = current or {}
        return self.log(
            event_type,
            entity_type,
            entity_id,
            actor_id=current.get("user_id") or "SYSTEM",
            actor_role=current.get("role") or "SYSTEM",
            description=description,
            metadata=metadata,
        )

    def get_logs(self, filters=None, page: int = 1, page_size: int = 50) -> Tuple[List[Dict[str, Any]], int]:
        return audit_repo.find_page(filters, page, page_size)


audit_service = AuditService()
