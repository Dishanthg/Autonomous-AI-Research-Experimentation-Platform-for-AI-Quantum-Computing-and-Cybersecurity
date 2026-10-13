"""In-process quantum experiment execution. Quantum circuits here are
this platform's own reviewed code
(Qiskit Aer calls via `app.quantum.circuits`/`runner`) - not LLM-generated or
otherwise untrusted code - so no sandbox tier applies (see ADR-009's
rationale for when sandboxing is required). Execution runs directly
in-process and every produced `ExperimentRun` is honestly labeled
`isolation_level="IN_PROCESS_TRUSTED"` so it is never confused with a
sandboxed (DOCKER / PROCESS_RESOURCE_LIMITED) run.

Two comparison modes are supported, both producing the same
`{"results": {"baseline": {...}, "proposed": {...}}}` shape the statistics
engine already expects (see `app.services.execution.analysis`):

  - "noise_ablation": ideal (noiseless) vs. noisy execution of the same
    circuit, same seed per repetition - Experiment 8 (Section 68).
  - "vs_classical_random": Grover search success probability vs. a real
    Monte-Carlo simulation of classical uniform-random guessing over the
    same search space and shot count - Experiment 7 (Section 67).
"""

from datetime import datetime, timezone

import numpy as np

from app.models.enums import RunStatus
from app.models.experiment import ExperimentConfig, ExperimentRun
from app.models.quantum import QuantumExperiment, QuantumRun
from app.quantum import circuits, runner
from app.quantum.runner import QuantumRunResult


class UnsupportedQuantumSpecError(ValueError):
    """Raised for a codegen_spec this module cannot honestly execute (e.g.
    an algorithm with no well-defined expected outcome to score against)."""


def _build_circuit(algorithm: str, n_qubits: int, marked_state: str | None):
    if algorithm == "bell_state":
        if n_qubits != 2:
            raise UnsupportedQuantumSpecError("bell_state is only defined for n_qubits=2")
        return circuits.build_bell_state(), "00"
    if algorithm == "grover":
        if not marked_state or len(marked_state) != n_qubits:
            raise UnsupportedQuantumSpecError(
                "grover requires 'marked_state' (a bitstring) matching 'n_qubits' in length"
            )
        return circuits.build_grover(n_qubits, marked_state), marked_state
    raise UnsupportedQuantumSpecError(
        f"Algorithm '{algorithm}' is not supported for a two-arm quantum comparison experiment "
        "(needs a well-defined expected_bitstring to score success probability against); "
        "use 'grover' or 'bell_state'."
    )


def _persist_quantum_run(
    db, quantum_experiment_id: str, run_id: str, result: QuantumRunResult
) -> None:
    db.add(
        QuantumRun(
            quantum_experiment_id=quantum_experiment_id,
            run_id=run_id,
            shots=result.shots,
            backend_name=result.backend_name,
            backend_type=result.backend_type,
            noise_model=result.noise_model,
            execution_time_seconds=result.execution_time_seconds,
            measurement_counts=result.measurement_counts,
            success_probability=result.success_probability,
            error_rate=result.error_rate,
        )
    )


def execute_quantum_config(db, config: ExperimentConfig, spec: dict) -> tuple[ExperimentRun, dict | None]:
    algorithm = spec.get("algorithm", "grover")
    n_qubits = int(spec.get("n_qubits", 3))
    marked_state = spec.get("marked_state")
    shots = int(spec.get("shots", 1024))
    num_runs = int(spec.get("num_runs") or config.num_runs or 10)
    base_seed = int(spec.get("base_seed", config.random_seed or 42))
    comparison = spec.get("comparison", "noise_ablation")

    run = ExperimentRun(
        experiment_id=config.experiment_id,
        config_id=config.id,
        status=RunStatus.RUNNING,
        started_at=datetime.now(timezone.utc),
        seed_used=base_seed,
        isolation_level="IN_PROCESS_TRUSTED",
    )
    db.add(run)
    db.flush()

    try:
        qc, expected = _build_circuit(algorithm, n_qubits, marked_state)
        if comparison not in ("noise_ablation", "vs_classical_random"):
            raise UnsupportedQuantumSpecError(f"Unknown comparison mode '{comparison}'")
    except UnsupportedQuantumSpecError as exc:
        run.status = RunStatus.FAILED
        run.stderr = str(exc)
        run.exit_code = 1
        run.finished_at = datetime.now(timezone.utc)
        db.flush()
        return run, None

    quantum_experiment = QuantumExperiment(
        experiment_id=config.experiment_id, algorithm=algorithm, qubit_count=n_qubits
    )
    db.add(quantum_experiment)
    db.flush()

    baseline_values: list[float] = []
    proposed_values: list[float] = []
    baseline_label = proposed_label = None

    if comparison == "noise_ablation":
        noise_error_rate = float(spec.get("noise_error_rate", 0.05))
        noise_model = runner.build_depolarizing_noise_model(noise_error_rate)
        noise_label = f"depolarizing_{noise_error_rate}"
        baseline_label, proposed_label = "ideal", "noisy"
        for i in range(num_runs):
            seed = base_seed + i
            ideal = runner.run_circuit(qc, shots=shots, expected_bitstring=expected, seed=seed)
            noisy = runner.run_circuit(
                qc,
                shots=shots,
                noise_model=noise_model,
                noise_label=noise_label,
                expected_bitstring=expected,
                seed=seed,
            )
            baseline_values.append(ideal.success_probability)
            proposed_values.append(noisy.success_probability)
            _persist_quantum_run(db, quantum_experiment.id, run.id, ideal)
            _persist_quantum_run(db, quantum_experiment.id, run.id, noisy)
            if quantum_experiment.circuit_depth is None:
                quantum_experiment.circuit_depth = ideal.circuit_depth
                quantum_experiment.gate_count = ideal.gate_count
    else:  # vs_classical_random
        baseline_label, proposed_label = "classical_random_guess", "grover_quantum"
        marked_index = int(expected, 2)
        n_states = 2**n_qubits
        for i in range(num_runs):
            seed = base_seed + i
            quantum_result = runner.run_circuit(qc, shots=shots, expected_bitstring=expected, seed=seed)
            rng = np.random.default_rng(seed)
            guesses = rng.integers(0, n_states, size=shots)
            classical_success = float(np.mean(guesses == marked_index))
            baseline_values.append(classical_success)
            proposed_values.append(quantum_result.success_probability)
            _persist_quantum_run(db, quantum_experiment.id, run.id, quantum_result)
            if quantum_experiment.circuit_depth is None:
                quantum_experiment.circuit_depth = quantum_result.circuit_depth
                quantum_experiment.gate_count = quantum_result.gate_count

    run.finished_at = datetime.now(timezone.utc)
    run.exit_code = 0
    run.status = RunStatus.COMPLETED
    run.stdout = (
        f"quantum in-process execution: algorithm={algorithm} n_qubits={n_qubits} "
        f"comparison={comparison} num_runs={num_runs} shots={shots}"
    )
    run.stderr = ""
    run.resource_usage = {}
    db.flush()

    metrics_json = {
        "results": {
            "baseline": {"success_probability": baseline_values},
            "proposed": {"success_probability": proposed_values},
        },
        "meta": {
            "algorithm": algorithm,
            "n_qubits": n_qubits,
            "shots": shots,
            "comparison": comparison,
            "baseline_label": baseline_label,
            "proposed_label": proposed_label,
        },
    }
    return run, metrics_json
