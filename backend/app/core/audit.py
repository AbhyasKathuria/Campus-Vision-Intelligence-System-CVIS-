from typing import Optional, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.models import AuditLog, User
from app.models.enums import UserRole

async def log_audit_event(
    db: AsyncSession,
    actor: Optional[User],
    action: str,
    target_type: str,
    target_id: str,
    metadata: Optional[Dict[str, Any]] = None
) -> AuditLog:
    """
    Creates an immutable audit log entry in the database.
    """
    entry = AuditLog(
        actor_id=actor.id if actor else None,
        actor_role=actor.role if actor else None,
        action=action,
        target_type=target_type,
        target_id=str(target_id),
        metadata_json=metadata or {}
    )
    db.add(entry)
    await db.flush()
    return entry
