"""Real, runnable quantum circuit constructors (Section 25-28).

Every circuit here is executed against Qiskit Aer - there is no fabricated
"quantum result". Results are always simulator results unless a hardware
backend is explicitly wired in (Section 27), which this build does not do.
"""

import math

from qiskit import QuantumCircuit


def build_bell_state() -> QuantumCircuit:
    """Experiment Q1: Bell state |00> + |11>."""
    qc = QuantumCircuit(2, 2, name="bell_state")
    qc.h(0)
    qc.cx(0, 1)
    qc.measure([0, 1], [0, 1])
    return qc


def build_qft(n_qubits: int) -> QuantumCircuit:
    """Experiment Q3: Quantum Fourier Transform on n_qubits, applied to the
    |0...01> input state so the output distribution is non-trivial."""
    qc = QuantumCircuit(n_qubits, n_qubits, name=f"qft_{n_qubits}")
    qc.x(0)  # prepare a non-trivial input
    _apply_qft(qc, n_qubits)
    qc.measure(range(n_qubits), range(n_qubits))
    return qc


def _apply_qft(qc: QuantumCircuit, n: int) -> None:
    for j in range(n):
        qc.h(j)
        for k in range(j + 1, n):
            angle = math.pi / (2 ** (k - j))
            qc.cp(angle, k, j)
    for i in range(n // 2):
        qc.swap(i, n - i - 1)


def build_grover(n_qubits: int, marked_state: str) -> QuantumCircuit:
    """Experiment Q2: Grover search over 2^n_qubits items for one marked
    basis state (given as a bitstring, e.g. "101"). Uses the
    textbook-optimal number of iterations: floor(pi/4 * sqrt(N))."""
    if len(marked_state) != n_qubits:
        raise ValueError("marked_state length must equal n_qubits")

    n_iterations = max(1, round((math.pi / 4) * math.sqrt(2**n_qubits)))
    qc = QuantumCircuit(n_qubits, n_qubits, name=f"grover_{n_qubits}")

    qc.h(range(n_qubits))
    for _ in range(n_iterations):
        _apply_oracle(qc, marked_state)
        _apply_diffuser(qc, n_qubits)
    qc.measure(range(n_qubits), range(n_qubits))
    return qc


def _apply_oracle(qc: QuantumCircuit, marked_state: str) -> None:
    n = len(marked_state)
    zero_bits = [i for i, b in enumerate(reversed(marked_state)) if b == "0"]
    for i in zero_bits:
        qc.x(i)
    qc.h(n - 1)
    qc.mcx(list(range(n - 1)), n - 1)
    qc.h(n - 1)
    for i in zero_bits:
        qc.x(i)


def _apply_diffuser(qc: QuantumCircuit, n: int) -> None:
    qc.h(range(n))
    qc.x(range(n))
    qc.h(n - 1)
    qc.mcx(list(range(n - 1)), n - 1)
    qc.h(n - 1)
    qc.x(range(n))
    qc.h(range(n))


def grover_iteration_count(n_qubits: int) -> int:
    return max(1, round((math.pi / 4) * math.sqrt(2**n_qubits)))
