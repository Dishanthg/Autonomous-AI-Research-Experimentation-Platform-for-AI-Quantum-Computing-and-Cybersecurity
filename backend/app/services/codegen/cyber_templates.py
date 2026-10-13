"""Deterministic code generation for cybersecurity-domain detection
experiments (Section 24/Q). Synthetic traffic-like feature data only -
generated inside the sandbox, no external dataset download, no network
egress required or permitted (Rule 7).
"""

import textwrap

SUPPORTED_DETECTORS = {"rule_based", "logistic_regression", "random_forest", "graph_enhanced_rf"}


def render_intrusion_detection_script(
    baseline: str,
    proposed: str,
    num_runs: int,
    base_seed: int,
    n_samples: int = 4000,
    n_features: int = 12,
) -> str:
    if baseline not in SUPPORTED_DETECTORS or proposed not in SUPPORTED_DETECTORS:
        raise ValueError(f"Unsupported detector; allowed: {SUPPORTED_DETECTORS}")

    return (
        textwrap.dedent(
            f"""
        import json, os, time
        import numpy as np
        from sklearn.model_selection import train_test_split
        from sklearn.metrics import f1_score, average_precision_score, precision_score, recall_score, confusion_matrix
        from sklearn.linear_model import LogisticRegression
        from sklearn.ensemble import RandomForestClassifier

        BASELINE = {baseline!r}
        PROPOSED = {proposed!r}
        NUM_RUNS = {num_runs}
        BASE_SEED = {base_seed}
        N_SAMPLES = {n_samples}
        N_FEATURES = {n_features}

        def make_synthetic_traffic(seed):
            \"\"\"Synthetic network-flow-like features: [packet_rate, byte_rate,
            unique_ports, syn_ratio, ...]. Attack traffic is a shifted-mean
            minority class - a simplified, honestly-synthetic stand-in for a
            real IDS dataset (e.g. CIC-IDS2017/NSL-KDD), not a claim about
            real network traffic distributions.\"\"\"
            rng = np.random.default_rng(seed)
            n_attack = int(N_SAMPLES * 0.12)
            n_benign = N_SAMPLES - n_attack
            benign = rng.normal(loc=0.0, scale=1.0, size=(n_benign, N_FEATURES))
            attack = rng.normal(loc=1.8, scale=1.2, size=(n_attack, N_FEATURES))
            # graph-proxy feature: a synthetic "fan-out score" correlated with
            # attack for the graph-enhanced arm only
            X = np.vstack([benign, attack])
            y = np.array([0] * n_benign + [1] * n_attack)
            fanout = np.where(y == 1, rng.normal(3.0, 1.0, size=len(y)), rng.normal(0.5, 0.5, size=len(y)))
            idx = rng.permutation(len(y))
            return X[idx], y[idx], fanout[idx]

        def rule_based_predict(X):
            # Simple static threshold rule on the first two "rate" features.
            score = X[:, 0] * 0.5 + X[:, 1] * 0.5
            return (score > 1.0).astype(int), score

        def run_once(name, seed):
            X, y, fanout = make_synthetic_traffic(seed)
            if name == "graph_enhanced_rf":
                X = np.hstack([X, fanout.reshape(-1, 1)])
            X_train, X_test, y_train, y_test = train_test_split(
                X, y, test_size=0.3, random_state=seed, stratify=y
            )

            t0 = time.perf_counter()
            if name == "rule_based":
                y_pred, y_score = rule_based_predict(X_test)
                train_time_ms = 0.0
            else:
                model = (LogisticRegression(max_iter=2000, random_state=seed)
                         if name == "logistic_regression"
                         else RandomForestClassifier(n_estimators=200, random_state=seed))
                model.fit(X_train, y_train)
                train_time_ms = (time.perf_counter() - t0) * 1000
                y_score = model.predict_proba(X_test)[:, 1]
                y_pred = (y_score >= 0.5).astype(int)

            t1 = time.perf_counter()
            latency_ms = (time.perf_counter() - t1) * 1000 / max(1, len(X_test)) + 1e-6

            tn, fp, fn, tp = confusion_matrix(y_test, y_pred, labels=[0, 1]).ravel()
            fpr = fp / (fp + tn) if (fp + tn) > 0 else 0.0

            return {{
                "precision": float(precision_score(y_test, y_pred, zero_division=0)),
                "recall": float(recall_score(y_test, y_pred, zero_division=0)),
                "f1": float(f1_score(y_test, y_pred, zero_division=0)),
                "pr_auc": float(average_precision_score(y_test, y_score)),
                "false_positive_rate": float(fpr),
                "latency_ms": float(latency_ms),
                "train_time_ms": float(train_time_ms),
            }}

        results = {{"baseline": {{k: [] for k in
                        ["precision","recall","f1","pr_auc","false_positive_rate","latency_ms","train_time_ms"]}},
                    "proposed": {{k: [] for k in
                        ["precision","recall","f1","pr_auc","false_positive_rate","latency_ms","train_time_ms"]}}}}

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
                "meta": {{"dataset": "synthetic_traffic_v1", "baseline": BASELINE, "proposed": PROPOSED,
                          "num_runs": NUM_RUNS, "base_seed": BASE_SEED}},
            }}, f, indent=2)

        print("EXPERIMENT_COMPLETE")
    """
        ).strip()
        + "\n"
    )
