"""Conclusion Engine (Section 40). Rule-based only - an LLM may explain a
conclusion in prose afterward, but this function alone decides
SUPPORTED / NOT_SUPPORTED / INCONCLUSIVE, evaluated strictly against the
hypothesis's pre-registered decision_rule (fixed before the experiment ran).
"""

from dataclasses import dataclass

from app.models.enums import ConclusionStatus
from app.services.statistics.engine import ComparisonResult


@dataclass
class DecisionRule:
    metric: str
    alpha: float = 0.05
    min_effect_size: float = 0.2
    direction: str = "greater"  # "greater" | "less" | "any"


def evaluate_hypothesis(rule: DecisionRule, comparison: ComparisonResult) -> tuple[ConclusionStatus, str]:
    significant = comparison.p_value < rule.alpha
    effect_ok = abs(comparison.effect_size) >= rule.min_effect_size

    if rule.direction == "greater":
        direction_ok = comparison.effect_size > 0
    elif rule.direction == "less":
        direction_ok = comparison.effect_size < 0
    else:
        direction_ok = True

    if not significant:
        return (
            ConclusionStatus.NOT_SUPPORTED if effect_ok and direction_ok else ConclusionStatus.INCONCLUSIVE,
            f"p={comparison.p_value:.4f} >= alpha={rule.alpha}; result is not statistically significant.",
        )

    if not direction_ok:
        return (
            ConclusionStatus.NOT_SUPPORTED,
            f"Effect direction ({comparison.effect_size:.3f}) does not match hypothesized "
            f"direction '{rule.direction}'.",
        )

    if not effect_ok:
        return (
            ConclusionStatus.INCONCLUSIVE,
            f"Statistically significant (p={comparison.p_value:.4f}) but effect size "
            f"({abs(comparison.effect_size):.3f}) is below the pre-registered minimum "
            f"({rule.min_effect_size}) - too small to be practically meaningful.",
        )

    return (
        ConclusionStatus.SUPPORTED,
        f"p={comparison.p_value:.4f} < alpha={rule.alpha}, effect size "
        f"{comparison.effect_size:.3f} ({comparison.effect_size_type}) meets pre-registered "
        f"threshold of {rule.min_effect_size} in the hypothesized direction.",
    )
