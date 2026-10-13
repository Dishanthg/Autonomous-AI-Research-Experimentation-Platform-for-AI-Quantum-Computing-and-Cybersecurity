from app.models.hypothesis import Hypothesis
from app.services.hypothesis.quality_check import QUALITY_THRESHOLD, run_quality_check


def _make_hypothesis(**overrides) -> Hypothesis:
    defaults = dict(
        project_id="p1",
        null_hypothesis="Graph features do not improve detection.",
        alternative_hypothesis="Graph features improve detection.",
        independent_variables=["graph_representation"],
        dependent_variables=["f1", "pr_auc"],
        dataset_id="d1",
        baseline="rule_based",
        evaluation_metric="f1",
        potential_confounders=["class_imbalance"],
        decision_rule={"metric": "f1", "alpha": 0.05, "min_effect_size": 0.2, "direction": "greater"},
        generated_by="human",
    )
    defaults.update(overrides)
    return Hypothesis(**defaults)


def test_well_formed_hypothesis_passes_quality_check():
    hyp = _make_hypothesis()
    result = run_quality_check(hyp)
    assert result.passed
    assert result.score >= QUALITY_THRESHOLD


def test_hypothesis_missing_dataset_fails_quality_check():
    hyp = _make_hypothesis(dataset_id=None)
    result = run_quality_check(hyp)
    assert result.checks["dataset_availability"] is False


def test_hypothesis_missing_decision_rule_fields_fails_falsifiability():
    hyp = _make_hypothesis(decision_rule={"metric": "f1"})  # no alpha/min_effect_size
    result = run_quality_check(hyp)
    assert result.checks["falsifiability"] is False


def test_vague_hypothesis_scores_low():
    hyp = _make_hypothesis(
        dataset_id=None,
        baseline=None,
        potential_confounders=None,
        decision_rule={"metric": "f1"},
    )
    result = run_quality_check(hyp)
    assert not result.passed
