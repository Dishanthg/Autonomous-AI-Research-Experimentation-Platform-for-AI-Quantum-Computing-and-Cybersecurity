from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.enums import DecisionOutcome, ExperimentStatus, GateType
from app.models.experiment import Artifact, Experiment, ExperimentConfig, ExperimentRun
from app.models.hypothesis import Hypothesis
from app.models.project import ResearchDecision
from app.models.result import Limitation, Result, StatisticalTest
from app.models.user import User
from app.sandbox.executor import ProcessSandboxNotAllowedError, SandboxUnavailableError
from app.schemas.experiment import (
    ApprovalRequest,
    ArtifactOut,
    ExperimentConfigCreate,
    ExperimentConfigOut,
    ExperimentCreate,
    ExperimentOut,
    ExperimentRunOut,
)
from app.schemas.result import ResultOut, StatisticalTestOut
from app.security.rbac import require_any, require_researcher
from app.services.audit import record_audit
from app.services.critic.checklist import critique_experiment_config
from app.services.execution.analysis import analyze_experiment
from app.services.execution.orchestrator import (
    ExperimentNotApprovedError,
    execute_experiment_config,
)
from app.services.execution.pqc_runner import PQCBackendUnavailableError
from app.services.memory.queries import find_duplicate_experiment
from app.services.next_experiment.generator import propose_next_experiments

router = APIRouter(prefix="/experiments", tags=["experiments"])


@router.post("", response_model=ExperimentOut, status_code=201)
def create_experiment(
    payload: ExperimentCreate, user: User = Depends(require_researcher), db: Session = Depends(get_db)
):
    hyp = db.get(Hypothesis, payload.hypothesis_id)
    if not hyp:
        raise HTTPException(status_code=404, detail="Hypothesis not found")

    exp = Experiment(**payload.model_dump())
    db.add(exp)
    db.flush()
    record_audit(
        db, actor_user_id=user.id, action="experiment.create", resource_type="experiment", resource_id=exp.id
    )
    db.commit()
    db.refresh(exp)
    return exp


@router.get("/{experiment_id}", response_model=ExperimentOut)
def get_experiment(experiment_id: str, user: User = Depends(require_any), db: Session = Depends(get_db)):
    exp = db.get(Experiment, experiment_id)
    if not exp:
        raise HTTPException(status_code=404, detail="Experiment not found")
    return exp


@router.post("/{experiment_id}/configs", response_model=ExperimentConfigOut, status_code=201)
def create_config(
    experiment_id: str,
    payload: ExperimentConfigCreate,
    user: User = Depends(require_researcher),
    db: Session = Depends(get_db),
):
    exp = db.get(Experiment, experiment_id)
    if not exp:
        raise HTTPException(status_code=404, detail="Experiment not found")

    latest = (
        db.query(ExperimentConfig)
        .filter(ExperimentConfig.experiment_id == experiment_id)
        .order_by(ExperimentConfig.version.desc())
        .first()
    )
    next_version = (latest.version + 1) if latest else 1

    data = payload.model_dump(exclude={"codegen_spec", "experiment_id"})
    config = ExperimentConfig(experiment_id=experiment_id, version=next_version, **data)
    config.software_environment = {
        **(config.software_environment or {}),
        "codegen_spec": payload.codegen_spec,
    }
    db.add(config)
    exp.status = ExperimentStatus.PLANNED
    db.flush()
    record_audit(
        db,
        actor_user_id=user.id,
        action="experiment_config.create",
        resource_type="experiment_config",
        resource_id=config.id,
    )
    db.commit()
    db.refresh(config)
    return config


