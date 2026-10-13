from typing import Optional

from pydantic import BaseModel

from app.models.enums import BackendType


class QuantumRunRequest(BaseModel):
    algorithm: str  # bell_state | grover | qft | noisy_vs_ideal
    n_qubits: int = 3
    marked_state: Optional[str] = None  # required for grover
    shots: int = 2000
    noise_error_rate: Optional[float] = None  # if set, also runs a noisy comparison


class QuantumRunOut(BaseModel):
    algorithm: str
    backend_name: str
    backend_type: BackendType
    shots: int
    noise_model: Optional[str] = None
    execution_time_seconds: float
    circuit_depth: int
    gate_count: dict
    measurement_counts: dict
    success_probability: Optional[float] = None
    error_rate: Optional[float] = None
