# Threat Model (Section AA)

## Assets to protect
- Dataset/API credentials (arXiv needs none; a future Semantic Scholar key,
  DB credentials, JWT signing secret, `ANTHROPIC_API_KEY`).
- The research database (source of truth for every claim's provenance).
- Researcher accounts (RBAC-scoped: ADMIN / RESEARCHER / VIEWER).
- The host running the sandbox (Docker Tier 1) or the local process (Tier 2).

## Threat actors
1. **The LLM itself.** Treated as untrusted output, never as a trusted
   component (Section 88). Every LLM call is logged with a prompt hash;
   no LLM call ever receives a secret, a DB credential, or unmediated tool
   access to the filesystem/network.
2. **Malicious content inside retrieved literature.** A paper abstract is
   untrusted text that could contain a prompt-injection payload
   ("ignore previous instructions..."). Mitigated by the delimiter +
   explicit system-prompt framing in `services/literature/claim_extraction.py`
   (see `docs/architecture/adr` and Section AB below) - the claim-extraction
   call additionally has zero tool access, so even a successful injection
   has nothing to invoke.
3. **Generated experiment code.** Could attempt resource exhaustion,
   filesystem escape, or (if ever given one) credential exfiltration.
   Mitigated by the Docker Tier 1 sandbox (network disabled, cgroup limits,
   non-root, dropped capabilities) for any code not from this platform's own
   reviewed templates, and by the Tier 2 process sandbox's restricted
   environment + timeout + rlimit for the platform's own templates only
   (ADR-009) - gated by `ALLOW_PROCESS_SANDBOX`, off by default.
4. **A compromised or careless researcher account.** RBAC limits blast
   radius (a VIEWER cannot create projects, execute experiments, or read
   the audit log - verified in `test_rbac_viewer_cannot_create_project`).
   Every mutating action is audit-logged with actor + before/after state,
   so a compromised account's actions are forensically visible even though
   RBAC doesn't prevent all misuse by a legitimately-authenticated user.
5. **A malicious commenter/contributor to a shared knowledge graph.** Not
   currently a real threat surface (the knowledge graph has no
   externally-writable ingestion path in this build), but tracked here for
   completeness if literature crowd-sourcing is ever added.

## Prompt-injection defense (Section AB) in this build
`services/literature/claim_extraction.py` wraps untrusted document text in
an explicit `<<<UNTRUSTED_PAPER_CONTENT_START/END>>>` delimiter, instructs
the model (system prompt) that content inside is DATA never INSTRUCTIONS,
and additionally enforces a provenance guard: any extracted claim whose
`source_span` doesn't literally appear in the original abstract is dropped
before it ever reaches the database (`test_extract_claims_rejects_ungrounded_span`).

## Sandbox security (Section 57) in this build
See ADR-004 and ADR-009 for the full two-tier design. Summary: Docker Tier 1
is required for anything not from this platform's own reviewed codegen
templates; Tier 2 (process-level, reduced isolation) exists only for this
platform's own templates in Docker-unavailable dev environments, is off by
default, and never leaks host environment variables into the child process
(verified in `test_process_executor_env_does_not_leak_host_secrets`).

## What this build does NOT yet cover (honest gaps)
- No rate limiting is implemented on the API (Section 56/87 calls for it).
- No dependency vulnerability scanning is wired into CI yet.
- Secrets management is `.env`-file based (fine for local dev; a production
  deployment should use a real secrets manager, not committed here).
- No penetration test or external security review has been performed on
  this codebase.
