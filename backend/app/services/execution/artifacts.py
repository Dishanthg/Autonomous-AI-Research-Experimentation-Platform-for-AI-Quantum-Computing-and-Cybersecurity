"""Artifact persistence.

Before this module, generated code, stdout/stderr, and the codegen spec
that produced a run existed only as values on the `ExperimentRun` row (or,
for the sandbox's generated code, not persisted at all beyond the
ephemeral sandbox workspace) - not as versioned, queryable, checksummed
`Artifact` rows a caller can list per run. This module writes real files
under `research/_artifacts/<run_id>/` and records their path + sha256
checksum in the `artifacts` table.
"""

import hashlib
import json
from pathlib import Path

from app.models.experiment import Artifact, ExperimentRun

REPO_ROOT = Path(__file__).resolve().parents[4]
ARTIFACTS_DIR = REPO_ROOT / "research" / "_artifacts"


def _write_file(run_id: str, filename: str, content: str) -> tuple[str, str]:
    run_dir = ARTIFACTS_DIR / run_id
    run_dir.mkdir(parents=True, exist_ok=True)
    path = run_dir / filename
    path.write_text(content, encoding="utf-8")
    checksum = hashlib.sha256(content.encode("utf-8")).hexdigest()
    return str(path.relative_to(REPO_ROOT)).replace("\\", "/"), checksum


def persist_run_artifacts(
    db,
    run: ExperimentRun,
    code: str | None = None,
    spec: dict | None = None,
) -> list[Artifact]:
    """Writes code (if this run's domain used codegen), the codegen_spec,
    and the run's stdout/stderr log, each as a real Artifact row. Safe to
    call for both completed and failed runs - a failed run's log is real
    evidence too."""
    created: list[Artifact] = []

    if code:
        path, checksum = _write_file(run.id, "generated_code.py", code)
        created.append(Artifact(run_id=run.id, artifact_type="code", path=path, checksum=checksum))

    if spec is not None:
        path, checksum = _write_file(run.id, "codegen_spec.json", json.dumps(spec, indent=2, default=str))
        created.append(Artifact(run_id=run.id, artifact_type="config", path=path, checksum=checksum))

    log_content = f"=== stdout ===\n{run.stdout or ''}\n\n=== stderr ===\n{run.stderr or ''}\n"
    path, checksum = _write_file(run.id, "run.log", log_content)
    created.append(Artifact(run_id=run.id, artifact_type="log", path=path, checksum=checksum))

    for artifact in created:
        db.add(artifact)
    db.flush()
    return created
