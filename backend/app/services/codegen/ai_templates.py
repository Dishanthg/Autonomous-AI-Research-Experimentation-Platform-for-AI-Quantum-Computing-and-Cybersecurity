"""Deterministic code generation for AI-domain model-comparison experiments
(Section 18/23/P). This is template-based, not LLM-freeform generation:
the LLM (when used at the Experiment Designer stage) selects a baseline
name, a proposed-method name, and hyperparameters from a fixed, reviewed
vocabulary - it never writes arbitrary Python that lands directly in the
sandbox unreviewed (Section 30's critic + Gate 1 review this config first).
"""

import textwrap

SUPPORTED_BASELINES = {"logistic_regression", "random_forest"}
SUPPORTED_PROPOSED = {"random_forest", "xgboost", "mlp"}
SUPPORTED_DATASETS = {"synthetic_classification", "breast_cancer", "digits"}


def render_model_comparison_script(
    dataset: str,
    baseline: str,
    proposed: str,
    num_runs: int,
    base_seed: int,
    n_samples: int = 2000,
    n_features: int = 20,
) -> str:
    if dataset not in SUPPORTED_DATASETS:
        raise ValueError(f"Unsupported dataset '{dataset}'; allowed: {SUPPORTED_DATASETS}")
    if baseline not in SUPPORTED_BASELINES:
        raise ValueError(f"Unsupported baseline '{baseline}'; allowed: {SUPPORTED_BASELINES}")
    if proposed not in SUPPORTED_PROPOSED:
        raise ValueError(f"Unsupported proposed method '{proposed}'; allowed: {SUPPORTED_PROPOSED}")

    return (
        textwrap.dedent(
            f"""
        import json, os, time
        import numpy as np
        from sklearn.model_selection import train_test_split
        from sklearn.metrics import f1_score, average_precision_score
        from sklearn.linear_model import LogisticRegression
        from sklearn.ensemble import RandomForestClassifier
        from sklearn.neural_network import MLPClassifier
        from sklearn.datasets import make_classification, load_breast_cancer, load_digits

        DATASET = {dataset!r}
        BASELINE = {baseline!r}
        PROPOSED = {proposed!r}
        NUM_RUNS = {num_runs}
        BASE_SEED = {base_seed}
        N_SAMPLES = {n_samples}
        N_FEATURES = {n_features}

        def load_dataset(seed):
            if DATASET == "synthetic_classification":
                X, y = make_classification(
                    n_samples=N_SAMPLES, n_features=N_FEATURES, n_informative=int(N_FEATURES*0.6),
                    n_redundant=int(N_FEATURES*0.2), weights=[0.85, 0.15], flip_y=0.02, random_state=seed,
                )
            elif DATASET == "breast_cancer":
                data = load_breast_cancer()
                X, y = data.data, data.target
            elif DATASET == "digits":
                data = load_digits()
                X, y = data.data, (data.target == 0).astype(int)
            return train_test_split(X, y, test_size=0.3, random_state=seed, stratify=y)

        def build_model(name, seed):
            if name == "logistic_regression":
                return LogisticRegression(max_iter=2000, random_state=seed)
            if name == "random_forest":
                return RandomForestClassifier(n_estimators=200, random_state=seed)
            if name == "mlp":
                return MLPClassifier(hidden_layer_sizes=(64, 32), max_iter=500, random_state=seed)
            if name == "xgboost":
                import xgboost as xgb
                return xgb.XGBClassifier(n_estimators=200, use_label_encoder=False,
                                          eval_metric="logloss", random_state=seed)
            raise ValueError(name)

        def run_once(name, seed):
            X_train, X_test, y_train, y_test = load_dataset(seed)
            model = build_model(name, seed)
            t0 = time.perf_counter()
            model.fit(X_train, y_train)
            train_time_ms = (time.perf_counter() - t0) * 1000

            t0 = time.perf_counter()
            if hasattr(model, "predict_proba"):
                y_score = model.predict_proba(X_test)[:, 1]
            else:
                y_score = model.decision_function(X_test)
            latency_ms = (time.perf_counter() - t0) * 1000 / max(1, len(X_test))
            y_pred = (y_score >= 0.5).astype(int)

            return {{
                "f1": float(f1_score(y_test, y_pred)),
                "pr_auc": float(average_precision_score(y_test, y_score)),
                "latency_ms": float(latency_ms),
                "train_time_ms": float(train_time_ms),
            }}

        results = {{"baseline": {{"f1": [], "pr_auc": [], "latency_ms": [], "train_time_ms": []}},
                    "proposed": {{"f1": [], "pr_auc": [], "latency_ms": [], "train_time_ms": []}}}}

        for i in range(NUM_RUNS):
            seed = BASE_SEED + i
            for arm, name in (("baseline", BASELINE), ("proposed", PROPOSED)):
                r = run_once(name, seed)
                for k, v in r.items():
                    results[arm][k].append(v)

        os.makedirs("output", exist_ok=True)
        with open("output/metrics.json", "w") as f:
            json.dump({{
                "results": results,
                "meta": {{"dataset": DATASET, "baseline": BASELINE, "proposed": PROPOSED,
                          "num_runs": NUM_RUNS, "base_seed": BASE_SEED}},
            }}, f, indent=2)

        print("EXPERIMENT_COMPLETE")
    """
        ).strip()
        + "\n"
    )
