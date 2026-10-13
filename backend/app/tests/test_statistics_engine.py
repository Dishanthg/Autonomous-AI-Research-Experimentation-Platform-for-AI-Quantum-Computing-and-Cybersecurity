import numpy as np

from app.models.enums import ConclusionStatus
from app.services.statistics.conclusion import DecisionRule, evaluate_hypothesis
from app.services.statistics.engine import cohens_d, compare_two_groups, describe, holm_bonferroni


def test_describe_basic_stats():
    values = [1.0, 2.0, 3.0, 4.0, 5.0]
    d = describe(values)
    assert d.n == 5
    assert d.mean == 3.0
    assert d.median == 3.0
    assert d.ci_lower <= d.mean <= d.ci_upper


def test_cohens_d_zero_for_identical_groups():
    a = [1.0, 2.0, 3.0]
    b = [1.0, 2.0, 3.0]
    assert cohens_d(a, b) == 0.0


def test_cohens_d_large_for_clearly_separated_groups():
    rng = np.random.default_rng(0)
    a = (rng.normal(0, 0.1, 100) + 5).tolist()
    b = (rng.normal(0, 0.1, 100) + 0).tolist()
    d = cohens_d(a, b)
    assert d > 5  # huge, obviously-separated effect


def test_compare_two_groups_detects_real_difference():
    rng = np.random.default_rng(1)
    a = (rng.normal(0.9, 0.02, 10)).tolist()
    b = (rng.normal(0.7, 0.02, 10)).tolist()
    result = compare_two_groups(a, b)
    assert result.p_value < 0.05
    assert result.effect_size > 0


def test_compare_two_groups_no_difference_not_significant():
    rng = np.random.default_rng(2)
    a = rng.normal(0.5, 0.05, 10).tolist()
    b = rng.normal(0.5, 0.05, 10).tolist()
    result = compare_two_groups(a, b)
    assert result.p_value > 0.01  # should not find a spurious strong effect


def test_holm_bonferroni_more_conservative_than_raw():
    raw = [0.01, 0.02, 0.03]
    adjusted = holm_bonferroni(raw)
    assert all(adj >= r for adj, r in zip(adjusted, raw))


def test_conclusion_engine_supported():
    rule = DecisionRule(metric="f1", alpha=0.05, min_effect_size=0.2, direction="greater")
    rng = np.random.default_rng(3)
    a = (rng.normal(0.9, 0.02, 10)).tolist()
    b = (rng.normal(0.7, 0.02, 10)).tolist()
    comparison = compare_two_groups(a, b)
    status, rationale = evaluate_hypothesis(rule, comparison)
    assert status == ConclusionStatus.SUPPORTED
    assert "p=" in rationale


def test_conclusion_engine_inconclusive_when_effect_too_small():
    rule = DecisionRule(metric="f1", alpha=0.05, min_effect_size=5.0, direction="greater")
    rng = np.random.default_rng(4)
    a = (rng.normal(0.71, 0.02, 10)).tolist()
    b = (rng.normal(0.70, 0.02, 10)).tolist()
    comparison = compare_two_groups(a, b)
    status, _ = evaluate_hypothesis(rule, comparison)
    assert status in (ConclusionStatus.INCONCLUSIVE, ConclusionStatus.NOT_SUPPORTED)


def test_conclusion_engine_wrong_direction_not_supported():
    rule = DecisionRule(metric="f1", alpha=0.05, min_effect_size=0.1, direction="greater")
    rng = np.random.default_rng(5)
    a = (rng.normal(0.5, 0.02, 10)).tolist()
    b = (rng.normal(0.9, 0.02, 10)).tolist()  # baseline much better than "proposed"
    comparison = compare_two_groups(a, b)
    status, _ = evaluate_hypothesis(rule, comparison)
    assert status == ConclusionStatus.NOT_SUPPORTED
