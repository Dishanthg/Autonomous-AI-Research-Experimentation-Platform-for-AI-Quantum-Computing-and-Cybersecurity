# ADR-004: Docker Sandbox for All Generated Code Execution

## Status
Accepted, implemented (`app/sandbox/docker_executor.py` - see ADR-009 for
the subsequent split into a pluggable Docker/process backend facade);
**integration-unverified in this build environment** (see below).

## Context
Generated experiment code must never run with the researcher's privileges,
network access, or filesystem visibility (Rule 5-7).

## Decision
`app/sandbox/docker_executor.py` runs one ephemeral Docker container per execution:
CPU/memory limits via the Docker SDK, `network_mode="none"` by default, a
read-only image with a single writable bind-mounted workspace, dropped Linux
capabilities, non-root user, and a host-side watchdog thread that kills the
container on timeout (never trusting the script to self-limit). Output
artifacts (`output/metrics.json`) are read from the host-side bind mount
*before* the workspace is torn down, so results survive container removal.
If the Docker daemon is unreachable, `execute()` raises
`SandboxUnavailableError` - there is no fallback to unsandboxed execution
(verified in `test_sandbox_executor.py` and live in the API integration test,
where the execute-gate call returns `503` rather than silently running code
on the host).

## Consequences
- Package installation is fixed per domain image
  (`sandbox/images/{ai,cyber,quantum}-image/Dockerfile`) and requires a
  reviewed image rebuild to change - generated code cannot `pip install`
  arbitrary packages at run time.
- A genuine limitation, not swept under the rug: this development machine's
  system drive filled up during the build (0 free space on `C:`), which made
  the local Docker Desktop daemon unusable partway through. Rather than
  disable the sandbox's security model to "make it work," the platform was
  changed to run entirely on local SQLite for dev/test (ADR-008), and the
  Docker-backed sandbox is documented as **IMPLEMENTED - NOT VERIFIED**
  end-to-end (a real container was never successfully executed against these
  templates in this environment, though the failure-mode path - daemon
  unreachable → clean `SandboxUnavailableError` → `503` to the caller - was
  verified).

## Verification status
IMPLEMENTED - NOT VERIFIED (happy path). IMPLEMENTED - VERIFIED (failure path:
Docker unavailable is handled correctly, never falls back to unsandboxed
execution). The codegen templates themselves (`ai_templates.py`,
`cyber_templates.py`) were verified by executing the generated Python
directly via `subprocess` (not inside Docker) in `test_codegen.py`, confirming
the *logic* is correct even though the *sandbox* integration is not yet
confirmed on this machine.
