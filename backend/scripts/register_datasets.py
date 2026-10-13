"""Register every dataset this
platform's codegen templates know how to use as a real `Dataset` +
`DatasetVersion` row, even ones not yet exercised by a concrete experiment
run. `run_research_pipeline.py` and `run_cyber_experiment.py` also
self-register the dataset they actually use (breast_cancer,
synthetic_traffic_v1 respectively) - this script additionally covers
`synthetic_classification` and `digits`, which are supported by
`app/services/codegen/ai_templates.py` but not yet used by a named
experiment script, so the registry is complete and idempotent no matter
which script ran first.
"""

import hashlib
import sys

import numpy as np
from sklearn.datasets import load_digits, make_classification

from scripts._pipeline import ensure_dataset_registered, ensure_schema, get_session


def _register_synthetic_classification(db) -> None:
    seed = 42
    n_samples, n_features = 2000, 20
    X, y = make_classification(
        n_samples=n_samples, n_features=n_features, random_state=seed, n_informative=int(n_features * 0.6)
    )
    checksum = hashlib.sha256(np.concatenate([X.ravel(), y.astype(float)]).tobytes()).hexdigest()
    ensure_dataset_registered(
        db,
        name="synthetic_classification",
        source="sklearn.datasets.make_classification, fixed seed",
        license="N/A (generated)",
        description="Generic synthetic binary classification dataset used as the default AI "
        "codegen template dataset when no real dataset is specified.",
        version_tag=f"seed-{seed}-n{n_samples}-f{n_features}",
        checksum=checksum,
        preprocessing=f"sklearn.datasets.make_classification(n_samples={n_samples}, "
        f"n_features={n_features}, random_state={seed}, n_informative={int(n_features * 0.6)})",
        row_count=n_samples,
    )


def _register_digits(db) -> None:
    data = load_digits()
    checksum = hashlib.sha256(data.data.tobytes()).hexdigest()
    ensure_dataset_registered(
        db,
        name="digits",
        source="sklearn.datasets.load_digits",
        license="public domain",
        description="UCI ML hand-written digits dataset, bundled with scikit-learn.",
        citation="E. Alpaydin, C. Kaynak. Optical Recognition of Handwritten Digits. UCI ML Repository.",
        version_tag="sklearn-bundled-v1",
        checksum=checksum,
        preprocessing="None - raw bundled feature matrix.",
        row_count=int(data.data.shape[0]),
    )


def main() -> int:
    ensure_schema()
    db = get_session()
    try:
        _register_synthetic_classification(db)
        _register_digits(db)
        db.commit()
    finally:
        db.close()
    print("Registered datasets: synthetic_classification, digits "
          "(breast_cancer / synthetic_traffic_v1 self-register from their own experiment scripts).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
