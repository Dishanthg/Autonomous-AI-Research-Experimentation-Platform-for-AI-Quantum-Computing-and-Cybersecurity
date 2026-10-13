# Architecture Decisions

See `docs/architecture/adr/` for the full records. Summary:

- ADR-001: every claim is tagged with a provenance type; ungrounded spans
  are rejected, not trusted.
- ADR-002: research memory is bounded, explicit SQL queries with an
  `enabled` flag, not free vector recall — designed specifically to make the
  memory ablation experiment clean.
- ADR-003: two independently-checked, audit-logged human approval gates
  stand between a hypothesis and code execution.
- ADR-004: all generated code runs only inside a resource-limited,
  network-disabled Docker container; unreachable sandbox fails loudly
  (verified), the happy path is not yet verified in this environment.
- ADR-005: the critic's structural checklist runs with zero LLM involvement
  and cannot be argued out of a blocking objection.
- ADR-006: statistics and the conclusion classification are computed by
  `scipy`/`numpy` alone; no LLM call exists in that code path.
- ADR-007: Neo4j is used specifically for its multi-hop graph-query fit to
  gap detection, not used elsewhere Postgres would do as well; unverified in
  this environment.
- ADR-008: local development runs entirely on SQLite (UUIDs as plain
  strings, not Postgres-native types) so the platform never requires Docker
  to develop or test — adopted mid-build in direct response to a disk-space
  incident on the build machine.
- ADR-009: the sandbox is now pluggable (Docker Tier 1 / process Tier 2).
  Tier 2 is gated behind an explicit config flag AND a
  `caller_declares_trusted_template` argument only the orchestrator sets,
  and only for this platform's own reviewed codegen output - never for
  arbitrary or LLM-authored code. This is the change that let the full
  pipeline actually execute and produce real results in this
  Docker-unavailable environment, rather than only proving it fails safely.
  Verified: real subprocess execution, timeout enforcement, and a test
  proving the restricted environment does not leak host secrets into the
  child process.
