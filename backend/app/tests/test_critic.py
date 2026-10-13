from app.models.experiment import ExperimentConfig
from app.models.hypothesis import Hypothesis
from app.services.critic.checklist import critique_experiment_config, critique_hypothesis


def test_critic_flags_missing_dataset_as_blocking():
    hyp = Hypothesis(
        project_id="p1",
        null_hypothesis="H0",
        alternative_hypothesis="H1",
        independent_variables=["x"],
        dependent_variables=["y"],
        dataset_id=None,
        baseline="rf",
        evaluation_metric="f1",
        potential_confounders=["c1"],
        decision_rule={"metric": "f1", "alpha": 0.05, "min_effect_size": 0.2, "direction": "greater"},
        generated_by="human",
    )
    report = critique_hypothesis(hyp)
    assert report.has_blocking
    assert any(o.category == "dataset_quality" for o in report.objections)


def test_critic_flags_zero_min_effect_size_as_blocking():
    hyp = Hypothesis(
        project_id="p1",
        null_hypothesis="H0",
        alternative_hypothesis="H1",
        independent_variables=["x"],
        dependent_variables=["y"],
        dataset_id="d1",
        baseline="rf",
        evaluation_metric="f1",
        potential_confounders=["c1"],
        decision_rule={"metric": "f1", "alpha": 0.05, "min_effect_size": 0.0, "direction": "greater"},
        generated_by="human",
    )
    report = critique_hypothesis(hyp)
    assert report.has_blocking
    assert any(o.category == "statistical_methodology" for o in report.objections)


def test_critic_passes_well_formed_hypothesis():
    hyp = Hypothesis(
        project_id="p1",
        null_hypothesis="H0",
        alternative_hypothesis="H1",
        independent_variables=["x"],
        dependent_variables=["y"],
        dataset_id="d1",
        baseline="rf",
        evaluation_metric="f1",
        potential_confounders=["c1"],
        decision_rule={"metric": "f1", "alpha": 0.05, "min_effect_size": 0.2, "direction": "greater"},
        generated_by="human",
    )
    report = critique_hypothesis(hyp)
    assert not report.has_blocking


def test_critic_flags_small_sample_size():
    config = ExperimentConfig(
        experiment_id="e1",
        version=1,
        num_runs=1,
        metrics_requested=["f1"],
        resource_limits={"cpu": 1},
        random_seed=42,
    )
    report = critique_experiment_config(config)
    assert any(o.category == "sample_size" for o in report.objections)


def test_critic_flags_missing_metrics_as_blocking():
    config = ExperimentConfig(
        experiment_id="e1",
        version=1,
        num_runs=5,
        metrics_requested=[],
        resource_limits={"cpu": 1},
        random_seed=42,
    )
    report = critique_experiment_config(config)
    assert report.has_blocking
