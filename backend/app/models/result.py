from typing import Optional

from sqlalchemy import JSON, Float, ForeignKey, String, Text
from sqlalchemy import Enum as SAEnum
from sqlalchemy.orm import Mapped, mapped_column

from app.db.session import Base
from app.models.enums import ConclusionStatus
from app.models.mixins import TimestampMixin, UUIDPKMixin


class Result(Base, UUIDPKMixin, TimestampMixin):
    """Written ONLY by the deterministic Result Analyzer / Statistical
    Analyst - never by an LLM call (Section 32/39 invariant)."""

    __tablename__ = "results"

    experiment_id: Mapped[str] = mapped_column(ForeignKey("experiments.id"), nullable=False)
    hypothesis_id: Mapped[str] = mapped_column(ForeignKey("hypotheses.id"), nullable=False)
    computed_by: Mapped[str] = mapped_column(
        String(100), nullable=False, default="deterministic:result_analyzer"
    )
    conclusion_status: Mapped[Optional[ConclusionStatus]] = mapped_column(
        SAEnum(ConclusionStatus, name="conclusion_status_enum"), nullable=True
    )
    conclusion_rationale: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    human_approved: Mapped[bool] = mapped_column(default=False)


class Metric(Base, UUIDPKMixin, TimestampMixin):
    __tablename__ = "metrics"

    result_id: Mapped[str] = mapped_column(ForeignKey("results.id"), nullable=False)
    run_id: Mapped[Optional[str]] = mapped_column(ForeignKey("experiment_runs.id"), nullable=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)  # f1, pr_auc, latency_ms, ...
    value: Mapped[float] = mapped_column(Float, nullable=False)
    unit: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)


class StatisticalTest(Base, UUIDPKMixin, TimestampMixin):
    __tablename__ = "statistical_tests"

    result_id: Mapped[str] = mapped_column(ForeignKey("results.id"), nullable=False)
    metric_name: Mapped[str] = mapped_column(String(100), nullable=False)
    test_name: Mapped[str] = mapped_column(
        String(100), nullable=False
    )  # t-test, mann-whitney, bootstrap-ci, ...
    statistic: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    p_value: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    effect_size: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    effect_size_type: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    ci_lower: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    ci_upper: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    ci_level: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    correction_method: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    raw_output: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)


class Limitation(Base, UUIDPKMixin, TimestampMixin):
    __tablename__ = "limitations"

    experiment_id: Mapped[Optional[str]] = mapped_column(ForeignKey("experiments.id"), nullable=True)
    project_id: Mapped[Optional[str]] = mapped_column(ForeignKey("projects.id"), nullable=True)
    category: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    detected_by: Mapped[str] = mapped_column(
        String(100), nullable=False
    )  # "deterministic:..." or "llm:..." or "human:..."
