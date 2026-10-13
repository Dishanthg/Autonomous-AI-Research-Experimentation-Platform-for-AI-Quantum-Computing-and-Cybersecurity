"""Sandbox facade (ADR-009). Selects a backend by `SANDBOX_BACKEND`
("docker" | "process") and dispatches to it. Existing callers importing
`execute`, `SandboxUnavailableError`, etc. from this module keep working
unchanged; `app.sandbox.docker_executor._get_client` is re-exported for the
health check.
"""

from typing import Optional

from app.core.config import get_settings
from app.sandbox import docker_executor, process_executor
from app.sandbox.base import (
    IsolationLevel,
    SandboxResult,
    SandboxTimeoutError,
    SandboxUnavailableError,
)
from app.sandbox.docker_executor import _get_client  # re-exported for health checks
from app.sandbox.process_executor import ProcessSandboxNotAllowedError

settings = get_settings()

__all__ = [
    "execute",
    "SandboxResult",
    "IsolationLevel",
    "SandboxUnavailableError",
    "SandboxTimeoutError",
    "ProcessSandboxNotAllowedError",
    "_get_client",
]


def execute(
    domain: str,
    code: str,
    entrypoint_filename: str = "experiment.py",
    timeout_seconds: Optional[int] = None,
    input_files: Optional[dict] = None,
    caller_declares_trusted_template: bool = False,
    **backend_kwargs,
) -> SandboxResult:
    backend = settings.sandbox_backend
    if backend == "docker":
        return docker_executor.execute(
            domain,
            code,
            entrypoint_filename=entrypoint_filename,
            timeout_seconds=timeout_seconds,
            input_files=input_files,
            **backend_kwargs,
        )
    if backend == "process":
        return process_executor.execute(
            domain,
            code,
            entrypoint_filename=entrypoint_filename,
            timeout_seconds=timeout_seconds,
            input_files=input_files,
            caller_declares_trusted_template=caller_declares_trusted_template,
        )
    raise ValueError(f"Unknown SANDBOX_BACKEND '{backend}' - expected 'docker' or 'process'")
