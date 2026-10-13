from typing import Optional

from sqlalchemy.orm import Session

from app.models.audit import AuditLog


def record_audit(
    db: Session,
    *,
    actor_user_id: Optional[str],
    action: str,
    resource_type: str,
    resource_id: Optional[str] = None,
    before_state: Optional[dict] = None,
    after_state: Optional[dict] = None,
    actor_type: str = "human",
) -> AuditLog:
    """Every gate decision, state transition, and sandbox execution start/stop
    must call this. Never fails silently: if the DB write itself fails, the
    caller's transaction should abort rather than proceed unaudited."""
    entry = AuditLog(
        actor_user_id=actor_user_id,
        actor_type=actor_type,
        action=action,
        resource_type=resource_type,
        resource_id=resource_id,
        before_state=before_state,
        after_state=after_state,
    )
    db.add(entry)
    db.flush()
    return entry
