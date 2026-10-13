"""Section 80/81 failure-mode tests + ADR-009 pluggable-backend tests.

Docker daemon unavailable must raise SandboxUnavailableError, never fall
back to unsandboxed execution. The process-tier backend (ADR-009) is
exercised for real - it runs an actual OS subprocess - since it requires no
external services and is safe to test directly.
"""

from unittest.mock import patch

import pytest
from docker.errors import DockerException

from app.sandbox import docker_executor, executor, process_executor
from app.sandbox.base import IsolationLevel
from app.sandbox.executor import ProcessSandboxNotAllowedError, SandboxUnavailableError


def test_docker_executor_raises_when_daemon_unreachable():
    with patch("app.sandbox.docker_executor.docker.from_env", side_effect=DockerException("no daemon")):
        with pytest.raises(SandboxUnavailableError):
            docker_executor.execute(domain="AI", code="print('hello')")


def test_docker_executor_rejects_unknown_domain():
    with patch("app.sandbox.docker_executor._get_client") as mock_get_client:
        mock_get_client.return_value = object()  # never reached
        with pytest.raises(ValueError):
            docker_executor.execute(domain="NOT_A_DOMAIN", code="print('hi')")


def test_facade_dispatches_to_docker_by_default(monkeypatch):
    from app.sandbox import executor as executor_module

    monkeypatch.setattr(executor_module.settings, "sandbox_backend", "docker")
    with patch("app.sandbox.docker_executor.docker.from_env", side_effect=DockerException("no daemon")):
        with pytest.raises(SandboxUnavailableError):
            executor.execute(domain="AI", code="print('hi')")


def test_facade_rejects_unknown_backend(monkeypatch):
    from app.sandbox import executor as executor_module

    monkeypatch.setattr(executor_module.settings, "sandbox_backend", "not_a_real_backend")
    with pytest.raises(ValueError):
        executor.execute(domain="AI", code="print('hi')")


def test_process_executor_refuses_when_disabled(monkeypatch):
    monkeypatch.setattr(process_executor.settings, "allow_process_sandbox", True)
    with pytest.raises(ProcessSandboxNotAllowedError):
        process_executor.execute(domain="AI", code="print('hi')", caller_declares_trusted_template=False)
    monkeypatch.setattr(process_executor.settings, "allow_process_sandbox", False)
    with pytest.raises(ProcessSandboxNotAllowedError):
        process_executor.execute(domain="AI", code="print('hi')", caller_declares_trusted_template=True)


def test_process_executor_runs_real_subprocess_and_captures_metrics(monkeypatch):
    """This is a REAL subprocess execution (no mocking) - it genuinely
    verifies the process-tier sandbox end to end: code is written to an
    ephemeral workspace, run with python, and output/metrics.json is read
    back before the workspace is deleted."""
    monkeypatch.setattr(process_executor.settings, "allow_process_sandbox", True)

    code = (
        "import json, os\n"
        "os.makedirs('output', exist_ok=True)\n"
        "with open('output/metrics.json', 'w') as f:\n"
        "    json.dump({'ok': True, 'value': 42}, f)\n"
        "print('DONE')\n"
    )
    result = process_executor.execute(domain="AI", code=code, caller_declares_trusted_template=True)

    assert result.exit_code == 0
    assert "DONE" in result.stdout
    assert result.metrics_json == {"ok": True, "value": 42}
    assert result.isolation_level == IsolationLevel.PROCESS_RESOURCE_LIMITED
    assert result.timed_out is False


def test_process_executor_enforces_timeout(monkeypatch):
    monkeypatch.setattr(process_executor.settings, "allow_process_sandbox", True)
    code = "import time\ntime.sleep(30)\n"
    result = process_executor.execute(
        domain="AI", code=code, caller_declares_trusted_template=True, timeout_seconds=1
    )
    assert result.timed_out is True


def test_process_executor_captures_nonzero_exit_and_stderr(monkeypatch):
    monkeypatch.setattr(process_executor.settings, "allow_process_sandbox", True)
    code = "raise ValueError('boom')\n"
    result = process_executor.execute(domain="AI", code=code, caller_declares_trusted_template=True)
    assert result.exit_code != 0
    assert "boom" in result.stderr
    assert result.metrics_json is None


def test_process_executor_env_does_not_leak_host_secrets(monkeypatch):
    """The restricted environment must not pass through arbitrary host
    variables (e.g. a secret accidentally set in the parent shell)."""
    monkeypatch.setattr(process_executor.settings, "allow_process_sandbox", True)
    monkeypatch.setenv("RMQ_TEST_SECRET_SHOULD_NOT_LEAK", "super-secret-value")

    code = (
        "import json, os\n"
        "os.makedirs('output', exist_ok=True)\n"
        "with open('output/metrics.json', 'w') as f:\n"
        "    json.dump({'saw_secret': 'RMQ_TEST_SECRET_SHOULD_NOT_LEAK' in os.environ}, f)\n"
    )
    result = process_executor.execute(domain="AI", code=code, caller_declares_trusted_template=True)
    assert result.metrics_json == {"saw_secret": False}
