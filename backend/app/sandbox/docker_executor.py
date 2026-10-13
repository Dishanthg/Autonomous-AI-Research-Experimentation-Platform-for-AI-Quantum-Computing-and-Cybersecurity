"""Docker-backed sandbox executor - Tier 1 (IsolationLevel.DOCKER).

See ADR-004 and ADR-009. This is the only tier approved for arbitrary or
LLM-authored code. Requires a running Docker daemon; raises
SandboxUnavailableError rather than falling back to a lower-assurance tier
if one is not reachable (Rule 5).
"""

import json
import shutil
import tempfile
import threading
import time
import uuid
from pathlib import Path
from typing import Optional

import docker
from docker.errors import DockerException, NotFound

from app.core.config import get_settings
from app.sandbox.base import IsolationLevel, SandboxResult, SandboxUnavailableError

settings = get_settings()

DOMAIN_IMAGES = {
    "AI": "researchmind-q/ai-image:latest",
    "CYBERSECURITY": "researchmind-q/cyber-image:latest",
    "QUANTUM": "researchmind-q/quantum-image:latest",
    "PQC": "researchmind-q/cyber-image:latest",
}


def _get_client() -> docker.DockerClient:
    try:
        client = docker.from_env()
        client.ping()
        return client
    except DockerException as exc:
        raise SandboxUnavailableError(f"Docker daemon unreachable: {exc}") from exc


def execute(
    domain: str,
    code: str,
    entrypoint_filename: str = "experiment.py",
    timeout_seconds: Optional[int] = None,
    cpu_limit: Optional[float] = None,
    memory_limit: Optional[str] = None,
    network_mode: Optional[str] = None,
    input_files: Optional[dict[str, bytes]] = None,
) -> SandboxResult:
    if not settings.sandbox_enabled:
        raise SandboxUnavailableError("Sandbox execution is disabled (SANDBOX_ENABLED=false).")

    image = DOMAIN_IMAGES.get(domain)
    if image is None:
        raise ValueError(f"No sandbox image configured for domain '{domain}'")

    timeout_seconds = timeout_seconds or settings.sandbox_timeout_seconds
    cpu_limit = cpu_limit or settings.sandbox_cpu_limit
    memory_limit = memory_limit or settings.sandbox_memory_limit
    network_mode = network_mode or settings.sandbox_network_mode

    client = _get_client()
    run_id = str(uuid.uuid4())
    workspace = Path(tempfile.mkdtemp(prefix=f"rmq-run-{run_id}-"))
    output_dir = workspace / "output"
    output_dir.mkdir()

    try:
        (workspace / entrypoint_filename).write_text(code, encoding="utf-8")
        for rel_path, content in (input_files or {}).items():
            target = workspace / rel_path
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(content)

        container = client.containers.run(
            image=image,
            command=["python", f"/workspace/{entrypoint_filename}"],
            working_dir="/workspace",
            volumes={str(workspace): {"bind": "/workspace", "mode": "rw"}},
            network_mode=network_mode,
            mem_limit=memory_limit,
            nano_cpus=int(cpu_limit * 1_000_000_000),
            pids_limit=128,
            read_only=False,
            security_opt=["no-new-privileges"],
            cap_drop=["ALL"],
            user="1000:1000",
            detach=True,
        )

        result_box: dict = {}
        timed_out_flag = {"value": False}

        def _waiter():
            try:
                result_box["exit_code"] = container.wait(timeout=timeout_seconds)["StatusCode"]
            except Exception:
                result_box["exit_code"] = None

        waiter_thread = threading.Thread(target=_waiter, daemon=True)
        start = time.time()
        waiter_thread.start()
        waiter_thread.join(timeout_seconds)

        if waiter_thread.is_alive():
            timed_out_flag["value"] = True
            try:
                container.kill()
            except (DockerException, NotFound):
                pass
            waiter_thread.join(5)

        wall_time = time.time() - start

        try:
            logs = container.logs(stdout=True, stderr=False).decode("utf-8", errors="replace")
            errs = container.logs(stdout=False, stderr=True).decode("utf-8", errors="replace")
        except (DockerException, NotFound):
            logs, errs = "", ""

        try:
            stats = container.stats(stream=False)
            resource_usage = {
                "memory_usage_bytes": stats.get("memory_stats", {}).get("usage"),
                "cpu_stats": stats.get("cpu_stats"),
            }
        except (DockerException, NotFound):
            resource_usage = {}

        container_id = container.id

        try:
            container.remove(force=True)
        except (DockerException, NotFound):
            pass

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
            exit_code=result_box.get("exit_code"),
            stdout=logs,
            stderr=errs,
            timed_out=timed_out_flag["value"],
            wall_time_seconds=wall_time,
            container_id=container_id,
            isolation_level=IsolationLevel.DOCKER,
            resource_usage=resource_usage,
            metrics_json=metrics_json,
            output_files=output_files,
        )
    finally:
        shutil.rmtree(workspace, ignore_errors=True)
