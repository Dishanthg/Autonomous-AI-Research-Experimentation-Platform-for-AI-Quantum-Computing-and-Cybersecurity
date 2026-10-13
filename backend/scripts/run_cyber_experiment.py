"""`make cybersecurity` - Experiment 6 (Section 66): rule-based vs ML vs
graph-enhanced intrusion detection. Runs two pairwise hypotheses through
the real pipeline (ML vs rule-based, graph-enhanced vs rule-based) on the
synthetic-traffic codegen template (honestly labeled synthetic - see
`app/services/codegen/cyber_templates.py`).
"""

import hashlib
import json
import sys

import numpy as np

from app.models.enums import Domain
from scripts._pipeline import RESEARCH_DIR, ensure_dataset_registered, ensure_schema, get_session, run_full_pipeline

BASE_SEED = 7
N_SAMPLES = 4000
N_FEATURES = 12


def _make_synthetic_traffic_checksum(seed: int, n_samples: int, n_features: int) -> str:
    """Replicates the exact generator in
    app/services/codegen/cyber_templates.py::make_synthetic_traffic so the
    registered DatasetVersion checksum genuinely matches this fixed-seed
    synthetic output, not an approximation of it."""
    rng = np.random.default_rng(seed)
    n_attack = int(n_samples * 0.12)
    n_benign = n_samples - n_attack
    benign = rng.normal(loc=0.0, scale=1.0, size=(n_benign, n_features))
    attack = rng.normal(loc=1.8, scale=1.2, size=(n_attack, n_features))
    X = np.vstack([benign, attack])
    return hashlib.sha256(X.tobytes()).hexdigest()


def _register_synthetic_traffic(db) -> tuple[str, str]:
    checksum = _make_synthetic_traffic_checksum(BASE_SEED, N_SAMPLES, N_FEATURES)
    return ensure_dataset_registered(
        db,
        name="synthetic_traffic_v1",
        source="app/services/codegen/cyber_templates.py::make_synthetic_traffic (in-sandbox generator)",
        license="N/A (generated)",
        description="Synthetic network-flow-like features (packet_rate, byte_rate, unique_ports, "
        "syn_ratio, ...) with a shifted-mean minority attack class - an explicitly synthetic "
        "stand-in for a real IDS dataset (e.g. CIC-IDS2017/NSL-KDD), not a claim about real "
        "network traffic distributions.",
        limitations="Synthetic; does not capture real network traffic correlations, feature drift, "
        "or adversarial evasion behavior.",
        version_tag=f"seed-{BASE_SEED}-n{N_SAMPLES}-f{N_FEATURES}",
        checksum=checksum,
        preprocessing=f"numpy.random.default_rng(seed={BASE_SEED}) normal-distribution generation, "
        f"12% attack ratio, n_samples={N_SAMPLES}, n_features={N_FEATURES}.",
        row_count=N_SAMPLES,
    )


def _run(db, proposed: str, dataset_id: str, dataset_version_id: str) -> dict:
    outcome = run_full_pipeline(
        db,
        domain=Domain.CYBERSECURITY,
        project_title=f"Experiment 6: {proposed} vs rule_based intrusion detection",
        question_text=f"Does {proposed} outperform a rule-based baseline for intrusion detection?",
        null_hypothesis=f"{proposed} does not outperform the rule-based baseline (F1).",
        alternative_hypothesis=f"{proposed} outperforms the rule-based baseline (F1).",
        baseline="rule_based",
        evaluation_metric="f1",
        decision_rule={"metric": "f1", "alpha": 0.05, "min_effect_size": 0.2, "direction": "greater"},
        codegen_spec={
            "baseline": "rule_based",
            "proposed": proposed,
            "num_runs": 10,
            "base_seed": BASE_SEED,
        },
        num_runs=10,
        metrics_requested=["precision", "recall", "f1", "pr_auc", "false_positive_rate", "latency_ms"],
        dataset_id=dataset_id,
        dataset_version_id=dataset_version_id,
    )
    return {
        "proposed": proposed,
        "baseline": "rule_based",
        "conclusion_status": outcome.conclusion_status,
        "conclusion_rationale": outcome.conclusion_rationale,
        "statistics": outcome.statistics,
        "limitations": outcome.limitations,
    }


def main() -> int:
    ensure_schema()
    db = get_session()
    try:
        dataset_id, dataset_version_id = _register_synthetic_traffic(db)
        db.commit()
        results = [
            _run(db, "logistic_regression", dataset_id, dataset_version_id),
            _run(db, "graph_enhanced_rf", dataset_id, dataset_version_id),
        ]
    finally:
        db.close()

    print(json.dumps(results, indent=2))
    out_path = RESEARCH_DIR / "cybersecurity" / "experiment_6_ids_comparison.json"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(results, indent=2), encoding="utf-8")
    print(f"\nwrote {out_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
