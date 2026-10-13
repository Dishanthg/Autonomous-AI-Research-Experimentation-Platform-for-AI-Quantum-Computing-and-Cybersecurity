# ADR-007: Neo4j Research Knowledge Graph for Gap Detection

## Status
Accepted, implemented in code (`app/services/knowledge_graph/`);
**IMPLEMENTED - NOT VERIFIED** against a live Neo4j instance in this build
environment (see ADR-008 for why).

## Context
Section 12's gap categories (unexplored dataset, missing baseline, unexplored
combination of methods) are naturally multi-hop graph queries
(`Method<-USES-Paper-USES->Dataset`, sparse-coverage counts, cross-method
overlap checks). Modeling this relationally would mean recursive CTEs for
every query; Neo4j's Cypher expresses them directly.

## Decision
`app/services/knowledge_graph/client.py` wraps the official Neo4j driver with
a `KnowledgeGraphUnavailableError` that's raised (not swallowed) on connection
failure, matching Section 81's "fail loudly" rule.
`app/services/knowledge_graph/gap_queries.py` implements two deterministic
gap-candidate generators (`find_sparse_method_dataset_pairs`,
`find_methods_with_no_dataset_overlap`); every result is a `GapCandidate`
dataclass with `human_verification_required` implicit (the API layer sets
this `True` by default on the corresponding `ResearchGap` row per Section 12 -
no gap is ever auto-promoted).

## Consequences
- Requires operating a fourth stateful service (Postgres, and previously
  planned Docker sandbox, plus Neo4j) - justified specifically by graph
  traversal needs, not used for anything Postgres could do as well (Section Z).
- This build's disk-constrained environment could not keep a Neo4j container
  running long enough to verify the Cypher queries against real data (see
  ADR-008). The Cypher itself was reviewed for correctness but not executed.

## Verification status
IMPLEMENTED - NOT VERIFIED. This is an honest gap in this build, not a
claim of completeness - tracked in FINAL_RESEARCH_AUDIT.md.
