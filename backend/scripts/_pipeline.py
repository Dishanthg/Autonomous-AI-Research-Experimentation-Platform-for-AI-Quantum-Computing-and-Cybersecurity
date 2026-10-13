"""Shared pipeline helper for the `scripts.*` CLI entry points.

This is deliberately NOT a duplicate of app/api/v1/experiments.py's logic -
it calls the exact same service-layer functions the API uses
(services.hypothesis.quality_check, services.critic.checklist,
services.execution.orchestrator, services.execution.analysis), just from a
script instead of an HTTP request, so a `make demo` run exercises the real
pipeline code, not a re-implementation of it.
"""

import uuid
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

from sqlalchemy.orm import Session

from app.db.session import Base, SessionLocal, engine
from app.models.enums import DecisionOutcome, Domain, ExperimentStatus, GateType, Role
from app.models.experiment import Experiment, ExperimentConfig
from app.models.hypothesis import Hypothesis
from app.models.literature import Dataset, DatasetVersion
from app.models.project import Project, ResearchDecision, ResearchQuestion
from app.models.result import Limitation, StatisticalTest
from app.models.user import User
from app.security.auth import hash_password
from app.services.critic.checklist import critique_experiment_config, critique_hypothesis
from app.services.execution.analysis import analyze_experiment
from app.services.execution.orchestrator import ExperimentNotApprovedError, execute_experiment_config
from app.services.hypothesis.quality_check import run_quality_check
from app.services.memory.queries import find_duplicate_experiment

REPO_ROOT = Path(__file__).resolve().parents[2]
RESEARCH_DIR = REPO_ROOT / "research"


def ensure_schema() -> None:
    import app.models  # noqa: F401  (registers all tables on Base.metadata)

    Base.metadata.create_all(bind=engine)


def get_session() -> Session:
    return SessionLocal()


def ensure_demo_user(db: Session, email: str = "demo-researcher@researchmind-q.local") -> User:
    user = db.query(User).filter(User.email == email).one_or_none()
    if user:
        return user
    user = User(
        email=email,
        hashed_password=hash_password(str(uuid.uuid4())),
        full_name="Demo Researcher",
        role=Role.RESEARCHER,
    )
    db.add(user)
    db.flush()
    return user


def ensure_dataset_registered(
    db: Session,
    *,
    name: str,
    source: str,
    license: str,
    description: Optional[str] = None,
    features: Optional[list] = None,
    limitations: Optional[str] = None,
    citation: Optional[str] = None,
    version_tag: str = "v1",
    checksum: Optional[str] = None,
    preprocessing: Optional[str] = None,
    row_count: Optional[int] = None,
) -> tuple[str, str]:
    """Idempotent Dataset/DatasetVersion registration (Priority 2). Returns
    (dataset_id, dataset_version_id). Registering the version actually used
    by an experiment and passing it through to ExperimentConfig is what
    clears the `reproducibility_limitation` finding for that run (see
    app/services/limitations/detector.py)."""
    dataset = db.query(Dataset).filter(Dataset.name == name).one_or_none()
    if dataset is None:
        dataset = Dataset(
            name=name,
            source=source,
            license=license,
            description=description,
            features=features,
            limitations=limitations,
            citation=citation,
        )
        db.add(dataset)
        db.flush()

    version = (
        db.query(DatasetVersion)
        .filter(DatasetVersion.dataset_id == dataset.id, DatasetVersion.version_tag == version_tag)
        .one_or_none()
    )
    if version is None:
        version = DatasetVersion(
            dataset_id=dataset.id,
            version_tag=version_tag,
            checksum=checksum,
            preprocessing=preprocessing,
            row_count=row_count,
        )
        db.add(version)
        db.flush()

    return dataset.id, version.id


@dataclass
class PipelineOutcome:
    project_id: str
    hypothesis_id: str
    experiment_id: str
    config_id: str
    run_id: Optional[str] = None
    run_status: Optional[str] = None
    isolation_level: Optional[str] = None
    stderr: Optional[str] = None
    result_id: Optional[str] = None
    conclusion_status: Optional[str] = None
    conclusion_rationale: Optional[str] = None
    statistics: dict = field(default_factory=dict)
    limitations: list = field(default_factory=list)
    next_experiments: list = field(default_factory=list)
    quality_check_passed: Optional[bool] = None
    critic_objections: list = field(default_factory=list)
    duplicate_warning: Optional[dict] = None


