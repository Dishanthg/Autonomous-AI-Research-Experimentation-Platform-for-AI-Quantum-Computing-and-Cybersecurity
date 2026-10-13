from typing import Optional

from sqlalchemy import JSON, ForeignKey, String, Text
from sqlalchemy import Enum as SAEnum
from sqlalchemy.orm import Mapped, mapped_column

from app.db.session import Base
from app.models.enums import DecisionOutcome, Domain, GateType
from app.models.mixins import TimestampMixin, UUIDPKMixin


class Project(Base, UUIDPKMixin, TimestampMixin):
    __tablename__ = "projects"

    title: Mapped[str] = mapped_column(String(500), nullable=False)
    domain: Mapped[Domain] = mapped_column(SAEnum(Domain, name="domain_enum"), nullable=False)
    owner_id: Mapped[str] = mapped_column(ForeignKey("users.id"), nullable=False)
    objectives: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    conclusions: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    limitations: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    future_work: Mapped[Optional[str]] = mapped_column(Text, nullable=True)


class ResearchQuestion(Base, UUIDPKMixin, TimestampMixin):
    __tablename__ = "research_questions"

    project_id: Mapped[str] = mapped_column(ForeignKey("projects.id"), nullable=False)
    question_text: Mapped[str] = mapped_column(Text, nullable=False)
    domain: Mapped[Domain] = mapped_column(SAEnum(Domain, name="domain_enum"))
    is_primary: Mapped[bool] = mapped_column(default=False)


class ResearchDecision(Base, UUIDPKMixin, TimestampMixin):
    """Every human approval-gate decision. This is the enforcement record
    for Rule: human approval required before execution/publication/etc."""

    __tablename__ = "research_decisions"

    project_id: Mapped[str] = mapped_column(ForeignKey("projects.id"), nullable=False)
    gate_type: Mapped[GateType] = mapped_column(SAEnum(GateType, name="gate_type_enum"), nullable=False)
    subject_type: Mapped[str] = mapped_column(String(100), nullable=False)  # e.g. "experiment", "hypothesis"
    subject_id: Mapped[str] = mapped_column(String(64), nullable=False)
    outcome: Mapped[DecisionOutcome] = mapped_column(SAEnum(DecisionOutcome, name="decision_outcome_enum"))
    actor_user_id: Mapped[str] = mapped_column(ForeignKey("users.id"), nullable=False)
    rationale: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    payload: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)


class ResearchFeedback(Base, UUIDPKMixin, TimestampMixin):
    """Free-text researcher feedback, consumed by Research Memory (Section 34)."""

    __tablename__ = "research_feedback"

    project_id: Mapped[str] = mapped_column(ForeignKey("projects.id"), nullable=False)
    subject_type: Mapped[str] = mapped_column(String(100), nullable=False)
    subject_id: Mapped[str] = mapped_column(String(64), nullable=False)
    author_user_id: Mapped[str] = mapped_column(ForeignKey("users.id"), nullable=False)
    comment: Mapped[str] = mapped_column(Text, nullable=False)
