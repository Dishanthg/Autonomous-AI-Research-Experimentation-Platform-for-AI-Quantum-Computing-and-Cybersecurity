"""`make experiment` - generic single-experiment runner (Section N). Runs
one hypothesis through the real pipeline (quality-check -> critic -> Gate 1
-> Gate 2 -> analysis) for the AI or cybersecurity domain and prints/saves
the real result.

Usage:
  python -m scripts.run_experiment --domain AI --dataset breast_cancer \
      --baseline logistic_regression --proposed random_forest --metric f1 --runs 10

  python -m scripts.run_experiment --domain CYBERSECURITY \
      --baseline rule_based --proposed graph_enhanced_rf --metric f1 --runs 10
"""

import argparse
import json
import sys

from app.models.enums import Domain
from scripts._pipeline import RESEARCH_DIR, ensure_schema, get_session, run_full_pipeline


def main() -> int:
    parser = argparse.ArgumentParser(description="Run a single ResearchMind-Q experiment")
    parser.add_argument("--domain", choices=["AI", "CYBERSECURITY"], required=True)
    parser.add_argument("--dataset", default="synthetic_classification", help="AI domain only")
    parser.add_argument("--baseline", required=True)
    parser.add_argument("--proposed", required=True)
    parser.add_argument("--metric", default="f1")
    parser.add_argument("--alpha", type=float, default=0.05)
    parser.add_argument("--min-effect-size", type=float, default=0.2)
    parser.add_argument("--direction", default="greater", choices=["greater", "less", "any"])
    parser.add_argument("--runs", type=int, default=10)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--output", default=None, help="research/-relative path to write JSON result to")
    args = parser.parse_args()

    domain = Domain(args.domain)
    if domain == Domain.AI:
        codegen_spec = {
            "dataset": args.dataset,
            "baseline": args.baseline,
            "proposed": args.proposed,
            "num_runs": args.runs,
            "base_seed": args.seed,
        }
        metrics_requested = ["f1", "pr_auc", "latency_ms"]
    else:
        codegen_spec = {
            "baseline": args.baseline,
            "proposed": args.proposed,
            "num_runs": args.runs,
            "base_seed": args.seed,
        }
        metrics_requested = ["f1", "pr_auc", "false_positive_rate"]

    ensure_schema()
    db = get_session()
    try:
        outcome = run_full_pipeline(
            db,
            domain=domain,
            project_title=f"CLI experiment: {args.baseline} vs {args.proposed} ({domain.value})",
            question_text=f"Does {args.proposed} outperform {args.baseline} on {args.metric}?",
            null_hypothesis=f"{args.proposed} does not outperform {args.baseline} on {args.metric}.",
            alternative_hypothesis=f"{args.proposed} outperforms {args.baseline} on {args.metric}.",
            baseline=args.baseline,
            evaluation_metric=args.metric,
            decision_rule={
                "metric": args.metric,
                "alpha": args.alpha,
                "min_effect_size": args.min_effect_size,
                "direction": args.direction,
            },
            codegen_spec=codegen_spec,
            num_runs=args.runs,
            metrics_requested=metrics_requested,
        )
    finally:
        db.close()

    result = {
        "domain": domain.value,
        "baseline": args.baseline,
        "proposed": args.proposed,
        "conclusion_status": outcome.conclusion_status,
        "conclusion_rationale": outcome.conclusion_rationale,
        "statistics": outcome.statistics,
        "limitations": outcome.limitations,
        "next_experiments": outcome.next_experiments,
        "experiment_id": outcome.experiment_id,
    }
    print(json.dumps(result, indent=2))

    if args.output:
        out_path = RESEARCH_DIR / args.output
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(json.dumps(result, indent=2), encoding="utf-8")
        print(f"\nwrote {out_path}")

    return 0 if outcome.run_status == "COMPLETED" else 1


if __name__ == "__main__":
    sys.exit(main())