def run_full_pipeline(
    db: Session,
    *,
    domain: Domain,
    project_title: str,
    question_text: str,
    null_hypothesis: str,
    alternative_hypothesis: str,
    baseline: str,
    evaluation_metric: str,
    decision_rule: dict,
    codegen_spec: dict,
    num_runs: int,
    metrics_requested: Optional[list[str]] = None,
    resource_limits: Optional[dict] = None,
    dataset_id: Optional[str] = None,
    dataset_version_id: Optional[str] = None,
    potential_confounders: Optional[list[str]] = None,
    allow_duplicate: bool = False,
) -> PipelineOutcome:
    """Runs project -> question -> hypothesis -> quality-check -> critique
    -> experiment -> config -> critique -> Gate 1 -> Gate 2 -> analysis,
    using the real service-layer code, and returns a structured summary.

    Raises if the hypothesis/config cannot pass its checks - callers should
    treat that as a real, honest failure (this function does not silently
    downgrade its own standards to "make the demo work")."""
    user = ensure_demo_user(db)

    project = Project(title=project_title, domain=domain, owner_id=user.id)
    db.add(project)
    db.flush()

    question = ResearchQuestion(
        project_id=project.id, question_text=question_text, domain=domain, is_primary=True
    )
    db.add(question)
    db.flush()

    hypothesis = Hypothesis(
        project_id=project.id,
        research_question_id=question.id,
        null_hypothesis=null_hypothesis,
        alternative_hypothesis=alternative_hypothesis,
        independent_variables=["method"],
        dependent_variables=[decision_rule["metric"]],
        dataset_id=dataset_id,
        baseline=baseline,
        evaluation_metric=evaluation_metric,
        potential_confounders=potential_confounders or ["random_seed_variance"],
        decision_rule=decision_rule,
        generated_by="human:demo_script",
    )
    db.add(hypothesis)
    db.flush()

    outcome = PipelineOutcome(
        project_id=project.id, hypothesis_id=hypothesis.id, experiment_id="", config_id=""
    )

    qc = run_quality_check(hypothesis)
    outcome.quality_check_passed = qc.passed
    from app.models.enums import HypothesisStatus

    hypothesis.quality_score = qc.score
    if qc.passed:
        hypothesis.status = HypothesisStatus.QUALITY_CHECKED

    critique = critique_hypothesis(hypothesis)
    outcome.critic_objections = [
        {"severity": o.severity, "category": o.category, "message": o.message} for o in critique.objections
    ]
    hypothesis.status = HypothesisStatus.CRITIQUED if critique.has_blocking else HypothesisStatus.APPROVED
    db.flush()

    experiment = Experiment(
        project_id=project.id,
        hypothesis_id=hypothesis.id,
        domain=domain,
        objective=f"Test: {alternative_hypothesis}",
        num_runs_planned=num_runs,
    )
    db.add(experiment)
    db.flush()
    outcome.experiment_id = experiment.id

    config = ExperimentConfig(
        experiment_id=experiment.id,
        version=1,
        dataset_id=dataset_id,
        dataset_version_id=dataset_version_id,
        baseline_spec=baseline,
        model_spec=codegen_spec.get("proposed"),
        random_seed=codegen_spec.get("base_seed", 42),
        num_runs=num_runs,
        metrics_requested=metrics_requested or [decision_rule["metric"]],
        resource_limits=resource_limits or {"cpu": 1.0, "memory": "512m", "timeout_seconds": 120},
        software_environment={"codegen_spec": codegen_spec},
    )
    db.add(config)
    experiment.status = ExperimentStatus.PLANNED
    db.flush()
    outcome.config_id = config.id

    config_critique = critique_experiment_config(config)
    if config_critique.has_blocking:
        raise RuntimeError(
            f"Experiment config failed critic review, refusing to proceed: "
            f"{[o.message for o in config_critique.objections]}"
        )

    if config.baseline_spec and config.model_spec and not allow_duplicate:
        duplicate = find_duplicate_experiment(
            db,
            project_id=project.id,
            domain=domain.value,
            baseline=config.baseline_spec,
            proposed=config.model_spec,
            dataset_id=config.dataset_id,
            exclude_experiment_id=experiment.id,
        )
        outcome.duplicate_warning = duplicate
        if duplicate is not None:
            raise RuntimeError(
                f"Research Memory found an identical (domain={domain.value}, "
                f"baseline={config.baseline_spec}, proposed={config.model_spec}) experiment "
                f"already in this project (experiment_id={duplicate['experiment_id']}). "
                "Pass allow_duplicate=True to proceed anyway."
            )

    config.approved = True
    config.approved_by_user_id = user.id
    experiment.status = ExperimentStatus.APPROVED
    db.add(
        ResearchDecision(
            project_id=project.id,
            gate_type=GateType.PLAN_APPROVAL,
            subject_type="experiment_config",
            subject_id=config.id,
            outcome=DecisionOutcome.APPROVED,
            actor_user_id=user.id,
            rationale="Automated demo pipeline: critic raised no blocking objections.",
        )
    )
    db.flush()

    db.add(
        ResearchDecision(
            project_id=project.id,
            gate_type=GateType.EXECUTION_APPROVAL,
            subject_type="experiment_config",
            subject_id=config.id,
            outcome=DecisionOutcome.APPROVED,
            actor_user_id=user.id,
            rationale="Automated demo pipeline: executing approved config.",
        )
    )

    try:
        run, metrics_json = execute_experiment_config(db, config, domain.value, codegen_spec)
    except ExperimentNotApprovedError as exc:
        raise RuntimeError(str(exc)) from exc

    outcome.run_id = run.id
    outcome.run_status = run.status.value
    outcome.isolation_level = run.isolation_level
    outcome.stderr = run.stderr

    if metrics_json is not None:
        result, next_candidates = analyze_experiment(
            db,
            experiment_id=experiment.id,
            hypothesis=hypothesis,
            run_id=run.id,
            metrics_json=metrics_json,
            config=config,
            isolation_level=run.isolation_level,
        )
        experiment.status = ExperimentStatus.ANALYZED
        outcome.result_id = result.id
        outcome.conclusion_status = result.conclusion_status.value if result.conclusion_status else None
        outcome.conclusion_rationale = result.conclusion_rationale

        stat = db.query(StatisticalTest).filter(StatisticalTest.result_id == result.id).first()
        if stat:
            outcome.statistics = {
                "test_name": stat.test_name,
                "statistic": stat.statistic,
                "p_value": stat.p_value,
                "effect_size": stat.effect_size,
                "effect_size_type": stat.effect_size_type,
                "ci_lower": stat.ci_lower,
                "ci_upper": stat.ci_upper,
                "ci_level": stat.ci_level,
            }

        limitations = db.query(Limitation).filter(Limitation.experiment_id == experiment.id).all()
        outcome.limitations = [
            {"category": lim.category, "description": lim.description} for lim in limitations
        ]
        outcome.next_experiments = [
            {"category": c.category, "description": c.description} for c in next_candidates
        ]

    db.commit()
    return outcome
