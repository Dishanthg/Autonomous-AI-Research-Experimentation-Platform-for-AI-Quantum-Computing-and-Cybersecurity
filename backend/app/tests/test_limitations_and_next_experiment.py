from app.models.enums import ConclusionStatus
from app.models.experiment import ExperimentConfig
from app.services.limitations.detector import detect_limitations
from app.services.next_experiment.generator import propose_next_experiments


def _config(**overrides) -> ExperimentConfig:
    defaults = dict(
        experiment_id="e1",
        version=1,
        num_runs=5,
        metrics_requested=["f1"],
        resource_limits={"cpu": 1.0, "memory": "512m"},
        random_seed=42,
        dataset_version_id=None,
    )
    defaults.update(overrides)
    return ExperimentConfig(**defaults)


def test_detects_small_sample_limitation():
    findings = detect_limitations(_config(num_runs=5), {"dataset": "synthetic_classification"})
    categories = {f.category for f in findings}
    assert "sample_limitation" in categories
    assert "synthetic_data_limitation" in categories


def test_detects_missing_dataset_version():
    findings = detect_limitations(_config(), {"dataset": "breast_cancer"})
    assert any(f.category == "reproducibility_limitation" for f in findings)


def test_detects_single_metric_limitation():
    findings = detect_limitations(_config(metrics_requested=["f1"]), {"dataset": "breast_cancer"})
    assert any(f.category == "measurement_limitation" for f in findings)


def test_no_single_metric_limitation_when_multiple_requested():
    findings = detect_limitations(
        _config(metrics_requested=["f1", "pr_auc"], num_runs=50, dataset_version_id="v1"),
        {"dataset": "breast_cancer"},
    )
    assert not any(f.category == "measurement_limitation" for f in findings)


def test_detects_process_sandbox_isolation_limitation():
    findings = detect_limitations(_config(), {"dataset": "x"}, isolation_level="PROCESS_RESOURCE_LIMITED")
    assert any(f.category == "sandbox_isolation_limitation" for f in findings)


def test_well_specified_config_has_fewer_findings():
    findings = detect_limitations(
        _config(
            num_runs=50,
            metrics_requested=["f1", "pr_auc"],
            dataset_version_id="v1",
            resource_limits={"cpu": 4.0},
        ),
        {"dataset": "breast_cancer"},
        isolation_level="DOCKER",
    )
    assert findings == []


def test_next_experiment_inconclusive_suggests_more_runs():
    config = _config(num_runs=5)
    candidates = propose_next_experiments(config, ConclusionStatus.INCONCLUSIVE)
    assert any(c.category == "increase_sample_size" for c in candidates)
    assert "20" in candidates[0].description  # 5 * 4


def test_next_experiment_supported_suggests_generalization_and_robustness():
    candidates = propose_next_experiments(_config(), ConclusionStatus.SUPPORTED)
    categories = {c.category for c in candidates}
    assert "test_generalization" in categories
    assert "test_robustness" in categories


def test_next_experiment_not_supported_suggests_baseline_change():
    candidates = propose_next_experiments(_config(), ConclusionStatus.NOT_SUPPORTED)
    assert any(c.category == "change_baseline" for c in candidates)


def test_next_experiment_always_suggests_ablation():
    for status in ConclusionStatus:
        candidates = propose_next_experiments(_config(), status)
        assert any(c.category == "ablation" for c in candidates)
