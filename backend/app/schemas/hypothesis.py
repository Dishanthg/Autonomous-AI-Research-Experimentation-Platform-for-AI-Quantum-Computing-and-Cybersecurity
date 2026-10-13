from typing import Optional

from pydantic import BaseModel

from app.models.enums import HypothesisStatus


class HypothesisCreate(BaseModel):
    project_id: str
    research_question_id: Optional[str] = None
    gap_id: Optional[str] = None
    null_hypothesis: str
    alternative_hypothesis: str
    independent_variables: list[str]
    dependent_variables: list[str]
    control_variables: Optional[list[str]] = None
    dataset_id: Optional[str] = None
    baseline: Optional[str] = None
    expected_direction: Optional[str] = None
    evaluation_metric: str
    potential_confounders: Optional[list[str]] = None
    limitations: Optional[str] = None
    decision_rule: dict  # {"metric": str, "alpha": float, "min_effect_size": float, "direction": str}
    generated_by: str = "human"


class HypothesisOut(BaseModel):
    id: str
    project_id: str
    null_hypothesis: str
    alternative_hypothesis: str
    independent_variables: list
    dependent_variables: list
    evaluation_metric: str
    decision_rule: dict
    quality_score: Optional[int] = None
    status: HypothesisStatus

    class Config:
        from_attributes = True


class QualityCheckOut(BaseModel):
    score: int
    max_score: int
    checks: dict[str, bool]
    passed: bool


class ObjectionOut(BaseModel):
    severity: str
    category: str
    message: str


class CritiqueOut(BaseModel):
    objections: list[ObjectionOut]
    has_blocking: bool
