# ADR-009: Pluggable Sandbox Backends (Docker Tier 1 / Process Tier 2)

## Status
Accepted, implemented (`app/sandbox/base.py`, `docker_executor.py`,
`process_executor.py`, `executor.py`).

## Context
ADR-004 committed the platform to Docker-only sandboxing. In practice, this
build's development machine lost Docker Desktop mid-session to a disk-space
incident (ADR-008), which meant every "run a real experiment" path was stuck
at `SandboxUnavailableError` — correct behavior, but it meant the platform
could never actually produce a real, sandboxed experimental result in this
environment, only prove that it refuses to fake one.

The alternative of "just run the generated code directly, no sandbox" was
rejected outright — that is precisely Rule 5. But an intermediate option
exists that many real MLOps platforms use for constrained/CI environments: a
second, explicitly lower-assurance isolation tier, used only for code the
platform itself wrote and reviewed (never for arbitrary or LLM-authored
code), with its own honesty guarantees.

## Decision
Introduce `IsolationLevel` (`DOCKER` | `PROCESS_RESOURCE_LIMITED`) and split
the sandbox into:
- `docker_executor.py` — the original Tier 1 implementation, unchanged in
  behavior, now labeled `IsolationLevel.DOCKER`.
- `process_executor.py` — a new Tier 2: a plain OS subprocess with a
  wall-clock timeout (process killed on expiry), a restricted environment
  (no inherited secrets - only `PATH`/`SYSTEMROOT`/etc.), an ephemeral
  per-run working directory, and (POSIX only) a best-effort
  `resource.setrlimit` on address space and CPU time. It has **no network
  isolation guarantee** and **no cross-platform CPU/memory cgroup
  enforcement** and is gated by two independent conditions that must both
  hold: `ALLOW_PROCESS_SANDBOX=true` (an operator-set config flag, default
  `false`) AND a `caller_declares_trusted_template=True` argument that only
  `services/execution/orchestrator.py` sets, and only because the code it
  passes in was just produced by `generate_code()` calling this platform's
  own reviewed `ai_templates`/`cyber_templates` modules — never arbitrary or
  LLM-authored code.
- `executor.py` is now a thin facade selecting a backend via
  `SANDBOX_BACKEND` (`"docker"` default, `"process"` opt-in).
- Every `ExperimentRun` row stores which `isolation_level` produced it
  (new column, migration `b21effd75a5e`), and nothing in the API/frontend
  renders a result without this label - a Tier 2 result can never be
  mistaken for a Tier 1 one.

## Consequences
- This build's local dev environment (`backend/.env`: `SANDBOX_BACKEND=process`,
  `ALLOW_PROCESS_SANDBOX=true`) can now run the platform's own AI and
  cybersecurity codegen templates to completion and produce real,
  statistically-analyzed conclusions — see `research/` for the actual
  outputs and `docs/masters-application/13_results.md` for the updated
  results table.
- Production deployments keep `SANDBOX_BACKEND=docker` (the `.env.example`
  default) and never set `ALLOW_PROCESS_SANDBOX=true`; nothing about this
  ADR weakens the Docker path or lets arbitrary code reach Tier 2.
- A malicious actor with API access to trigger the *specific, reviewed*
  codegen templates run under Tier 2 could still exhaust local CPU/memory
  on Windows (no rlimit there) - acceptable for a local single-operator dev
  environment, unacceptable for a shared or production deployment, which is
  exactly why the flag defaults off and is documented as such everywhere it
  appears.

## Verification status
IMPLEMENTED — VERIFIED. `test_sandbox_executor.py` includes a real
(unmocked) subprocess execution test, a timeout-enforcement test, a
nonzero-exit/stderr-capture test, and a test proving the restricted
environment does not leak an arbitrary host environment variable into the
child process. The Docker Tier 1 path remains IMPLEMENTED — NOT VERIFIED
end-to-end in this environment (its failure-mode behavior is verified).