@router.post("/configs/{config_id}/critique")
def critique_config(config_id: str, user: User = Depends(require_researcher), db: Session = Depends(get_db)):
    config = db.get(ExperimentConfig, config_id)
    if not config:
        raise HTTPException(status_code=404, detail="Config not found")
    report = critique_experiment_config(config)
    record_audit(
        db,
        actor_user_id=user.id,
        action="experiment_config.critique",
        resource_type="experiment_config",
        resource_id=config.id,
        after_state={"objections": [o.__dict__ for o in report.objections]},
    )
    db.commit()
    return {
        "objections": [
            {"severity": o.severity, "category": o.category, "message": o.message} for o in report.objections
        ],
        "has_blocking": report.has_blocking,
    }


@router.post("/configs/{config_id}/approve", response_model=ExperimentConfigOut)
def approve_config(
    config_id: str,
    payload: ApprovalRequest,
    user: User = Depends(require_researcher),
    db: Session = Depends(get_db),
):
    """Human Approval Gate 1 (Section H). Refuses to approve a config with
    an unresolved blocking critic objection, or (Priority 7: Research
    Memory actually influencing the pipeline) one that Research Memory
    finds is an exact duplicate of an already-existing experiment in this
    project, unless the researcher explicitly overrides that warning."""
    config = db.get(ExperimentConfig, config_id)
    if not config:
        raise HTTPException(status_code=404, detail="Config not found")
    exp = db.get(Experiment, config.experiment_id)

    report = critique_experiment_config(config)
    if report.has_blocking:
        raise HTTPException(
            status_code=409,
            detail={
                "message": "Cannot approve: blocking critic objections unresolved.",
                "objections": [o.__dict__ for o in report.objections],
            },
        )

    if config.baseline_spec and config.model_spec and not payload.override_duplicate_warning:
        duplicate = find_duplicate_experiment(
            db,
            project_id=exp.project_id,
            domain=exp.domain.value,
            baseline=config.baseline_spec,
            proposed=config.model_spec,
            dataset_id=config.dataset_id,
            exclude_experiment_id=exp.id,
        )
        if duplicate is not None:
            raise HTTPException(
                status_code=409,
                detail={
                    "message": (
                        "Research Memory found an identical (domain, baseline, proposed, dataset) "
                        "experiment already in this project. Re-submit with "
                        "override_duplicate_warning=true to approve anyway."
                    ),
                    "duplicate": duplicate,
                },
            )

    config.approved = True
    config.approved_by_user_id = user.id
    exp.status = ExperimentStatus.APPROVED

    decision = ResearchDecision(
        project_id=exp.project_id,
        gate_type=GateType.PLAN_APPROVAL,
        subject_type="experiment_config",
        subject_id=config.id,
        outcome=DecisionOutcome.APPROVED,
        actor_user_id=user.id,
        rationale=payload.rationale,
    )
    db.add(decision)
    db.flush()
    record_audit(
        db,
        actor_user_id=user.id,
        action="experiment_config.approve",
        resource_type="experiment_config",
        resource_id=config.id,
    )
    db.commit()
    db.refresh(config)
    return config


