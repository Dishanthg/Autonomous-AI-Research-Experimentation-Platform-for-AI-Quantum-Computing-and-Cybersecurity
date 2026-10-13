"""`make quantum` - CLI for running real Qiskit Aer quantum experiments
without going through the API (Section 25-28). Every result printed here is
a real simulator run; nothing is fabricated or pre-computed.

Usage:
  python -m app.quantum.cli bell --shots 2000
  python -m app.quantum.cli grover --n-qubits 4 --marked 1011 --shots 4000
  python -m app.quantum.cli qft --n-qubits 3 --shots 1000
  python -m app.quantum.cli noise --n-qubits 3 --marked 101 --error-rate 0.05
"""

import argparse
import json
import sys

from app.quantum import circuits, runner
from app.quantum.classical_baseline import classical_exhaustive_search_cost


def _print_result(label: str, result) -> None:
    print(f"\n=== {label} ===")
    print(f"backend: {result.backend_name} [{result.backend_type}]")
    if result.noise_model:
        print(f"noise model: {result.noise_model}")
    print(f"shots: {result.shots}  circuit depth: {result.circuit_depth}")
    print(f"execution time: {result.execution_time_seconds * 1000:.2f} ms")
    if result.success_probability is not None:
        print(f"success probability: {result.success_probability * 100:.2f}%")
    if result.error_rate is not None:
        print(f"error rate: {result.error_rate * 100:.2f}%")
    print(f"measurement counts: {json.dumps(result.measurement_counts)}")


def cmd_bell(args) -> int:
    qc = circuits.build_bell_state()
    result = runner.run_circuit(qc, shots=args.shots, expected_bitstring="00", seed=args.seed)
    _print_result("Bell state (Q1)", result)
    return 0


def cmd_grover(args) -> int:
    if len(args.marked) != args.n_qubits:
        print(f"error: --marked must be {args.n_qubits} bits long", file=sys.stderr)
        return 1
    qc = circuits.build_grover(args.n_qubits, args.marked)
    result = runner.run_circuit(qc, shots=args.shots, expected_bitstring=args.marked, seed=args.seed)
    _print_result(f"Grover search (Q2, n={args.n_qubits})", result)

    classical = classical_exhaustive_search_cost(args.n_qubits)
    print(
        f"\nclassical exhaustive search (THEORETICAL_COMPLEXITY): "
        f"expected {classical.expected_queries} queries, worst case {classical.worst_case_queries} "
        f"over a search space of {classical.search_space_size}"
    )
    return 0


def cmd_qft(args) -> int:
    qc = circuits.build_qft(args.n_qubits)
    result = runner.run_circuit(qc, shots=args.shots, seed=args.seed)
    _print_result(f"Quantum Fourier Transform (Q3, n={args.n_qubits})", result)
    return 0


def cmd_noise(args) -> int:
    if len(args.marked) != args.n_qubits:
        print(f"error: --marked must be {args.n_qubits} bits long", file=sys.stderr)
        return 1
    qc = circuits.build_grover(args.n_qubits, args.marked)
    ideal = runner.run_circuit(qc, shots=args.shots, expected_bitstring=args.marked, seed=args.seed)
    _print_result("Grover - ideal simulator", ideal)

    noise_model = runner.build_depolarizing_noise_model(args.error_rate)
    noisy = runner.run_circuit(
        qc,
        shots=args.shots,
        noise_model=noise_model,
        noise_label=f"depolarizing_{args.error_rate}",
        expected_bitstring=args.marked,
        seed=args.seed,
    )
    _print_result(f"Grover - noisy simulator (Q5, error_rate={args.error_rate})", noisy)

    print(
        f"\ndelta: ideal success {ideal.success_probability * 100:.2f}% vs. noisy "
        f"{noisy.success_probability * 100:.2f}% "
        f"(-{(ideal.success_probability - noisy.success_probability) * 100:.2f} percentage points)"
    )
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="ResearchMind-Q quantum experiment CLI")
    parser.add_argument("--seed", type=int, default=42)
    sub = parser.add_subparsers(dest="command", required=True)

    p_bell = sub.add_parser("bell", help="Bell state entanglement (Q1)")
    p_bell.add_argument("--shots", type=int, default=2000)
    p_bell.set_defaults(func=cmd_bell)

    p_grover = sub.add_parser("grover", help="Grover search (Q2)")
    p_grover.add_argument("--n-qubits", type=int, default=3)
    p_grover.add_argument("--marked", type=str, default="101")
    p_grover.add_argument("--shots", type=int, default=2000)
    p_grover.set_defaults(func=cmd_grover)

    p_qft = sub.add_parser("qft", help="Quantum Fourier Transform (Q3)")
    p_qft.add_argument("--n-qubits", type=int, default=3)
    p_qft.add_argument("--shots", type=int, default=1000)
    p_qft.set_defaults(func=cmd_qft)

    p_noise = sub.add_parser("noise", help="Ideal vs. noisy Grover (Q5)")
    p_noise.add_argument("--n-qubits", type=int, default=3)
    p_noise.add_argument("--marked", type=str, default="101")
    p_noise.add_argument("--shots", type=int, default=2000)
    p_noise.add_argument("--error-rate", type=float, default=0.05)
    p_noise.set_defaults(func=cmd_noise)

    args = parser.parse_args()
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
