from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.user import User
from app.security.rbac import require_any
from app.services.memory import queries as memory_queries

router = APIRouter(prefix="/memory", tags=["memory"])


@router.get("/{project_id}/prior-experiments")
def prior_experiments(
    project_id: str,
    domain: str | None = None,
    user: User = Depends(require_any),
    db: Session = Depends(get_db),
):
    return memory_queries.get_prior_experiments(db, project_id, domain)


@router.get("/{project_id}/failed-experiments")
def failed_experiments(project_id: str, user: User = Depends(require_any), db: Session = Depends(get_db)):
    return memory_queries.get_failed_experiments(db, project_id)


@router.get("/{project_id}/unresolved-hypotheses")
def unresolved_hypotheses(project_id: str, user: User = Depends(require_any), db: Session = Depends(get_db)):
    return memory_queries.get_unresolved_hypotheses(db, project_id)
