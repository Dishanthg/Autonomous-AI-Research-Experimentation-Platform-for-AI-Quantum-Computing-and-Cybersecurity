"""`make demo` - runs all three project demonstrations (Sections 91-93) end
to end using the platform's real service-layer code (not a re-implementation
of it), and writes the actual results to research/ as evidence.

Usage: python -m scripts.run_demo [--skip-cybersecurity] [--skip-quantum] [--skip-pqc]
"""

import argparse
import json
import sys
from datetime import datetime, timezone

from app.models.enums import Domain
from app.pqc.benchmark import run_comparison as run_pqc_comparison
from app.quantum.circuits import build_grover, grover_iteration_count
from app.quantum.classical_baseline import classical_exhaustive_search_cost
from app.quantum.runner import build_depolarizing_noise_model, run_circuit
from scripts._pipeline import RESEARCH_DIR, ensure_schema, get_session, run_full_pipeline


def _write_json(relative_path: str, data: dict) -> None:
    path = RESEARCH_DIR / relative_path
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = {**data, "generated_at_utc": datetime.now(timezone.utc).isoformat()}
    path.write_text(json.dumps(payload, indent=2, default=str), encoding="utf-8")
    print(f"  wrote {path.relative_to(RESEARCH_DIR.parent)}")


def demonstration_1_cybersecurity() -> dict:
    """Demonstration 1 (Section 91): 'Does graph-based representation
    improve cybersecurity anomaly detection?' Runs the full pipeline for
    real via the process-tier sandbox (ADR-009) and records the actual
    conclusion - whatever it turns out to be."""
    print("\n=== Demonstration 1: Cybersecurity (graph-based anomaly detection) ===")
    ensure_schema()
    db = get_session()
    try:
        outcome = run_full_pipeline(
            db,
            domain=Domain.CYBERSECURITY,
            project_title="Demo: Graph-based Cybersecurity Anomaly Detection",
            question_text="Does graph-based representation improve cybersecurity anomaly detection?",
            null_hypothesis="Graph-based features do not improve intrusion-detection F1 over a rule-based baseline.",
            alternative_hypothesis="Graph-based features improve intrusion-detection F1 over a rule-based baseline.",
            baseline="rule_based",
            evaluation_metric="f1",
            decision_rule={"metric": "f1", "alpha": 0.05, "min_effect_size": 0.2, "direction": "greater"},
            codegen_spec={
                "baseline": "rule_based",
                "proposed": "graph_enhanced_rf",
                "num_runs": 10,
                "base_seed": 42,
                "n_samples": 4000,
                "n_features": 12,
            },
            num_runs=10,
            metrics_requested=["f1", "pr_auc", "false_positive_rate"],
        )
        result = {
            "demonstration": "cybersecurity_graph_anomaly_detection",
            "project_id": outcome.project_id,
            "hypothesis_id": outcome.hypothesis_id,
            "experiment_id": outcome.experiment_id,
            "run_status": outcome.run_status,
            "isolation_level": outcome.isolation_level,
            "conclusion_status": outcome.conclusion_status,
            "conclusion_rationale": outcome.conclusion_rationale,
            "statistics": outcome.statistics,
            "limitations": outcome.limitations,
            "next_experiments": outcome.next_experiments,
            "quality_check_passed": outcome.quality_check_passed,
            "critic_objections": outcome.critic_objections,
        }
        print(f"  conclusion: {result['conclusion_status']} - {result['conclusion_rationale']}")
        _write_json("cybersecurity/demo_graph_anomaly_detection.json", result)
        return result
    finally:
        db.close()


def demonstration_2_quantum() -> dict:
    """Demonstration 2 (Section 92): classical exhaustive search vs
    Grover's algorithm. Real Qiskit Aer simulation, real classical
    theoretical-complexity comparison - never conflated (Section 92 item 10)."""
    print("\n=== Demonstration 2: Quantum (Grover vs classical search) ===")
    n_qubits = 4
    marked_state = "1011"
    qc = build_grover(n_qubits, marked_state)
    ideal = run_circuit(qc, shots=4000, expected_bitstring=marked_state, seed=42)

    noise_model = build_depolarizing_noise_model(0.02)
    noisy = run_circuit(
        qc,
        shots=4000,
        noise_model=noise_model,
        noise_label="depolarizing_0.02",
        expected_bitstring=marked_state,
        seed=42,
    )
    classical = classical_exhaustive_search_cost(n_qubits)

    result = {
        "demonstration": "quantum_grover_vs_classical",
        "n_qubits": n_qubits,
        "search_space_size": classical.search_space_size,
        "marked_state": marked_state,
        "grover_iterations": grover_iteration_count(n_qubits),
        "classical_theoretical": {
            "label": classical.label,
            "expected_queries": classical.expected_queries,
            "worst_case_queries": classical.worst_case_queries,
        },
        "quantum_simulated_ideal": {
            "backend_type": ideal.backend_type,
            "success_probability": ideal.success_probability,
            "circuit_depth": ideal.circuit_depth,
            "execution_time_seconds": ideal.execution_time_seconds,
        },
        "quantum_simulated_noisy": {
            "backend_type": noisy.backend_type,
            "noise_model": noisy.noise_model,
            "success_probability": noisy.success_probability,
            "error_rate": noisy.error_rate,
        },
        "note": "quantum_simulated_* are SIMULATOR results (Section 27/59 - no "
        "hardware wiring in this build); classical_theoretical is analytic "
        "complexity, not a measured value. These are three different kinds "
        "of number and must never be conflated.",
    }
    print(
        f"  Grover ideal success={ideal.success_probability:.3f}, "
        f"noisy success={noisy.success_probability:.3f}, "
        f"classical expected queries={classical.expected_queries}"
    )
    _write_json("quantum/demo_grover_vs_classical.json", result)
    return result


def demonstration_3_pqc() -> dict:
    """Demonstration 3 (Section 93): classical vs PQC cryptographic
    benchmark. Reports honestly if the PQC arm is unavailable."""
    print("\n=== Demonstration 3: PQC (classical vs post-quantum benchmark) ===")
    report = run_pqc_comparison(n_runs=20)
    result = {
        "demonstration": "pqc_classical_vs_postquantum",
        "pqc_available": report.pqc_available,
        "status_note": report.status_note,
        "classical_results": [
            {
                "scheme": r.scheme,
                "operation": r.operation,
                "mean_seconds": r.mean_seconds,
                "artifact_size_bytes": r.artifact_size_bytes,
            }
            for r in report.classical_results
        ],
        "pqc_results": [
            {
                "scheme": r.scheme,
                "operation": r.operation,
                "mean_seconds": r.mean_seconds,
                "artifact_size_bytes": r.artifact_size_bytes,
            }
            for r in report.pqc_results
        ],
    }
    print(f"  pqc_available={report.pqc_available}: {report.status_note}")
    _write_json("pqc/demo_classical_vs_pqc.json", result)
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description="Run ResearchMind-Q demonstrations")
    parser.add_argument("--skip-cybersecurity", action="store_true")
    parser.add_argument("--skip-quantum", action="store_true")
    parser.add_argument("--skip-pqc", action="store_true")
    args = parser.parse_args()

    results = {}
    if not args.skip_cybersecurity:
        results["cybersecurity"] = demonstration_1_cybersecurity()
    if not args.skip_quantum:
        results["quantum"] = demonstration_2_quantum()
    if not args.skip_pqc:
        results["pqc"] = demonstration_3_pqc()

    print("\n=== Summary ===")
    for name, r in results.items():
        print(f"  {name}: see research/{name}/")
    return 0


if __name__ == "__main__":
    sys.exit(main())
