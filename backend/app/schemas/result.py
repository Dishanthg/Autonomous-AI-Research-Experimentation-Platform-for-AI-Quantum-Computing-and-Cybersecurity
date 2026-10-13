from typing import Optional

from pydantic import BaseModel

from app.models.enums import ConclusionStatus


class MetricOut(BaseModel):
    name: str
    value: float
    unit: Optional[str] = None

    class Config:
        from_attributes = True


class StatisticalTestOut(BaseModel):
    metric_name: str
    test_name: str
    statistic: Optional[float] = None
    p_value: Optional[float] = None
    effect_size: Optional[float] = None
    effect_size_type: Optional[str] = None
    ci_lower: Optional[float] = None
    ci_upper: Optional[float] = None
    ci_level: Optional[float] = None

    class Config:
        from_attributes = True


class ResultOut(BaseModel):
    id: str
    experiment_id: str
    hypothesis_id: str
    computed_by: str
    conclusion_status: Optional[ConclusionStatus] = None
    conclusion_rationale: Optional[str] = None
    human_approved: bool

    class Config:
        from_attributes = True
