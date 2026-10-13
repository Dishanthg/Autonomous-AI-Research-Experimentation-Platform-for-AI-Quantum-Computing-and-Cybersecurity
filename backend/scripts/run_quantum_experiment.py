"""Experiments 7 & 8 (Section 67/68): real quantum-domain research runs
through the full pipeline (project -> hypothesis -> config -> critic ->
Gate 1 -> Gate 2 -> in-process quantum execution -> statistics ->
conclusion), exactly like `run_research_pipeline.py` does for AI.

Experiment 7 (Section 67): does Grover's algorithm's per-shot success
probability genuinely exceed a real Monte-Carlo simulation of classical
uniform-random guessing over the same search space?

Experiment 8 (Section 68, noise ablation): does adding a realistic
depolarizing noise model measurably reduce success probability relative to
the ideal (noiseless) simulator run of the same circuit?
"""

import json
import sys

from app.models.enums import Domain
from scripts._pipeline import RESEARCH_DIR, ensure_schema, get_session, run_full_pipeline

N_QUBITS = 3
MARKED_STATE = "101"
SHOTS = 2048
NUM_RUNS = 15


def _experiment_7(db) -> dict:
    outcome = run_full_pipeline(
        db,
        domain=Domain.QUANTUM,
        project_title="Experiment 7: Grover search vs. classical random guessing",
        question_text="Does Grover's algorithm find a marked item with higher probability "
        "per shot than classical uniform-random guessing over the same search space?",
        null_hypothesis="Grover's algorithm's success probability does not exceed classical "
        "uniform-random guessing over the same 2^n search space.",
        alternative_hypothesis="Grover's algorithm's success probability exceeds classical "
        "uniform-random guessing over the same 2^n search space.",
        baseline="classical_random_guess",
        evaluation_metric="success_probability",
        decision_rule={
            "metric": "success_probability",
            "alpha": 0.05,
            "min_effect_size": 0.5,
            "direction": "greater",
        },
        codegen_spec={
            "algorithm": "grover",
            "n_qubits": N_QUBITS,
            "marked_state": MARKED_STATE,
            "shots": SHOTS,
            "num_runs": NUM_RUNS,
            "base_seed": 42,
            "comparison": "vs_classical_random",
            "baseline": "classical_random_guess",
            "proposed": "grover_quantum",
        },
        num_runs=NUM_RUNS,
        metrics_requested=["success_probability"],
    )
    return {
        "experiment": "Experiment 7: Grover vs classical random guessing",
        "n_qubits": N_QUBITS,
        "marked_state": MARKED_STATE,
        "shots": SHOTS,
        "conclusion_status": outcome.conclusion_status,
        "conclusion_rationale": outcome.conclusion_rationale,
        "statistics": outcome.statistics,
        "limitations": outcome.limitations,
    }


def _experiment_8(db) -> dict:
    outcome = run_full_pipeline(
        db,
        domain=Domain.QUANTUM,
        project_title="Experiment 8: quantum noise ablation (ideal vs. noisy Grover)",
        question_text="Does a realistic depolarizing noise model measurably reduce Grover's "
        "success probability relative to the ideal (noiseless) simulator run?",
        null_hypothesis="A depolarizing noise model does not reduce Grover's success "
        "probability relative to the ideal run.",
        alternative_hypothesis="A depolarizing noise model reduces Grover's success "
        "probability relative to the ideal run.",
        baseline="ideal",
        evaluation_metric="success_probability",
        decision_rule={
            "metric": "success_probability",
            "alpha": 0.05,
            "min_effect_size": 0.05,
            "direction": "less",
        },
        codegen_spec={
            "algorithm": "grover",
            "n_qubits": N_QUBITS,
            "marked_state": MARKED_STATE,
            "shots": SHOTS,
            "num_runs": NUM_RUNS,
            "base_seed": 42,
            "comparison": "noise_ablation",
            "noise_error_rate": 0.05,
            "baseline": "ideal",
            "proposed": "noisy",
        },
        num_runs=NUM_RUNS,
        metrics_requested=["success_probability"],
    )
    return {
        "experiment": "Experiment 8: noise ablation (ideal vs noisy Grover)",
        "n_qubits": N_QUBITS,
        "marked_state": MARKED_STATE,
        "shots": SHOTS,
        "noise_error_rate": 0.05,
        "conclusion_status": outcome.conclusion_status,
        "conclusion_rationale": outcome.conclusion_rationale,
        "statistics": outcome.statistics,
        "limitations": outcome.limitations,
    }


def main() -> int:
    ensure_schema()
    db = get_session()
    try:
        exp7 = _experiment_7(db)
        exp8 = _experiment_8(db)
    finally:
        db.close()

    out_dir = RESEARCH_DIR / "quantum"
    out_dir.mkdir(parents=True, exist_ok=True)

    exp7_path = out_dir / "experiment_7_grover_vs_classical.json"
    exp7_path.write_text(json.dumps(exp7, indent=2), encoding="utf-8")
    print(json.dumps(exp7, indent=2))
    print(f"\nwrote {exp7_path}")

    exp8_path = out_dir / "experiment_8_noise_ablation.json"
    exp8_path.write_text(json.dumps(exp8, indent=2), encoding="utf-8")
    print(json.dumps(exp8, indent=2))
    print(f"\nwrote {exp8_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
