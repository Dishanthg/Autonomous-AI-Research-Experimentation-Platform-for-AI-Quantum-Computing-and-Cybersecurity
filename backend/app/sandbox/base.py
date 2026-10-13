"""Shared sandbox types (Section 19/57/O + ADR-009).

Two isolation tiers are supported, and every result is honestly labeled
with which one produced it - nothing downstream may treat a
PROCESS_RESOURCE_LIMITED result as equivalent to a DOCKER one.
"""

import enum
from dataclasses import dataclass, field
from typing import Optional


class IsolationLevel(str, enum.Enum):
    DOCKER = "DOCKER"
    """Full isolation: ephemeral container, cgroup CPU/memory limits,
    network disabled, read-only image, non-root user, dropped capabilities.
    The only tier approved for arbitrary/LLM-authored code (Rule 5-7)."""

    PROCESS_RESOURCE_LIMITED = "PROCESS_RESOURCE_LIMITED"
    """Reduced isolation: a plain OS subprocess with a wall-clock timeout,
    a restricted environment (no inherited secrets), and an ephemeral
    working directory. No network isolation guarantee and no CPU/memory
    cgroup enforcement on Windows. ONLY permitted for the platform's own
    reviewed, version-controlled codegen templates (see
    ALLOW_PROCESS_SANDBOX / ADR-009) - never for arbitrary generated code."""


class SandboxUnavailableError(RuntimeError):
    """Raised when the selected sandbox backend cannot run at all (e.g. the
    Docker daemon is unreachable). Callers must surface this and mark the
    run FAILED - never silently fall back to a lower-assurance tier."""


class SandboxTimeoutError(RuntimeError):
    pass


@dataclass
class SandboxResult:
    run_workspace_id: str
    exit_code: Optional[int]
    stdout: str
    stderr: str
    timed_out: bool
    wall_time_seconds: float
    container_id: Optional[str]
    isolation_level: IsolationLevel
    resource_usage: dict = field(default_factory=dict)
    metrics_json: Optional[dict] = None
    output_files: list = field(default_factory=list)
