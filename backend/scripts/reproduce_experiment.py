"""`make reproduce` - Section 54's "REPRODUCE EXPERIMENT" button, as a CLI.

Given an experiment_id, re-executes its most recent approved config (same
seed, same codegen_spec - pulled from the stored config, not retyped) in a
fresh sandbox run, then diffs the new metrics against the originally stored
Result. Reports MATCH / DEVIATION per metric rather than assuming
reproduction succeeded.

Usage: python -m scripts.reproduce_experiment <experiment_id>
"""

import json
import sys

from app.models.experiment import Experiment, ExperimentConfig
from app.models.hypothesis import Hypothesis
from app.models.result import Metric, Result
from app.services.execution.analysis import analyze_experiment
from app.services.execution.orchestrator import execute_experiment_config
from scripts._pipeline import REPO_ROOT, ensure_schema, get_session


def main() -> int:
    if len(sys.argv) != 2:
        print("Usage: python -m scripts.reproduce_experiment <experiment_id>", file=sys.stderr)
        return 1
    experiment_id = sys.argv[1]

    ensure_schema()
    db = get_session()
    try:
        experiment = db.get(Experiment, experiment_id)
        if not experiment:
            print(f"error: experiment {experiment_id} not found", file=sys.stderr)
            return 1

        config = (
            db.query(ExperimentConfig)
            .filter(ExperimentConfig.experiment_id == experiment_id, ExperimentConfig.approved.is_(True))
            .order_by(ExperimentConfig.version.desc())
            .first()
        )
        if not config:
            print(f"error: no approved config found for experiment {experiment_id}", file=sys.stderr)
            return 1

        original_result = (
            db.query(Result)
            .filter(Result.experiment_id == experiment_id)
            .order_by(Result.created_at.asc())
            .first()
        )
        original_metrics = {}
        if original_result:
            for m in db.query(Metric).filter(Metric.result_id == original_result.id).all():
                original_metrics[m.name] = m.value

        hypothesis = db.get(Hypothesis, experiment.hypothesis_id)
        codegen_spec = (config.software_environment or {}).get("codegen_spec", {})

        print(
            f"Reproducing experiment {experiment_id} (config v{config.version}, seed={config.random_seed})..."
        )
        run, metrics_json = execute_experiment_config(db, config, experiment.domain.value, codegen_spec)
        print(f"  run status: {run.status.value}  isolation: {run.isolation_level}")

        report = {"experiment_id": experiment_id, "config_version": config.version, "metric_comparison": []}

        if metrics_json is not None:
            new_result, _ = analyze_experiment(
                db,
                experiment_id=experiment_id,
                hypothesis=hypothesis,
                run_id=run.id,
                metrics_json=metrics_json,
                config=config,
                isolation_level=run.isolation_level,
            )
            new_metrics = {
                m.name: m.value for m in db.query(Metric).filter(Metric.result_id == new_result.id).all()
            }

            for name, new_value in new_metrics.items():
                old_value = original_metrics.get(name)
                if old_value is None:
                    status = "NO_BASELINE"
                    delta = None
                else:
                    delta = new_value - old_value
                    # Same random seed + same deterministic codegen template should
                    # reproduce closely; allow small floating-point/model-nondeterminism
                    # tolerance rather than requiring bit-exact equality.
                    status = (
                        "MATCH"
                        if abs(delta) < 1e-6 or abs(delta) / (abs(old_value) + 1e-9) < 0.05
                        else "DEVIATION"
                    )
                report["metric_comparison"].append(
                    {
                        "metric": name,
                        "original": old_value,
                        "reproduced": new_value,
                        "delta": delta,
                        "status": status,
                    }
                )
                print(f"  {name}: original={old_value} reproduced={new_value} -> {status}")

            report["original_conclusion"] = (
                original_result.conclusion_status.value
                if original_result and original_result.conclusion_status
                else None
            )
            report["reproduced_conclusion"] = (
                new_result.conclusion_status.value if new_result.conclusion_status else None
            )
            report["conclusion_status_matches"] = (
                report["original_conclusion"] == report["reproduced_conclusion"]
            )
            print(
                f"  conclusion: original={report['original_conclusion']} reproduced={report['reproduced_conclusion']} "
                f"match={report['conclusion_status_matches']}"
            )
        else:
            report["error"] = f"Reproduction run did not complete: {run.stderr}"
            print(f"  {report['error']}", file=sys.stderr)

        db.commit()
        print("\n" + json.dumps(report, indent=2, default=str))

        package_dir = REPO_ROOT / "reproducibility" / f"experiment-{experiment_id[:8]}"
        package_dir.mkdir(parents=True, exist_ok=True)
        (package_dir / "reproduction_report.json").write_text(
            json.dumps(report, indent=2, default=str), encoding="utf-8"
        )
        (package_dir / "config_snapshot.json").write_text(
            json.dumps(
                {
                    "experiment_id": experiment_id,
                    "config_version": config.version,
                    "random_seed": config.random_seed,
                    "num_runs": config.num_runs,
                    "metrics_requested": config.metrics_requested,
                    "resource_limits": config.resource_limits,
                    "codegen_spec": codegen_spec,
                },
                indent=2,
                default=str,
            ),
            encoding="utf-8",
        )
        (package_dir / "README.md").write_text(
            f"# Reproducibility Package: experiment {experiment_id}\n\n"
            f"Reproduce with:\n\n"
            f"```\ncd backend\npython -m scripts.reproduce_experiment {experiment_id}\n```\n\n"
            f"See `config_snapshot.json` for the exact pinned config (seed, codegen spec, "
            f"resource limits) and `reproduction_report.json` for the per-metric "
            f"MATCH/DEVIATION comparison against the originally stored result "
            f"(Section 54).\n",
            encoding="utf-8",
        )
        print(f"\nwrote reproducibility package to {package_dir}")
        return 0
    finally:
        db.close()


if __name__ == "__main__":
    sys.exit(main())