@router.post("/configs/{config_id}/execute", response_model=ExperimentRunOut)
def execute_config(
    config_id: str,
    payload: ApprovalRequest,
    user: User = Depends(require_researcher),
    db: Session = Depends(get_db),
):
    """Human Approval Gate 2 (Section H): this call itself IS the execution
    approval - it is only reachable by a RESEARCHER/ADMIN and is fully
    audit-logged. Refuses if the config was not already approved at Gate 1."""
    config = db.get(ExperimentConfig, config_id)
    if not config:
        raise HTTPException(status_code=404, detail="Config not found")
    exp = db.get(Experiment, config.experiment_id)
    hyp = db.get(Hypothesis, exp.hypothesis_id)

    decision = ResearchDecision(
        project_id=exp.project_id,
        gate_type=GateType.EXECUTION_APPROVAL,
        subject_type="experiment_config",
        subject_id=config.id,
        outcome=DecisionOutcome.APPROVED,
        actor_user_id=user.id,
        rationale=payload.rationale,
    )
    db.add(decision)

    spec = (config.software_environment or {}).get("codegen_spec", {})
    try:
        run, metrics_json = execute_experiment_config(db, config, exp.domain.value, spec)
    except ExperimentNotApprovedError as exc:
        raise HTTPException(status_code=409, detail=str(exc))
    except SandboxUnavailableError as exc:
        raise HTTPException(status_code=503, detail=f"Sandbox unavailable: {exc}")
    except ProcessSandboxNotAllowedError as exc:
        raise HTTPException(status_code=503, detail=f"Sandbox unavailable: {exc}")
    except PQCBackendUnavailableError as exc:
        raise HTTPException(status_code=503, detail=f"PQC backend unavailable: {exc}")

    exp.status = ExperimentStatus.COMPLETED if run.status.value == "COMPLETED" else ExperimentStatus.FAILED

    if metrics_json is not None:
        analyze_experiment(
            db,
            experiment_id=exp.id,
            hypothesis=hyp,
            run_id=run.id,
            metrics_json=metrics_json,
            config=config,
            isolation_level=run.isolation_level,
        )
        exp.status = ExperimentStatus.ANALYZED

    record_audit(
        db,
        actor_user_id=user.id,
        action="experiment_config.execute",
        resource_type="experiment_run",
        resource_id=run.id,
    )
    db.commit()
    db.refresh(run)
    return run


@router.get("/runs/{run_id}/artifacts", response_model=list[ArtifactOut])
def get_run_artifacts(run_id: str, user: User = Depends(require_any), db: Session = Depends(get_db)):
    """Section 22/55: real, checksummed code/config/log artifacts persisted
    for this run by `app.services.execution.artifacts.persist_run_artifacts`."""
    run = db.get(ExperimentRun, run_id)
    if not run:
        raise HTTPException(status_code=404, detail="Run not found")
    return db.query(Artifact).filter(Artifact.run_id == run_id).all()


@router.get("/{experiment_id}/results", response_model=list[ResultOut])
def get_results(experiment_id: str, user: User = Depends(require_any), db: Session = Depends(get_db)):
    return db.query(Result).filter(Result.experiment_id == experiment_id).all()


@router.get("/results/{result_id}/statistics", response_model=list[StatisticalTestOut])
def get_statistics(result_id: str, user: User = Depends(require_any), db: Session = Depends(get_db)):
    return db.query(StatisticalTest).filter(StatisticalTest.result_id == result_id).all()


@router.get("/{experiment_id}/limitations")
def get_limitations(experiment_id: str, user: User = Depends(require_any), db: Session = Depends(get_db)):
    """Section 41: deterministically-detected limitations for this
    experiment, written by the Result Analyzer at analysis time."""
    rows = db.query(Limitation).filter(Limitation.experiment_id == experiment_id).all()
    return [
        {"category": r.category, "description": r.description, "detected_by": r.detected_by} for r in rows
    ]


@router.get("/{experiment_id}/next-experiments")
def get_next_experiments(
    experiment_id: str, user: User = Depends(require_any), db: Session = Depends(get_db)
):
    """Section 42: candidate follow-up experiments, recomputed from the
    latest concluded Result + its ExperimentConfig. Proposals only - the
    researcher must approve one before it becomes a real experiment."""
    result = (
        db.query(Result)
        .filter(Result.experiment_id == experiment_id, Result.conclusion_status.isnot(None))
        .order_by(Result.created_at.desc())
        .first()
    )
    if not result:
        raise HTTPException(status_code=404, detail="No concluded result found for this experiment yet")

    config = (
        db.query(ExperimentConfig)
        .filter(ExperimentConfig.experiment_id == experiment_id, ExperimentConfig.approved.is_(True))
        .order_by(ExperimentConfig.version.desc())
        .first()
    )
    if not config:
        raise HTTPException(status_code=404, detail="No approved config found for this experiment")

    candidates = propose_next_experiments(config, result.conclusion_status)
    return [{"category": c.category, "description": c.description} for c in candidates]
