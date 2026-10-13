"""Deterministic Limitation Detector (Section 41).

Inspects a completed experiment's config, dataset reference, codegen spec,
and run metadata for known limitation categories. Purely rule-based - no
LLM call, no judgment calls that could be argued away. Every finding here
is written to the `limitations` table with `detected_by =
"deterministic:limitation_detector"`, distinguishable from any future
LLM-detected limitation (which would be tagged `llm:<model>`) or a
human-added one (`human:<user_id>`).
"""

from dataclasses import dataclass

from app.models.experiment import ExperimentConfig
from app.sandbox.base import IsolationLevel

MIN_ROBUST_SAMPLE_SIZE = 30
LOW_CPU_LIMIT = 1.0
LOW_MEMORY_GB = 1


@dataclass
class DetectedLimitation:
    category: str
    description: str


def detect_limitations(
    config: ExperimentConfig,
    codegen_spec: dict,
    isolation_level: str | None = None,
) -> list[DetectedLimitation]:
    findings: list[DetectedLimitation] = []

    dataset_name = str(codegen_spec.get("dataset", ""))
    if dataset_name.startswith("synthetic") or "synthetic" in str(codegen_spec).lower():
        findings.append(
            DetectedLimitation(
                "synthetic_data_limitation",
                "The dataset used is synthetic (or contains a synthetic-data component). "
                "Findings should not be generalized to real-world data of the same nominal "
                "type without separate validation.",
            )
        )

    if config.num_runs < MIN_ROBUST_SAMPLE_SIZE:
        findings.append(
            DetectedLimitation(
                "sample_limitation",
                f"num_runs={config.num_runs} is below the {MIN_ROBUST_SAMPLE_SIZE}-run "
                "threshold generally recommended for a stable effect-size estimate; "
                "confidence intervals may be wide.",
            )
        )

    if not config.dataset_version_id:
        findings.append(
            DetectedLimitation(
                "reproducibility_limitation",
                "No pinned dataset_version_id is recorded on this config; exact dataset "
                "state at execution time is not independently verifiable.",
            )
        )

    resource_limits = config.resource_limits or {}
    cpu = resource_limits.get("cpu", None)
    if cpu is not None and cpu <= LOW_CPU_LIMIT:
        findings.append(
            DetectedLimitation(
                "computational_limitation",
                f"Experiment ran under a {cpu}-CPU resource limit; results (especially "
                "latency/timing metrics) may not reflect production-scale hardware.",
            )
        )

    if len(config.metrics_requested or []) < 2:
        findings.append(
            DetectedLimitation(
                "measurement_limitation",
                "Only one evaluation metric was requested; a single metric can miss "
                "trade-offs (e.g. recall vs. false-positive rate) a multi-metric "
                "evaluation would surface.",
            )
        )

    if isolation_level == IsolationLevel.PROCESS_RESOURCE_LIMITED.value:
        findings.append(
            DetectedLimitation(
                "sandbox_isolation_limitation",
                "This run executed under the reduced-isolation process-tier sandbox "
                "(ADR-009), not the fully-isolated Docker tier - acceptable for this "
                "platform's own reviewed templates, but the resource/timing measurements "
                "are not cgroup-enforced on this platform.",
            )
        )

    return findings
