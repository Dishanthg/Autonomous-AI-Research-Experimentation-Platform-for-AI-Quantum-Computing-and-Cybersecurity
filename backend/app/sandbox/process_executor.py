"""OS-process sandbox executor - Tier 2 (IsolationLevel.PROCESS_RESOURCE_LIMITED).

See ADR-009. This tier exists for constrained development environments
where a Docker daemon is unavailable (this project hit exactly that
situation - a disk-space incident on the build machine, see ADR-008).

SECURITY BOUNDARY (do not weaken without re-reading this):
  - This executor provides NO network isolation guarantee on Windows and NO
    cgroup-style CPU/memory enforcement cross-platform (best-effort
    `resource.setrlimit` is applied on POSIX only).
  - It is gated behind `ALLOW_PROCESS_SANDBOX` (default False) and is
    intended ONLY for this platform's own reviewed, version-controlled
    codegen templates (`app.services.codegen.*`), never for arbitrary or
    LLM-authored code. `execute()` takes a `caller_declares_trusted_template`
    flag that must be explicitly set True by callers that are running a
    known template; the orchestrator is the only production call site and
    always sets it based on which codegen module produced the code.
  - Every run using this tier is written to the audit log with its
    isolation level so no result can silently be presented as if it came
    from the fully-isolated Docker tier (Result rows carry this through
    ExperimentRun.sandbox_backend).

What IS enforced here: a wall-clock timeout (subprocess killed on expiry),
an ephemeral per-run working directory (removed after execution), a
restricted environment (no inherited secrets/credentials - only PATH and
the minimum variables Python itself needs to start), and (POSIX only) a
best-effort address-space / CPU-time rlimit.
"""

import json
import os
import platform
import shutil
import subprocess
import sys
import tempfile
import time
import uuid
from pathlib import Path
from typing import Optional

from app.core.config import get_settings
from app.sandbox.base import IsolationLevel, SandboxResult

settings = get_settings()


class ProcessSandboxNotAllowedError(RuntimeError):
    pass


def _restricted_env() -> dict:
    """Deliberately minimal - no inherited API keys, DB URLs, or JWT
    secrets. Only what the Python interpreter itself needs to start."""
    env = {
        "PYTHONDONTWRITEBYTECODE": "1",
        "PYTHONIOENCODING": "utf-8",
    }
    for key in ("PATH", "SYSTEMROOT", "SYSTEMDRIVE", "TEMP", "TMP", "HOME"):
        if key in os.environ:
            env[key] = os.environ[key]
    return env


def _posix_preexec_fn(memory_limit_bytes: int, cpu_time_seconds: int):
    def _limit():
        import resource

        try:
            resource.setrlimit(resource.RLIMIT_AS, (memory_limit_bytes, memory_limit_bytes))
        except (ValueError, OSError):
            pass
        try:
            resource.setrlimit(resource.RLIMIT_CPU, (cpu_time_seconds, cpu_time_seconds))
        except (ValueError, OSError):
            pass

    return _limit


def execute(
    domain: str,
    code: str,
    entrypoint_filename: str = "experiment.py",
    timeout_seconds: Optional[int] = None,
    input_files: Optional[dict[str, bytes]] = None,
    caller_declares_trusted_template: bool = False,
) -> SandboxResult:
    if not settings.allow_process_sandbox:
        raise ProcessSandboxNotAllowedError(
            "Process-tier sandbox is disabled (ALLOW_PROCESS_SANDBOX=false). "
            "Set it only in constrained dev environments, for trusted, "
            "reviewed codegen templates - see ADR-009."
        )
    if not caller_declares_trusted_template:
        raise ProcessSandboxNotAllowedError(
            "Refusing to run: caller did not declare this code as a trusted, "
            "version-controlled template. The process-tier sandbox must "
            "never run arbitrary or LLM-authored code (see ADR-009)."
        )

    timeout_seconds = timeout_seconds or settings.sandbox_timeout_seconds
    memory_limit_bytes = 1024 * 1024 * 1024  # 1GiB, matches SANDBOX_MEMORY_LIMIT default
    run_id = str(uuid.uuid4())
    workspace = Path(tempfile.mkdtemp(prefix=f"rmq-proc-{run_id}-"))
    output_dir = workspace / "output"
    output_dir.mkdir()

    try:
        (workspace / entrypoint_filename).write_text(code, encoding="utf-8")
        for rel_path, content in (input_files or {}).items():
            target = workspace / rel_path
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(content)

        kwargs = {}
        if platform.system() != "Windows":
            kwargs["preexec_fn"] = _posix_preexec_fn(memory_limit_bytes, timeout_seconds)

        start = time.time()
        timed_out = False
        stdout, stderr, exit_code = "", "", None
        try:
            proc = subprocess.run(
                [sys.executable, entrypoint_filename],
                cwd=str(workspace),
                capture_output=True,
                text=True,
                timeout=timeout_seconds,
                env=_restricted_env(),
                **kwargs,
            )
            exit_code = proc.returncode
            stdout, stderr = proc.stdout, proc.stderr
        except subprocess.TimeoutExpired as exc:
            timed_out = True

            def _decode(x):
                return x.decode("utf-8", errors="replace") if isinstance(x, bytes) else (x or "")

            stdout = _decode(exc.stdout)
            stderr = _decode(exc.stderr) + "\n[killed: wall-clock timeout exceeded]"
        wall_time = time.time() - start

        metrics_json = None
        metrics_path = output_dir / "metrics.json"
        if metrics_path.exists():
            try:
                metrics_json = json.loads(metrics_path.read_text(encoding="utf-8"))
            except (json.JSONDecodeError, OSError):
                metrics_json = None
        output_files = [str(p.relative_to(output_dir)) for p in output_dir.rglob("*") if p.is_file()]

        return SandboxResult(
            run_workspace_id=run_id,
            exit_code=exit_code,
            stdout=stdout,
            stderr=stderr,
            timed_out=timed_out,
            wall_time_seconds=wall_time,
            container_id=None,
            isolation_level=IsolationLevel.PROCESS_RESOURCE_LIMITED,
            resource_usage={
                "platform": platform.system(),
                "rlimit_enforced": platform.system() != "Windows",
                "note": (
                    "no cgroup-level CPU/memory enforcement on this platform"
                    if platform.system() == "Windows"
                    else "POSIX rlimit applied (best-effort)"
                ),
            },
            metrics_json=metrics_json,
            output_files=output_files,
        )
    finally:
        shutil.rmtree(workspace, ignore_errors=True)
