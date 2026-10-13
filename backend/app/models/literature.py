from typing import Optional

from sqlalchemy import JSON, ForeignKey, Integer, String, Text
from sqlalchemy import Enum as SAEnum
from sqlalchemy.orm import Mapped, mapped_column

from app.db.session import Base
from app.models.enums import ClaimType
from app.models.mixins import TimestampMixin, UUIDPKMixin


class Paper(Base, UUIDPKMixin, TimestampMixin):
    """Never fabricated: every field is either sourced from a real API
    response (arXiv / Semantic Scholar / Crossref) or left NULL."""

    __tablename__ = "papers"

    title: Mapped[str] = mapped_column(Text, nullable=False)
    authors: Mapped[Optional[list]] = mapped_column(JSON, nullable=True)
    year: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    venue: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    doi: Mapped[Optional[str]] = mapped_column(String(255), nullable=True, index=True)
    url: Mapped[Optional[str]] = mapped_column(String(1000), nullable=True)
    source: Mapped[str] = mapped_column(String(50), nullable=False)  # arxiv|semantic_scholar|crossref
    external_id: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    abstract: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    keywords: Mapped[Optional[list]] = mapped_column(JSON, nullable=True)
    raw_metadata: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)


class PaperClaim(Base, UUIDPKMixin, TimestampMixin):
    """Paper -> Section -> Claim -> Evidence provenance chain (Section 10/J)."""

    __tablename__ = "paper_claims"

    paper_id: Mapped[str] = mapped_column(ForeignKey("papers.id"), nullable=False)
    section: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    source_span: Mapped[str] = mapped_column(Text, nullable=False)  # exact quoted source text
    claim_text: Mapped[str] = mapped_column(Text, nullable=False)
    claim_type: Mapped[ClaimType] = mapped_column(SAEnum(ClaimType, name="claim_type_enum"), nullable=False)
    # Non-null only when claim_type == EXPERIMENTALLY_OBSERVED (enforced in service layer + DB check constraint)
    run_id: Mapped[Optional[str]] = mapped_column(ForeignKey("experiment_runs.id"), nullable=True)
    extracted_by: Mapped[str] = mapped_column(
        String(100), nullable=False
    )  # "llm:<model>" or "human:<user_id>"
    human_verified: Mapped[bool] = mapped_column(default=False)


class Dataset(Base, UUIDPKMixin, TimestampMixin):
    __tablename__ = "datasets"

    name: Mapped[str] = mapped_column(String(255), nullable=False)
    source: Mapped[str] = mapped_column(String(500), nullable=False)
    license: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    features: Mapped[Optional[list]] = mapped_column(JSON, nullable=True)
    limitations: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    citation: Mapped[Optional[str]] = mapped_column(Text, nullable=True)


class DatasetVersion(Base, UUIDPKMixin, TimestampMixin):
    __tablename__ = "dataset_versions"

    dataset_id: Mapped[str] = mapped_column(ForeignKey("datasets.id"), nullable=False)
    version_tag: Mapped[str] = mapped_column(String(100), nullable=False)
    checksum: Mapped[Optional[str]] = mapped_column(String(128), nullable=True)
    preprocessing: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    row_count: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)


class Method(Base, UUIDPKMixin, TimestampMixin):
    __tablename__ = "methods"
    name: Mapped[str] = mapped_column(String(255), nullable=False, unique=True)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)


class Algorithm(Base, UUIDPKMixin, TimestampMixin):
    __tablename__ = "algorithms"
    name: Mapped[str] = mapped_column(String(255), nullable=False, unique=True)
    method_id: Mapped[Optional[str]] = mapped_column(ForeignKey("methods.id"), nullable=True)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
