"""`make research` - Experiment 5 (Section 65): AI-domain model comparison.

Runs two pairwise hypotheses through the real pipeline: Random Forest vs.
Logistic Regression, and (if the xgboost package is available in the
sandbox image) XGBoost vs. Logistic Regression - each a genuine
hypothesis/config/critic/approval/execution/analysis cycle, not a
simulated 3-arm ANOVA (the platform's statistical engine currently does
pairwise comparisons only - see ADR-006 - so this script does not claim
more than that).
"""

import hashlib
import json
import sys

from sklearn.datasets import load_breast_cancer

from app.models.enums import Domain
from scripts._pipeline import RESEARCH_DIR, ensure_dataset_registered, ensure_schema, get_session, run_full_pipeline

DATASET = "breast_cancer"  # a real, bundled sklearn dataset - not synthetic


def _register_breast_cancer(db) -> tuple[str, str]:
    """Priority 2: register a real Dataset/DatasetVersion row for
    breast_cancer, checksummed against the actual bundled array, so this
    experiment's config carries a real dataset_version_id instead of a bare
    string - clears the reproducibility_limitation finding for this run."""
    data = load_breast_cancer()
    checksum = hashlib.sha256(data.data.tobytes()).hexdigest()
    return ensure_dataset_registered(
        db,
        name=DATASET,
        source="sklearn.datasets.load_breast_cancer (UCI ML Repository, Wolberg et al.)",
        license="public domain / UCI",
        description="Wisconsin Diagnostic Breast Cancer dataset, bundled with scikit-learn.",
        features=list(data.feature_names),
        citation="Wolberg, W.H., Street, W.N., & Mangasarian, O.L. (1995). Breast Cancer Wisconsin "
        "(Diagnostic) Data Set. UCI Machine Learning Repository.",
        version_tag="sklearn-bundled-v1",
        checksum=checksum,
        preprocessing="None - raw bundled feature matrix, StandardScaler applied per-run inside the codegen template.",
        row_count=int(data.data.shape[0]),
    )


def _run(db, proposed: str, dataset_id: str, dataset_version_id: str) -> dict:
    outcome = run_full_pipeline(
        db,
        domain=Domain.AI,
        project_title=f"Experiment 5: {proposed} vs logistic_regression on {DATASET}",
        question_text=f"Does {proposed} outperform logistic regression on {DATASET}?",
        null_hypothesis=f"{proposed} does not outperform logistic regression (F1) on {DATASET}.",
        alternative_hypothesis=f"{proposed} outperforms logistic regression (F1) on {DATASET}.",
        baseline="logistic_regression",
        evaluation_metric="f1",
        decision_rule={"metric": "f1", "alpha": 0.05, "min_effect_size": 0.1, "direction": "greater"},
        codegen_spec={
            "dataset": DATASET,
            "baseline": "logistic_regression",
            "proposed": proposed,
            "num_runs": 10,
            "base_seed": 42,
        },
        num_runs=10,
        metrics_requested=["f1", "pr_auc", "latency_ms"],
        dataset_id=dataset_id,
        dataset_version_id=dataset_version_id,
    )
    return {
        "proposed": proposed,
        "baseline": "logistic_regression",
        "dataset": DATASET,
        "conclusion_status": outcome.conclusion_status,
        "conclusion_rationale": outcome.conclusion_rationale,
        "statistics": outcome.statistics,
        "limitations": outcome.limitations,
    }


def main() -> int:
    ensure_schema()
    db = get_session()
    try:
        dataset_id, dataset_version_id = _register_breast_cancer(db)
        db.commit()
        results = [_run(db, "random_forest", dataset_id, dataset_version_id)]
        try:
            import xgboost  # noqa: F401

            results.append(_run(db, "xgboost", dataset_id, dataset_version_id))
        except ImportError:
            print("xgboost not installed in this environment - skipping that arm (NOT_IMPLEMENTED here).")
    finally:
        db.close()

    print(json.dumps(results, indent=2))
    out_path = RESEARCH_DIR / "ai" / "experiment_5_model_comparison.json"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(results, indent=2), encoding="utf-8")
    print(f"\nwrote {out_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
