# ADR-003: Mandatory Human Approval Gates

## Status
Accepted, implemented (`app/api/v1/experiments.py`, `ResearchDecision` model).

## Context
The project's founding constraint (Section 7) is that the AI is an assistant,
not an autonomous authority. Two points in the pipeline are irreversible or
costly enough to require a human decision: running generated code, and
publishing a conclusion.

## Decision
Two gates are enforced in the API layer, not just documented convention:
- **Gate 1 (Plan Approval)**: `POST /experiments/configs/{id}/approve` runs
  the deterministic critic first and refuses (`409`) if there is an unresolved
  blocking objection. Only a human-authenticated request (RESEARCHER/ADMIN
  role, JWT-verified) can call this endpoint.
- **Gate 2 (Execution Approval)**: `POST /experiments/configs/{id}/execute`
  is itself the execution authorization - reachable only by the same roles,
  and `execute_experiment_config()` in the service layer independently
  re-checks `config.approved` and raises `ExperimentNotApprovedError` if Gate
  1 was skipped, so the guarantee doesn't depend on the API layer alone.

Every gate decision is written to `research_decisions` (actor, outcome,
rationale) and to `audit_logs`.

## Consequences
- No config can reach sandbox execution without two independently-checked,
  audit-logged human actions.
- This intentionally slows the pipeline down; that is the point (Section 7).

## Verification status
IMPLEMENTED - VERIFIED. `test_api_integration.py::test_full_research_pipeline_end_to_end`
exercises both gates end-to-end, including the critic-blocks-approval path
(too-small `num_runs`) and confirms execution is unreachable without a prior
approval.
