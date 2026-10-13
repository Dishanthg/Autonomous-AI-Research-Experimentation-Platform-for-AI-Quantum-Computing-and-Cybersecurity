"""Result Analyzer + Statistical Analyst + Conclusion Engine wiring
(Section 39/40). Deterministic only. This is the ONLY code path allowed to
write Result/Metric/StatisticalTest rows - no LLM call appears anywhere in
this module (Section 32 invariant). Also wires in the deterministic
Limitation Detector (Section 41) and returns Next-Experiment candidates
(Section 42) for the caller to surface to the researcher.
"""

from typing import Optional

from sqlalchemy.orm import Session

from app.models.experiment import ExperimentConfig
from app.models.hypothesis import Hypothesis
from app.models.result import Limitation, Metric, Result, StatisticalTest
from app.services.limitations.detector import detect_limitations
from app.services.next_experiment.generator import NextExperimentCandidate, propose_next_experiments
from app.services.statistics.conclusion import DecisionRule, evaluate_hypothesis
from app.services.statistics.engine import compare_two_groups, describe


def analyze_experiment(
    db: Session,
    experiment_id: str,
    hypothesis: Hypothesis,
    run_id: str,
    metrics_json: dict,
    config: Optional[ExperimentConfig] = None,
    isolation_level: Optional[str] = None,
) -> tuple[Result, list[NextExperimentCandidate]]:
    """metrics_json shape: {"results": {"baseline": {metric: [values...]},
    "proposed": {metric: [values...]}}, "meta": {...}}"""
    rule = DecisionRule(**hypothesis.decision_rule)
    baseline_values = metrics_json["results"]["baseline"][rule.metric]
    proposed_values = metrics_json["results"]["proposed"][rule.metric]

    comparison = compare_two_groups(proposed_values, baseline_values)
    status, rationale = evaluate_hypothesis(rule, comparison)

    result = Result(
        experiment_id=experiment_id,
        hypothesis_id=hypothesis.id,
        computed_by="deterministic:result_analyzer+statistical_analyst",
        conclusion_status=status,
        conclusion_rationale=rationale,
        human_approved=False,
    )
    db.add(result)
    db.flush()

    for arm, values in metrics_json["results"].items():
        for metric_name, vals in values.items():
            desc = describe(vals)
            db.add(
                Metric(result_id=result.id, run_id=run_id, name=f"{arm}.{metric_name}.mean", value=desc.mean)
            )
            db.add(
                Metric(result_id=result.id, run_id=run_id, name=f"{arm}.{metric_name}.std", value=desc.std)
            )

    db.add(
        StatisticalTest(
            result_id=result.id,
            metric_name=rule.metric,
            test_name=comparison.test_name,
            statistic=comparison.statistic,
            p_value=comparison.p_value,
            effect_size=comparison.effect_size,
            effect_size_type=comparison.effect_size_type,
            ci_lower=comparison.ci_lower,
            ci_upper=comparison.ci_upper,
            ci_level=comparison.ci_level,
        )
    )

    next_candidates: list[NextExperimentCandidate] = []
    if config is not None:
        codegen_spec = (config.software_environment or {}).get("codegen_spec", {})
        for finding in detect_limitations(config, codegen_spec, isolation_level=isolation_level):
            db.add(
                Limitation(
                    experiment_id=experiment_id,
                    category=finding.category,
                    description=finding.description,
                    detected_by="deterministic:limitation_detector",
                )
            )
        next_candidates = propose_next_experiments(config, status)

    db.flush()
    return result, next_candidates
