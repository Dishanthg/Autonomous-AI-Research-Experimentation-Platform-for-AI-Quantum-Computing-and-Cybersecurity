from typing import Optional

from pydantic import BaseModel


class GapAnalyzeRequest(BaseModel):
    project_id: str
    min_papers: int = 1
    # If True, runs the LLM narrative-framing pass (GapNarrativeAgent) over
    # each deterministic candidate; raises 503 if no LLM provider is
    # configured. If False (default), stores the deterministic candidate's
    # own description/confidence with no LLM call at all.
    narrate: bool = False


class GapOut(BaseModel):
    id: str
    project_id: str
    category: str
    description: str
    evidence: Optional[dict] = None
    confidence: float
    human_verification_required: bool
    human_verified: bool

    class Config:
        from_attributes = True


class GapVerifyRequest(BaseModel):
    verified: bool
    rationale: Optional[str] = None
