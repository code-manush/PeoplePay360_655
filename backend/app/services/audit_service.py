"""
AuditService — records audit events for important operations.

FUTURE DATABASE INTEGRATION:
Replace DummyAuditRepository with AivenAuditRepository.
The service interface remains the same.
"""
from datetime import datetime, timezone
from typing import Dict, Any, Optional

from app.repositories.postgres_repos import PostgresAuditRepository

audit_repo = PostgresAuditRepository()


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
        return audit_repo.create({
            "event_type": event_type,
            "entity_type": entity_type,
            "entity_id": entity_id,
            "actor_id": actor_id,
            "actor_role": actor_role,
            "description": description,
            "metadata": metadata or {},
        })

    def get_logs(self, filters=None):
        return audit_repo.find_all(filters)


audit_service = AuditService()
