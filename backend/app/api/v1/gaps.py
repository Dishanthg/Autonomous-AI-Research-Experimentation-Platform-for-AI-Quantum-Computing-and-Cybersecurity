"""Gap Analyzer API.

Before this module the deterministic Cypher queries
(`app.services.knowledge_graph.gap_queries`) and the `GapNarrativeAgent`
existed with no HTTP surface at all - this wires them up, still behind the
project's usual guardrails: every stored `ResearchGap` defaults
`human_verification_required=True` and can only be flipped by a recorded
`ResearchDecision` (Section 12's hard requirement), never by the analyze
call itself.
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.agents.gap_narrative_agent import GapNarrativeAgent, compute_confidence
from app.db.session import get_db
from app.models.enums import DecisionOutcome, GateType
from app.models.hypothesis import ResearchGap
from app.models.project import Project, ResearchDecision
from app.models.user import User
from app.schemas.gap import GapAnalyzeRequest, GapOut, GapVerifyRequest
from app.security.rbac import require_any, require_researcher
from app.services.audit import record_audit
from app.services.knowledge_graph.client import KnowledgeGraphUnavailableError, get_kg_client
from app.services.knowledge_graph.gap_queries import (
    find_methods_with_no_dataset_overlap,
    find_sparse_method_dataset_pairs,
)
from app.services.llm.provider import LLMNotConfiguredError, get_llm_provider

router = APIRouter(prefix="/gaps", tags=["gaps"])


@router.post("/analyze", response_model=list[GapOut], status_code=201)
def analyze_gaps(
    payload: GapAnalyzeRequest, user: User = Depends(require_researcher), db: Session = Depends(get_db)
):
    project = db.get(Project, payload.project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    client = get_kg_client()
    try:
        candidates = find_sparse_method_dataset_pairs(client, min_papers=payload.min_papers)
        candidates += find_methods_with_no_dataset_overlap(client)
    except KnowledgeGraphUnavailableError as exc:
        raise HTTPException(status_code=503, detail=f"Knowledge graph unavailable: {exc}")

    agent = GapNarrativeAgent(get_llm_provider()) if payload.narrate else None

    created: list[ResearchGap] = []
    for candidate in candidates:
        if agent is not None:
            try:
                narrated = agent.narrate(candidate)
            except LLMNotConfiguredError as exc:
                raise HTTPException(status_code=503, detail=f"LLM provider unavailable: {exc}")
            description, confidence = narrated.narrative, narrated.confidence
        else:
            description, confidence = candidate.description, compute_confidence(candidate)

        gap = ResearchGap(
            project_id=payload.project_id,
            category=candidate.category,
            description=description,
            evidence=candidate.evidence,
            confidence=confidence,
            human_verification_required=True,
            human_verified=False,
        )
        db.add(gap)
        created.append(gap)

    db.flush()
    record_audit(
        db,
        actor_user_id=user.id,
        action="gap.analyze",
        resource_type="project",
        resource_id=payload.project_id,
        after_state={"gap_count": len(created)},
    )
    db.commit()
    for gap in created:
        db.refresh(gap)
    return created


@router.get("", response_model=list[GapOut])
def list_gaps(
    project_id: str | None = None, user: User = Depends(require_any), db: Session = Depends(get_db)
):
    q = db.query(ResearchGap)
    if project_id:
        q = q.filter(ResearchGap.project_id == project_id)
    return q.order_by(ResearchGap.created_at.desc()).all()


@router.post("/{gap_id}/verify", response_model=GapOut)
def verify_gap(
    gap_id: str,
    payload: GapVerifyRequest,
    user: User = Depends(require_researcher),
    db: Session = Depends(get_db),
):
    """The only code path allowed to flip `human_verified` (Section 12) -
    always writes a recorded ResearchDecision, whichever way the human
    calls it, so a gap is never silently treated as confirmed."""
    gap = db.get(ResearchGap, gap_id)
    if not gap:
        raise HTTPException(status_code=404, detail="Gap not found")

    gap.human_verified = payload.verified

    db.add(
        ResearchDecision(
            project_id=gap.project_id,
            gate_type=GateType.GAP_VERIFICATION,
            subject_type="research_gap",
            subject_id=gap.id,
            outcome=DecisionOutcome.APPROVED if payload.verified else DecisionOutcome.REJECTED,
            actor_user_id=user.id,
            rationale=payload.rationale,
        )
    )
    db.flush()
    record_audit(
        db, actor_user_id=user.id, action="gap.verify", resource_type="research_gap", resource_id=gap.id
    )
    db.commit()
    db.refresh(gap)
    return gap
