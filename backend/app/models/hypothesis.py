from typing import Optional

from sqlalchemy import JSON, Boolean, Float, ForeignKey, String, Text
from sqlalchemy import Enum as SAEnum
from sqlalchemy.orm import Mapped, mapped_column

from app.db.session import Base
from app.models.enums import HypothesisStatus
from app.models.mixins import TimestampMixin, UUIDPKMixin


class ResearchGap(Base, UUIDPKMixin, TimestampMixin):
    """Section 12 / L. Never auto-declared real; human_verification_required
    defaults true and can only be flipped by a recorded ResearchDecision."""

    __tablename__ = "research_gaps"

    project_id: Mapped[str] = mapped_column(ForeignKey("projects.id"), nullable=False)
    category: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    evidence: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    supporting_paper_ids: Mapped[Optional[list]] = mapped_column(JSON, nullable=True)
    contradicting_paper_ids: Mapped[Optional[list]] = mapped_column(JSON, nullable=True)
    confidence: Mapped[float] = mapped_column(Float, nullable=False)
    human_verification_required: Mapped[bool] = mapped_column(Boolean, default=True)
    human_verified: Mapped[bool] = mapped_column(Boolean, default=False)


class Hypothesis(Base, UUIDPKMixin, TimestampMixin):
    """Section 13/14/M. Pre-registered: decision_rule is fixed before any
    experiment runs and the Conclusion Engine evaluates against it only."""

    __tablename__ = "hypotheses"

    project_id: Mapped[str] = mapped_column(ForeignKey("projects.id"), nullable=False)
    research_question_id: Mapped[Optional[str]] = mapped_column(
        ForeignKey("research_questions.id"), nullable=True
    )
    gap_id: Mapped[Optional[str]] = mapped_column(ForeignKey("research_gaps.id"), nullable=True)

    null_hypothesis: Mapped[str] = mapped_column(Text, nullable=False)
    alternative_hypothesis: Mapped[str] = mapped_column(Text, nullable=False)
    independent_variables: Mapped[list] = mapped_column(JSON, nullable=False)
    dependent_variables: Mapped[list] = mapped_column(JSON, nullable=False)
    control_variables: Mapped[Optional[list]] = mapped_column(JSON, nullable=True)
    dataset_id: Mapped[Optional[str]] = mapped_column(ForeignKey("datasets.id"), nullable=True)
    baseline: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    expected_direction: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    evaluation_metric: Mapped[str] = mapped_column(String(255), nullable=False)
    potential_confounders: Mapped[Optional[list]] = mapped_column(JSON, nullable=True)
    limitations: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Pre-registered decision rule, e.g.
    # {"metric": "f1", "min_effect_size": 0.2, "alpha": 0.05, "direction": "greater"}
    decision_rule: Mapped[dict] = mapped_column(JSON, nullable=False)

    quality_score: Mapped[Optional[int]] = mapped_column(nullable=True)  # 0-8, Section 14 checklist
    status: Mapped[HypothesisStatus] = mapped_column(
        SAEnum(HypothesisStatus, name="hypothesis_status_enum"), default=HypothesisStatus.DRAFT
    )
    generated_by: Mapped[str] = mapped_column(
        String(100), nullable=False
    )  # "llm:<model>" or "human:<user_id>"
