# ADR-002: Structured Research Memory Instead of Free-Recall

## Status
Accepted, implemented (`app/services/memory/queries.py`).

## Context
A vector-similarity "remember everything" store lets an agent free-associate
over the whole project history, which is exactly the kind of unconstrained
context that produces inconsistent plans and duplicate experiments. Section
35's Memory Ablation needs a mechanism where "no memory" and "memory" differ
in only one variable.

## Decision
Research Memory is a set of explicit, bounded SQL queries
(`get_prior_experiments`, `get_failed_experiments`, `get_unresolved_hypotheses`,
`find_duplicate_experiment`), each accepting an `enabled: bool` flag. Agents
call these functions directly; they do not receive an open-ended dump of
project history. The ablation study reuses the exact same code path with
`enabled=False` to produce the "no memory" condition, guaranteeing the two
conditions differ only in the presence/absence of memory context, not in
prompt structure or agent code.

## Consequences
- Memory queries are cheap, deterministic, and testable with ordinary SQL
  fixtures - no vector DB dependency for this feature.
- The trade-off: memory is only as good as the explicit queries written: an
  agent cannot discover a relevant precedent no query anticipates. Documented
  as a limitation (see FINAL_RESEARCH_AUDIT.md).

## Verification status
IMPLEMENTED - NOT VERIFIED end-to-end against a populated project (unit-level
query logic is straightforward SQLAlchemy and was exercised indirectly via the
API integration test, but a dedicated memory-ablation experiment run - Section
62 - has not yet been executed).
