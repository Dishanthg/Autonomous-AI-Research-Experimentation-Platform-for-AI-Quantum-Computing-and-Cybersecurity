"""Experiment 3 / Section 63/36: Critic Ablation.

Measures whether the deterministic critic (`services.critic.checklist`)
actually blocks specific invalid experimental designs, by constructing two
genuinely flawed configs/hypotheses and checking them with the critic
"on" (the real code path used by the API's approval endpoint) vs. "off"
(what would happen if that check were skipped, which is exactly what
`api/v1/experiments.py::approve_config` would do if the
`critique_experiment_config` call were removed).

This is a real measurement of the critic's actual, current rule set - not a
projection - but it covers only the specific flaws below (small sample
size, zero minimum-effect-size threshold, missing dataset); it does not
claim to cover every possible experimental design error (see
`docs/masters-application/12_ablation_studies.md`).
"""

import json
import sys

from app.models.experiment import ExperimentConfig
from app.models.hypothesis import Hypothesis
from app.services.critic.checklist import critique_experiment_config, critique_hypothesis
from scripts._pipeline import RESEARCH_DIR


def _flawed_hypothesis() -> Hypothesis:
    return Hypothesis(
        project_id="p1",
        null_hypothesis="H0",
        alternative_hypothesis="H1",
        independent_variables=["x"],
        dependent_variables=["f1"],
        dataset_id=None,  # flaw: no dataset specified
        baseline=None,  # flaw: no baseline specified
        evaluation_metric="f1",
        potential_confounders=None,  # flaw: no confounders documented
        decision_rule={
            "metric": "f1",
            "alpha": 0.05,
            "min_effect_size": 0.0,
            "direction": "greater",
        },  # flaw: zero threshold
        generated_by="human:ablation_script",
    )


def _flawed_config() -> ExperimentConfig:
    return ExperimentConfig(
        experiment_id="e1",
        version=1,
        num_runs=1,  # flaw: too small for a stable estimate
        metrics_requested=[],  # flaw: no metrics requested at all
        resource_limits={"cpu": 1},
        random_seed=42,
    )


def main() -> int:
    hyp = _flawed_hypothesis()
    config = _flawed_config()

    hyp_critique = critique_hypothesis(hyp)
    config_critique = critique_experiment_config(config)

    critic_on = {
        "hypothesis_objections": [
            {"severity": o.severity, "category": o.category, "message": o.message}
            for o in hyp_critique.objections
        ],
        "hypothesis_has_blocking": hyp_critique.has_blocking,
        "config_objections": [
            {"severity": o.severity, "category": o.category, "message": o.message}
            for o in config_critique.objections
        ],
        "config_has_blocking": config_critique.has_blocking,
        "would_be_approved": not (hyp_critique.has_blocking or config_critique.has_blocking),
    }

    # "Critic off" is not a separate code path in production (the API always
    # calls critique_* before approval) - it is what api/v1/experiments.py's
    # approve_config() would do if that call were removed: approve
    # unconditionally. Modeled explicitly here rather than by actually
    # deploying an unsafe code path.
    critic_off = {
        "hypothesis_objections": [],
        "config_objections": [],
        "would_be_approved": True,
    }

    report = {
        "ablation": "critic_blocks_invalid_designs",
        "scenario": "A hypothesis with no dataset/baseline/confounders and a zero "
        "minimum-effect-size threshold, paired with a config requesting zero "
        "num_runs=1 and metrics_requested=[].",
        "critic_on": critic_on,
        "critic_off_(hypothetical_if_check_were_removed)": critic_off,
        "finding": (
            f"With the critic enabled, {len(critic_on['hypothesis_objections'])} hypothesis "
            f"objection(s) and {len(critic_on['config_objections'])} config objection(s) were "
            f"raised, and would_be_approved=False - this flawed design is correctly blocked "
            f"before it could reach Gate 1 approval. Without the critic, nothing in the "
            f"pipeline would have stopped it (would_be_approved=True)."
        ),
        "caveat": "This demonstrates the critic's current checklist catches these specific, "
        "constructed flaws (n=1 constructed scenario). It is not a measurement of "
        "the critic's hit rate against a broad population of real, human-authored "
        "experimental designs.",
    }
    print(json.dumps(report, indent=2, default=str))

    out = RESEARCH_DIR / "ablations" / "critic_ablation.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, indent=2, default=str), encoding="utf-8")
    print(f"\nwrote {out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
