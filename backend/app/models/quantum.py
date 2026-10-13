from typing import Optional

from sqlalchemy import JSON, Float, ForeignKey, Integer, String, Text
from sqlalchemy import Enum as SAEnum
from sqlalchemy.orm import Mapped, mapped_column

from app.db.session import Base
from app.models.enums import BackendType
from app.models.mixins import TimestampMixin, UUIDPKMixin


class QuantumExperiment(Base, UUIDPKMixin, TimestampMixin):
    __tablename__ = "quantum_experiments"

    experiment_id: Mapped[str] = mapped_column(ForeignKey("experiments.id"), nullable=False)
    algorithm: Mapped[str] = mapped_column(
        String(100), nullable=False
    )  # bell_state|grover|qft|shor_small|noisy_vs_ideal
    qubit_count: Mapped[int] = mapped_column(Integer, nullable=False)
    circuit_qasm: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    circuit_depth: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    gate_count: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)


class QuantumRun(Base, UUIDPKMixin, TimestampMixin):
    """Section 26. backend_type is enforced not-null - every quantum run
    result must be explicitly labeled SIMULATOR or HARDWARE (Section 27/52)."""

    __tablename__ = "quantum_runs"

    quantum_experiment_id: Mapped[str] = mapped_column(ForeignKey("quantum_experiments.id"), nullable=False)
    run_id: Mapped[str] = mapped_column(ForeignKey("experiment_runs.id"), nullable=False)
    shots: Mapped[int] = mapped_column(Integer, nullable=False)
    backend_name: Mapped[str] = mapped_column(String(100), nullable=False)
    backend_type: Mapped[BackendType] = mapped_column(
        SAEnum(BackendType, name="backend_type_enum"), nullable=False
    )
    noise_model: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    execution_time_seconds: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    measurement_counts: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    success_probability: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    error_rate: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
