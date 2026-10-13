from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.enums import HypothesisStatus
from app.models.hypothesis import Hypothesis
from app.models.user import User
from app.schemas.hypothesis import (
    CritiqueOut,
    HypothesisCreate,
    HypothesisOut,
    QualityCheckOut,
)
from app.security.rbac import require_any, require_researcher
from app.services.audit import record_audit
from app.services.critic.checklist import critique_hypothesis
from app.services.hypothesis.quality_check import run_quality_check

router = APIRouter(prefix="/hypotheses", tags=["hypotheses"])


@router.post("", response_model=HypothesisOut, status_code=201)
def create_hypothesis(
    payload: HypothesisCreate, user: User = Depends(require_researcher), db: Session = Depends(get_db)
):
    hyp = Hypothesis(**payload.model_dump())
    db.add(hyp)
    db.flush()
    record_audit(
        db, actor_user_id=user.id, action="hypothesis.create", resource_type="hypothesis", resource_id=hyp.id
    )
    db.commit()
    db.refresh(hyp)
    return hyp


@router.get("/{hypothesis_id}", response_model=HypothesisOut)
def get_hypothesis(hypothesis_id: str, user: User = Depends(require_any), db: Session = Depends(get_db)):
    hyp = db.get(Hypothesis, hypothesis_id)
    if not hyp:
        raise HTTPException(status_code=404, detail="Hypothesis not found")
    return hyp


@router.post("/{hypothesis_id}/quality-check", response_model=QualityCheckOut)
def quality_check(
    hypothesis_id: str, user: User = Depends(require_researcher), db: Session = Depends(get_db)
):
    """Section 14: deterministic checklist. Advances status to
    QUALITY_CHECKED only if the score passes threshold - never advances a
    hypothesis that fails, regardless of caller intent."""
    hyp = db.get(Hypothesis, hypothesis_id)
    if not hyp:
        raise HTTPException(status_code=404, detail="Hypothesis not found")

    result = run_quality_check(hyp)
    hyp.quality_score = result.score
    if result.passed:
        hyp.status = HypothesisStatus.QUALITY_CHECKED
    db.flush()
    record_audit(
        db,
        actor_user_id=user.id,
        action="hypothesis.quality_check",
        resource_type="hypothesis",
        resource_id=hyp.id,
        after_state={"score": result.score, "passed": result.passed},
    )
    db.commit()
    return QualityCheckOut(
        score=result.score, max_score=result.max_score, checks=result.checks, passed=result.passed
    )


@router.post("/{hypothesis_id}/critique", response_model=CritiqueOut)
def critique(hypothesis_id: str, user: User = Depends(require_researcher), db: Session = Depends(get_db)):
    """Section 30: independent structural critic. A hypothesis with a
    blocking objection cannot be marked APPROVED via this endpoint."""
    hyp = db.get(Hypothesis, hypothesis_id)
    if not hyp:
        raise HTTPException(status_code=404, detail="Hypothesis not found")
    if hyp.status not in (HypothesisStatus.QUALITY_CHECKED, HypothesisStatus.CRITIQUED):
        raise HTTPException(status_code=409, detail="Hypothesis must pass quality-check before critique")

    report = critique_hypothesis(hyp)
    hyp.status = HypothesisStatus.CRITIQUED if report.has_blocking else HypothesisStatus.APPROVED
    db.flush()
    record_audit(
        db,
        actor_user_id=user.id,
        action="hypothesis.critique",
        resource_type="hypothesis",
        resource_id=hyp.id,
        after_state={"objections": [o.__dict__ for o in report.objections]},
    )
    db.commit()
    return CritiqueOut(
        objections=[
            {"severity": o.severity, "category": o.category, "message": o.message} for o in report.objections
        ],
        has_blocking=report.has_blocking,
    )
