"""Next-Experiment Generator (Section 42). Deterministic candidate
generation from a concluded experiment's conclusion status and config -
proposes, never creates. Every candidate still requires a researcher to
turn it into an approved experiment through the normal pipeline (Section
42: "The researcher must approve the next experiment.").
"""

from dataclasses import dataclass

from app.models.enums import ConclusionStatus
from app.models.experiment import ExperimentConfig


@dataclass
class NextExperimentCandidate:
    category: str
    description: str


def propose_next_experiments(
    config: ExperimentConfig,
    conclusion_status: ConclusionStatus,
) -> list[NextExperimentCandidate]:
    candidates: list[NextExperimentCandidate] = []

    if conclusion_status == ConclusionStatus.INCONCLUSIVE:
        candidates.append(
            NextExperimentCandidate(
                "increase_sample_size",
                f"Re-run with num_runs={config.num_runs * 4} (was {config.num_runs}) to narrow "
                "the confidence interval and determine whether the true effect clears the "
                "pre-registered minimum effect size.",
            )
        )

    if conclusion_status == ConclusionStatus.NOT_SUPPORTED:
        candidates.append(
            NextExperimentCandidate(
                "change_baseline",
                "The proposed method did not outperform this baseline. Consider whether "
                "the baseline was too strong, or whether the proposed method needs "
                "hyperparameter tuning before a fair comparison can be made.",
            )
        )

    if conclusion_status == ConclusionStatus.SUPPORTED:
        candidates.append(
            NextExperimentCandidate(
                "test_generalization",
                "Result was SUPPORTED on this dataset/config. Test on a second, "
                "independent dataset to check whether the effect generalizes before "
                "treating it as a general finding.",
            )
        )
        candidates.append(
            NextExperimentCandidate(
                "test_robustness",
                "Repeat with a different random seed range and/or class-imbalance ratio "
                "to test whether the SUPPORTED conclusion is robust to those choices.",
            )
        )

    candidates.append(
        NextExperimentCandidate(
            "ablation",
            "Run an ablation removing one component of the proposed method at a time to "
            "attribute the observed effect to a specific mechanism rather than the "
            "method as a whole.",
        )
    )

    return candidates
