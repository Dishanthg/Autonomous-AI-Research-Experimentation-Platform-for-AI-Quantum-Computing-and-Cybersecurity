from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.audit import AuditLog
from app.models.user import User
from app.security.rbac import require_admin

router = APIRouter(prefix="/audit", tags=["audit"])


@router.get("")
def list_audit_logs(limit: int = 100, user: User = Depends(require_admin), db: Session = Depends(get_db)):
    rows = db.query(AuditLog).order_by(AuditLog.created_at.desc()).limit(limit).all()
    return [
        {
            "id": r.id,
            "actor_user_id": r.actor_user_id,
            "actor_type": r.actor_type,
            "action": r.action,
            "resource_type": r.resource_type,
            "resource_id": r.resource_id,
            "created_at": r.created_at.isoformat(),
        }
        for r in rows
    ]
