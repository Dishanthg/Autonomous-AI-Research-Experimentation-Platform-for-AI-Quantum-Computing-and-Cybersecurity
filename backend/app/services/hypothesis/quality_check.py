"""Hypothesis Quality Check (Section 14/M). Deterministic 8-point checklist,
independent of any LLM judgment. A hypothesis below the configured
threshold cannot advance past DRAFT (enforced as a state-machine guard in
the API layer, not merely a suggestion)."""

from dataclasses import dataclass

from app.models.hypothesis import Hypothesis

QUALITY_THRESHOLD = 6  # out of 8


@dataclass
class QualityCheckResult:
    score: int
    max_score: int
    checks: dict[str, bool]
    passed: bool


def run_quality_check(hypothesis: Hypothesis) -> QualityCheckResult:
    checks = {
        "testability": bool(hypothesis.null_hypothesis and hypothesis.alternative_hypothesis),
        "specificity": len(hypothesis.independent_variables or []) > 0
        and len(hypothesis.dependent_variables or []) > 0,
        "measurability": bool(hypothesis.evaluation_metric),
        "falsifiability": _is_falsifiable(hypothesis),
        "dataset_availability": bool(hypothesis.dataset_id),
        "experimental_feasibility": bool(hypothesis.baseline),
        "baseline_availability": bool(hypothesis.baseline),
        "confounders_considered": bool(hypothesis.potential_confounders),
    }
    score = sum(1 for v in checks.values() if v)
    max_score = len(checks)
    return QualityCheckResult(
        score=score, max_score=max_score, checks=checks, passed=score >= QUALITY_THRESHOLD
    )


def _is_falsifiable(hypothesis: Hypothesis) -> bool:
    rule = hypothesis.decision_rule or {}
    return all(k in rule for k in ("metric", "alpha", "min_effect_size"))
