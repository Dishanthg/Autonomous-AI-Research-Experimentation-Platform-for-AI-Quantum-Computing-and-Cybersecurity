from typing import Optional

from sqlalchemy import JSON, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy import Enum as SAEnum
from sqlalchemy.orm import Mapped, mapped_column

from app.db.session import Base
from app.models.enums import Domain, ExperimentStatus, RunStatus
from app.models.mixins import TimestampMixin, UUIDPKMixin


class Experiment(Base, UUIDPKMixin, TimestampMixin):
    """Rule 9: unique id. Rule 10: traceable to dataset/code/config/env/model
    via its ExperimentConfig + ExperimentRun children."""

    __tablename__ = "experiments"

    project_id: Mapped[str] = mapped_column(ForeignKey("projects.id"), nullable=False)
    hypothesis_id: Mapped[str] = mapped_column(ForeignKey("hypotheses.id"), nullable=False)
    domain: Mapped[Domain] = mapped_column(SAEnum(Domain, name="domain_enum"))
    objective: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[ExperimentStatus] = mapped_column(
        SAEnum(ExperimentStatus, name="experiment_status_enum"), default=ExperimentStatus.DRAFT
    )
    num_runs_planned: Mapped[int] = mapped_column(Integer, default=1)


class ExperimentConfig(Base, UUIDPKMixin, TimestampMixin):
    """Immutable once approved. A new change creates a new version row -
    never edited in place (Rule 10 / Section N)."""

    __tablename__ = "experiment_configs"

    experiment_id: Mapped[str] = mapped_column(ForeignKey("experiments.id"), nullable=False)
    version: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    dataset_id: Mapped[Optional[str]] = mapped_column(ForeignKey("datasets.id"), nullable=True)
    dataset_version_id: Mapped[Optional[str]] = mapped_column(
        ForeignKey("dataset_versions.id"), nullable=True
    )
    model_spec: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    baseline_spec: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    features: Mapped[Optional[list]] = mapped_column(JSON, nullable=True)
    hyperparameters: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    random_seed: Mapped[int] = mapped_column(Integer, default=42)
    num_runs: Mapped[int] = mapped_column(Integer, default=1)
    metrics_requested: Mapped[list] = mapped_column(JSON, nullable=False)
    resource_limits: Mapped[dict] = mapped_column(JSON, nullable=False)
    software_environment: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    approved: Mapped[bool] = mapped_column(default=False)
    approved_by_user_id: Mapped[Optional[str]] = mapped_column(ForeignKey("users.id"), nullable=True)
    generated_code_path: Mapped[Optional[str]] = mapped_column(String(1000), nullable=True)
    git_commit: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)


class ExperimentRun(Base, UUIDPKMixin, TimestampMixin):
    """One sandbox execution. Full stdout/stderr/exit/resource trace captured
    regardless of outcome (Section 20/O)."""

    __tablename__ = "experiment_runs"

    experiment_id: Mapped[str] = mapped_column(ForeignKey("experiments.id"), nullable=False)
    config_id: Mapped[str] = mapped_column(ForeignKey("experiment_configs.id"), nullable=False)
    status: Mapped[RunStatus] = mapped_column(
        SAEnum(RunStatus, name="run_status_enum"), default=RunStatus.PENDING
    )
    started_at: Mapped[Optional[str]] = mapped_column(DateTime(timezone=True), nullable=True)
    finished_at: Mapped[Optional[str]] = mapped_column(DateTime(timezone=True), nullable=True)
    exit_code: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    stdout: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    stderr: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    resource_usage: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)  # cpu, mem, wall time
    container_image: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    container_id: Mapped[Optional[str]] = mapped_column(String(128), nullable=True)
    seed_used: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    # "DOCKER" or "PROCESS_RESOURCE_LIMITED" (app.sandbox.base.IsolationLevel) -
    # every run is honestly labeled with the isolation tier that produced it
    # (ADR-009); never displayed or reported without this alongside it.
    isolation_level: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)


class Artifact(Base, UUIDPKMixin, TimestampMixin):
    __tablename__ = "artifacts"

    run_id: Mapped[str] = mapped_column(ForeignKey("experiment_runs.id"), nullable=False)
    artifact_type: Mapped[str] = mapped_column(
        String(100), nullable=False
    )  # code|config|log|plot|table|report
    path: Mapped[str] = mapped_column(String(1000), nullable=False)
    checksum: Mapped[Optional[str]] = mapped_column(String(128), nullable=True)


class MLModel(Base, UUIDPKMixin, TimestampMixin):
    __tablename__ = "models"
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    domain: Mapped[Domain] = mapped_column(SAEnum(Domain, name="domain_enum"))
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)


class ModelVersion(Base, UUIDPKMixin, TimestampMixin):
    __tablename__ = "model_versions"
    model_id: Mapped[str] = mapped_column(ForeignKey("models.id"), nullable=False)
    version_tag: Mapped[str] = mapped_column(String(100), nullable=False)
    artifact_path: Mapped[Optional[str]] = mapped_column(String(1000), nullable=True)
    training_config: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
