"""Research Critic - deterministic structural checklist (Section 30/U).

Runs BEFORE any LLM narrative critique and cannot be overridden by one: if
a structural objection fires here, it is recorded as an objection
regardless of what an LLM-generated critique text says. This keeps the
critic's core function auditable and independent of LLM behavior, per
Section 31's "use deterministic code for tasks that do not require LLM
reasoning."
"""

from dataclasses import dataclass, field

from app.models.experiment import ExperimentConfig
from app.models.hypothesis import Hypothesis


@dataclass
class Objection:
    severity: str  # "blocking" | "major" | "minor"
    category: str
    message: str


@dataclass
class CritiqueReport:
    objections: list[Objection] = field(default_factory=list)

    @property
    def has_blocking(self) -> bool:
        return any(o.severity == "blocking" for o in self.objections)


def critique_hypothesis(hypothesis: Hypothesis) -> CritiqueReport:
    objections = []

    if not hypothesis.dataset_id:
        objections.append(
            Objection("blocking", "dataset_quality", "No dataset is specified for this hypothesis.")
        )

    if not hypothesis.potential_confounders:
        objections.append(Objection("major", "confounders", "No potential confounders were documented."))

    rule = hypothesis.decision_rule or {}
    if rule.get("min_effect_size", 0) <= 0:
        objections.append(
            Objection(
                "blocking",
                "statistical_methodology",
                "Pre-registered decision rule has no minimum effect-size threshold - "
                "a purely p-value-based rule risks flagging trivial effects as SUPPORTED.",
            )
        )
    if rule.get("alpha", 1) > 0.10:
        objections.append(
            Objection(
                "major",
                "statistical_methodology",
                f"Alpha threshold ({rule.get('alpha')}) is unusually permissive.",
            )
        )

    if not hypothesis.baseline:
        objections.append(Objection("blocking", "baseline_selection", "No baseline method specified."))

    return CritiqueReport(objections=objections)


def critique_experiment_config(config: ExperimentConfig) -> CritiqueReport:
    objections = []

    if config.num_runs < 3:
        objections.append(
            Objection(
                "major",
                "sample_size",
                f"num_runs={config.num_runs} is too small to support a meaningful statistical "
                f"test (t-test/Mann-Whitney need at least 3-5 per arm for a stable estimate).",
            )
        )

    if not config.metrics_requested:
        objections.append(Objection("blocking", "metric_selection", "No evaluation metrics requested."))

    if config.dataset_id and not config.dataset_version_id:
        objections.append(
            Objection(
                "major",
                "reproducibility",
                "A dataset is referenced without a pinned dataset_version - results may not be reproducible.",
            )
        )

    if not config.random_seed and config.random_seed != 0:
        objections.append(Objection("major", "reproducibility", "No random seed recorded."))

    return CritiqueReport(objections=objections)
