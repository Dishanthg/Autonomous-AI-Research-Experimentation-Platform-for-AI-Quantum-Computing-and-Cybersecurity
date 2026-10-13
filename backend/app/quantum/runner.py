"""Quantum execution + noise modeling (Section 26/28 Q5).

QUANTUM_HARDWARE_SAFETY (Section 27/59): this module only ever constructs
AerSimulator backends. There is no code path to a real QPU in this build;
`backend_type` is therefore always recorded as SIMULATOR. If hardware
integration is added later, it must go behind the approval/quota/allowlist
mechanism described in ADR-00X before backend_type can ever be HARDWARE.
"""

import os
import time
from dataclasses import dataclass
from typing import Optional

# Verified crash (Windows, hybrid P-core/E-core CPU): qiskit-aer's bundled
# OpenBLAS misdetects core topology and segfaults (access violation) on
# import unless pinned to a single thread. Must be set before qiskit_aer is
# imported anywhere in the process - setdefault so a deployment that already
# tuned these is left alone.
os.environ.setdefault("OPENBLAS_NUM_THREADS", "1")
os.environ.setdefault("OMP_NUM_THREADS", "1")
os.environ.setdefault("MKL_NUM_THREADS", "1")

from qiskit import QuantumCircuit, transpile
from qiskit_aer import AerSimulator
from qiskit_aer.noise import NoiseModel, depolarizing_error


@dataclass
class QuantumRunResult:
    backend_name: str
    backend_type: str  # always "SIMULATOR" in this build
    shots: int
    noise_model: Optional[str]
    execution_time_seconds: float
    measurement_counts: dict
    circuit_depth: int
    gate_count: dict
    success_probability: Optional[float]
    error_rate: Optional[float]


def build_depolarizing_noise_model(error_rate: float = 0.02) -> NoiseModel:
    """A simple, honestly-labeled noise model (Section 28 Q5): single- and
    two-qubit depolarizing error at the given rate. This is a modeling
    choice, not a measured property of any real device."""
    noise_model = NoiseModel()
    error_1q = depolarizing_error(error_rate, 1)
    error_2q = depolarizing_error(error_rate, 2)
    noise_model.add_all_qubit_quantum_error(error_1q, ["h", "x", "u", "rz", "sx"])
    noise_model.add_all_qubit_quantum_error(error_2q, ["cx", "cp", "swap"])
    return noise_model


def run_circuit(
    circuit: QuantumCircuit,
    shots: int = 1024,
    noise_model: Optional[NoiseModel] = None,
    noise_label: Optional[str] = None,
    expected_bitstring: Optional[str] = None,
    seed: int = 42,
) -> QuantumRunResult:
    backend = AerSimulator(noise_model=noise_model) if noise_model else AerSimulator()
    transpiled = transpile(circuit, backend, seed_transpiler=seed)

    start = time.time()
    job = backend.run(transpiled, shots=shots, seed_simulator=seed)
    result = job.result()
    execution_time = time.time() - start

    counts = result.get_counts()
    success_probability = None
    if expected_bitstring is not None:
        total = sum(counts.values())
        hits = counts.get(expected_bitstring, 0)
        success_probability = hits / total if total else 0.0

    error_rate = (1 - success_probability) if success_probability is not None else None

    ops = transpiled.count_ops()
    return QuantumRunResult(
        backend_name=backend.name,
        backend_type="SIMULATOR",
        shots=shots,
        noise_model=noise_label,
        execution_time_seconds=execution_time,
        measurement_counts=dict(counts),
        circuit_depth=transpiled.depth(),
        gate_count=dict(ops),
        success_probability=success_probability,
        error_rate=error_rate,
    )
