"""Experiment 2 / Section 62/35: Memory Ablation.

Measures the platform's own claimed benefit of Research Memory - duplicate-
experiment detection - by calling the EXACT SAME query function
(`services.memory.queries.find_duplicate_experiment`) with `enabled=True`
vs `enabled=False` against a real, populated project where a duplicate
config genuinely exists. This is the actual mechanism the platform ships,
not a simulation of it, so the measured difference is real (n=1 project,
one duplicate-configuration scenario - a first data point toward H2/H6, not
a general claim).
"""

import json
import sys

from app.models.enums import Domain, ExperimentStatus
from app.models.experiment import Experiment, ExperimentConfig
from app.models.hypothesis import Hypothesis
from app.models.project import Project
from app.services.memory.queries import find_duplicate_experiment
from scripts._pipeline import RESEARCH_DIR, ensure_demo_user, ensure_schema, get_session


def main() -> int:
    ensure_schema()
    db = get_session()
    try:
        user = ensure_demo_user(db)
        project = Project(title="Memory Ablation Test Project", domain=Domain.AI, owner_id=user.id)
        db.add(project)
        db.flush()

        hyp = Hypothesis(
            project_id=project.id,
            null_hypothesis="H0",
            alternative_hypothesis="H1",
            independent_variables=["method"],
            dependent_variables=["f1"],
            baseline="logistic_regression",
            evaluation_metric="f1",
            decision_rule={"metric": "f1", "alpha": 0.05, "min_effect_size": 0.2, "direction": "greater"},
            generated_by="human:ablation_script",
        )
        db.add(hyp)
        db.flush()

        # First experiment: random_forest vs logistic_regression on synthetic data.
        exp1 = Experiment(
            project_id=project.id,
            hypothesis_id=hyp.id,
            domain=Domain.AI,
            objective="RF vs LogReg",
            status=ExperimentStatus.PLANNED,
        )
        db.add(exp1)
        db.flush()
        cfg1 = ExperimentConfig(
            experiment_id=exp1.id,
            version=1,
            baseline_spec="logistic_regression",
            model_spec="random_forest",
            num_runs=10,
            metrics_requested=["f1"],
            resource_limits={"cpu": 1},
            random_seed=42,
        )
        db.add(cfg1)
        db.flush()

        # Second experiment: the SAME baseline/proposed/domain combination -
        # a researcher (or an AI planner without memory) proposing this again
        # without realizing it was already run.
        exp2 = Experiment(
            project_id=project.id,
            hypothesis_id=hyp.id,
            domain=Domain.AI,
            objective="RF vs LogReg (proposed again, unaware of exp1)",
            status=ExperimentStatus.DRAFT,
        )
        db.add(exp2)
        db.flush()
        db.commit()

        without_memory = find_duplicate_experiment(
            db, project.id, "AI", "logistic_regression", "random_forest", None, enabled=False
        )
        with_memory = find_duplicate_experiment(
            db, project.id, "AI", "logistic_regression", "random_forest", None, enabled=True
        )

        report = {
            "ablation": "memory_duplicate_detection",
            "scenario": "A second experiment proposes the exact same (domain, baseline, proposed) "
            "combination as an experiment that already exists in the project.",
            "without_memory": {
                "enabled": False,
                "duplicate_detected": without_memory is not None,
                "result": without_memory,
            },
            "with_memory": {
                "enabled": True,
                "duplicate_detected": with_memory is not None,
                "result": with_memory,
            },
            "finding": (
                "With memory enabled, the platform correctly identifies exp2 as a duplicate of "
                "exp1 (same domain/baseline/proposed) BEFORE it would be executed, pointing the "
                "researcher/agent back to the existing result. With memory disabled, no such "
                "warning is possible - the duplicate would proceed to execution undetected."
                if (with_memory is not None and without_memory is None)
                else "UNEXPECTED: see raw values above - the expected with/without contrast did not hold."
            ),
            "caveat": "n=1 project, one duplicate scenario. This demonstrates the mechanism works "
            "as designed; it is not a statistical claim about duplicate-experiment rates "
            "across many researchers/projects (that would require Section 35's full "
            "human-subjects-style ablation, not run here).",
        }
        print(json.dumps(report, indent=2, default=str))

        out = RESEARCH_DIR / "ablations" / "memory_ablation.json"
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(json.dumps(report, indent=2, default=str), encoding="utf-8")
        print(f"\nwrote {out}")
        return 0
    finally:
        db.close()


if __name__ == "__main__":
    sys.exit(main())
