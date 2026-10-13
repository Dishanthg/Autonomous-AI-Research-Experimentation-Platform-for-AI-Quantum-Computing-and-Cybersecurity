"""Research Memory (Section 34/T). Structured, bounded DB queries - NOT a
vector-similarity "recall everything" mechanism. Agents call these
functions explicitly and receive a small, relevant excerpt of prior
research state; they do not free-associate over the full project history.

This module is the target of the Memory Ablation (Section 35/62): callers
can pass `enabled=False` to simulate "no memory" and get empty results,
which is exactly how that ablation experiment is implemented (same code
path, one flag), guaranteeing the two conditions differ only in the
presence/absence of memory context.
"""

from typing import Optional

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.enums import HypothesisStatus, RunStatus
from app.models.experiment import Experiment, ExperimentConfig, ExperimentRun
from app.models.hypothesis import Hypothesis


def get_prior_experiments(
    db: Session, project_id: str, domain: Optional[str] = None, enabled: bool = True
) -> list[dict]:
    if not enabled:
        return []
    q = select(Experiment).where(Experiment.project_id == project_id)
    if domain:
        q = q.where(Experiment.domain == domain)
    experiments = db.execute(q).scalars().all()
    return [
        {"id": e.id, "objective": e.objective, "status": e.status.value, "domain": e.domain.value}
        for e in experiments
    ]


def get_failed_experiments(db: Session, project_id: str, enabled: bool = True) -> list[dict]:
    if not enabled:
        return []
    q = (
        select(Experiment, ExperimentRun)
        .join(ExperimentRun, ExperimentRun.experiment_id == Experiment.id)
        .where(Experiment.project_id == project_id, ExperimentRun.status == RunStatus.FAILED)
    )
    rows = db.execute(q).all()
    return [
        {
            "experiment_id": e.id,
            "objective": e.objective,
            "run_id": r.id,
            "stderr_excerpt": (r.stderr or "")[:500],
        }
        for e, r in rows
    ]


def get_unresolved_hypotheses(db: Session, project_id: str, enabled: bool = True) -> list[dict]:
    if not enabled:
        return []
    q = select(Hypothesis).where(
        Hypothesis.project_id == project_id,
        Hypothesis.status.in_(
            [
                HypothesisStatus.DRAFT,
                HypothesisStatus.QUALITY_CHECKED,
                HypothesisStatus.CRITIQUED,
                HypothesisStatus.APPROVED,
                HypothesisStatus.TESTING,
            ]
        ),
    )
    hyps = db.execute(q).scalars().all()
    return [
        {"id": h.id, "alternative_hypothesis": h.alternative_hypothesis, "status": h.status.value}
        for h in hyps
    ]


def find_duplicate_experiment(
    db: Session,
    project_id: str,
    domain: str,
    baseline: str,
    proposed: str,
    dataset_id: Optional[str],
    enabled: bool = True,
    exclude_experiment_id: Optional[str] = None,
) -> Optional[dict]:
    """Used to measure/prevent the 'duplicate experiment rate' metric
    (Section 35/72): has this exact (domain, baseline, proposed, dataset)
    combination already been run in this project?

    `exclude_experiment_id` lets a caller checking a config belonging to
    experiment X (e.g. at Gate 1 approval) exclude X's own prior config
    versions from counting as "a duplicate of itself" - see
    `app.api.v1.experiments.approve_config`."""
    if not enabled:
        return None
    q = (
        select(Experiment, ExperimentConfig)
        .join(ExperimentConfig, ExperimentConfig.experiment_id == Experiment.id)
        .where(
            Experiment.project_id == project_id,
            Experiment.domain == domain,
            ExperimentConfig.baseline_spec == baseline,
            ExperimentConfig.model_spec == proposed,
        )
    )
    if dataset_id:
        q = q.where(ExperimentConfig.dataset_id == dataset_id)
    if exclude_experiment_id:
        q = q.where(Experiment.id != exclude_experiment_id)
    row = db.execute(q).first()
    if row is None:
        return None
    e, c = row
    return {"experiment_id": e.id, "config_id": c.id, "status": e.status.value}
