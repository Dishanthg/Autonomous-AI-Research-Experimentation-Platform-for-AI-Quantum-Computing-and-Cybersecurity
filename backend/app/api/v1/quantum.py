from fastapi import APIRouter, Depends, HTTPException

from app.models.enums import BackendType
from app.models.user import User
from app.quantum import circuits, runner
from app.schemas.quantum import QuantumRunOut, QuantumRunRequest
from app.security.rbac import require_any

router = APIRouter(prefix="/quantum", tags=["quantum"])


@router.post("/run", response_model=QuantumRunOut)
def run_quantum_experiment(payload: QuantumRunRequest, user: User = Depends(require_any)):
    """Section 25-28. Always executes against Aer simulator in this build;
    backend_type is always SIMULATOR (Section 27/59 - no hardware wiring
    exists here). Every response is honestly labeled as such."""
    if payload.algorithm == "bell_state":
        qc = circuits.build_bell_state()
        expected = "00"
    elif payload.algorithm == "grover":
        if not payload.marked_state or len(payload.marked_state) != payload.n_qubits:
            raise HTTPException(
                status_code=400, detail="marked_state (matching n_qubits length) is required for grover"
            )
        qc = circuits.build_grover(payload.n_qubits, payload.marked_state)
        expected = payload.marked_state
    elif payload.algorithm == "qft":
        qc = circuits.build_qft(payload.n_qubits)
        expected = None
    else:
        raise HTTPException(status_code=400, detail=f"Unsupported algorithm '{payload.algorithm}'")

    noise_model = None
    noise_label = None
    if payload.noise_error_rate:
        noise_model = runner.build_depolarizing_noise_model(payload.noise_error_rate)
        noise_label = f"depolarizing_{payload.noise_error_rate}"

    result = runner.run_circuit(
        qc,
        shots=payload.shots,
        noise_model=noise_model,
        noise_label=noise_label,
        expected_bitstring=expected,
    )

    return QuantumRunOut(
        algorithm=payload.algorithm,
        backend_name=result.backend_name,
        backend_type=BackendType(result.backend_type),
        shots=result.shots,
        noise_model=result.noise_model,
        execution_time_seconds=result.execution_time_seconds,
        circuit_depth=result.circuit_depth,
        gate_count=result.gate_count,
        measurement_counts=result.measurement_counts,
        success_probability=result.success_probability,
        error_rate=result.error_rate,
    )
