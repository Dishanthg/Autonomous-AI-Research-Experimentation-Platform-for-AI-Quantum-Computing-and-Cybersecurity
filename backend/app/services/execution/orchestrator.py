"""Experiment Execution Manager (Section 20/N). Deterministic orchestration
only - no LLM call anywhere in this path. Ties together:
  ExperimentConfig (must be approved) -> generated code -> sandbox execution
  -> ExperimentRun record -> parsed metrics.json -> Metric rows.

Gate enforcement: `execute_experiment_config` refuses to run a config that
is not marked `approved=True` (Section H Gate 1) - this is checked here,
not just in the API layer, so no other code path can bypass it.
"""

from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.models.enums import RunStatus
from app.models.experiment import ExperimentConfig, ExperimentRun
from app.sandbox import executor as sandbox_executor
from app.sandbox.executor import ProcessSandboxNotAllowedError, SandboxResult, SandboxUnavailableError
from app.services.codegen import ai_templates, cyber_templates
from app.services.execution.artifacts import persist_run_artifacts


class ExperimentNotApprovedError(RuntimeError):
    """Raised when execution is attempted on a config that hasn't passed
    the human approval gate (Rule: never execute without approval)."""


def generate_code(domain: str, spec: dict) -> str:
    if domain == "AI":
        return ai_templates.render_model_comparison_script(
            dataset=spec["dataset"],
            baseline=spec["baseline"],
            proposed=spec["proposed"],
            num_runs=spec.get("num_runs", 5),
            base_seed=spec.get("base_seed", 42),
            n_samples=spec.get("n_samples", 2000),
            n_features=spec.get("n_features", 20),
        )
    if domain in ("CYBERSECURITY",):
        return cyber_templates.render_intrusion_detection_script(
            baseline=spec["baseline"],
            proposed=spec["proposed"],
            num_runs=spec.get("num_runs", 5),
            base_seed=spec.get("base_seed", 42),
            n_samples=spec.get("n_samples", 4000),
            n_features=spec.get("n_features", 12),
        )
    raise ValueError(f"No code generator registered for domain '{domain}' (Section 78: NOT_IMPLEMENTED)")


def execute_experiment_config(
    db: Session,
    config: ExperimentConfig,
    domain: str,
    spec: dict,
) -> tuple[ExperimentRun, dict | None]:
    if not config.approved:
        raise ExperimentNotApprovedError(
            f"ExperimentConfig {config.id} has not passed the human approval gate; refusing to execute."
        )

    # QUANTUM/PQC experiments run this platform's own reviewed simulator/
    # benchmark code directly in-process - not LLM-generated or otherwise
    # untrusted code - so the sandbox tier below does not apply to them
    # (see quantum_runner.py / pqc_runner.py docstrings).
    #
    # Imported lazily here (not at module load) because app.quantum.runner
    # pulls in qiskit-aer, which on some environments (verified: Windows +
    # scikit-learn in the same process) segfaults with an access violation
    # if loaded eagerly alongside the AI/cybersecurity codegen path's
    # scikit-learn import. Deferring the import means a non-quantum request
    # never loads qiskit-aer at all.
    if domain == "QUANTUM":
        from app.services.execution import quantum_runner

        run, metrics_json = quantum_runner.execute_quantum_config(db, config, spec)
        persist_run_artifacts(db, run, spec=spec)
        return run, metrics_json
    if domain == "PQC":
        from app.services.execution import pqc_runner

        run, metrics_json = pqc_runner.execute_pqc_config(db, config, spec)
        persist_run_artifacts(db, run, spec=spec)
        return run, metrics_json

    code = generate_code(domain, spec)

    run = ExperimentRun(
        experiment_id=config.experiment_id,
        config_id=config.id,
        status=RunStatus.RUNNING,
        started_at=datetime.now(timezone.utc),
        seed_used=spec.get("base_seed", 42),
    )
    db.add(run)
    db.flush()

    try:
        # caller_declares_trusted_template=True: `code` was just produced by
        # generate_code() above, which only ever calls this platform's own
        # reviewed codegen modules (ai_templates/cyber_templates) - never
        # arbitrary or LLM-authored code (see ADR-009). This flag is a no-op
        # for the Docker backend and a hard requirement for the process
        # backend.
        sandbox_result: SandboxResult = sandbox_executor.execute(
            domain=domain, code=code, caller_declares_trusted_template=True
        )
    except (SandboxUnavailableError, ProcessSandboxNotAllowedError) as exc:
        run.status = RunStatus.FAILED
        run.stderr = str(exc)
        run.finished_at = datetime.now(timezone.utc)
        db.flush()
        raise

    run.finished_at = datetime.now(timezone.utc)
    run.exit_code = sandbox_result.exit_code
    run.stdout = sandbox_result.stdout
    run.stderr = sandbox_result.stderr
    run.resource_usage = sandbox_result.resource_usage
    run.container_id = sandbox_result.container_id
    run.isolation_level = sandbox_result.isolation_level.value

    if sandbox_result.timed_out:
        run.status = RunStatus.TIMEOUT
    elif sandbox_result.exit_code == 0 and sandbox_result.metrics_json is not None:
        run.status = RunStatus.COMPLETED
    else:
        # Non-zero exit OR a zero exit that produced no parseable
        # output/metrics.json both count as FAILED - a script that exits 0
        # without emitting metrics is not a successful experiment.
        run.status = RunStatus.FAILED

    db.flush()
    persist_run_artifacts(db, run, code=code, spec=spec)
    return run, sandbox_result.metrics_json
