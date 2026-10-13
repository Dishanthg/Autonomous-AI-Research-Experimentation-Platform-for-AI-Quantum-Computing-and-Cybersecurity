# Research Gaps

The Gap Analyzer's detection logic (`app/services/knowledge_graph/gap_queries.py`)
implements two deterministic Cypher-query-based generators:
`find_sparse_method_dataset_pairs` (candidate "unexplored combination"
gaps — Method×Dataset pairs with too few supporting papers) and
`find_methods_with_no_dataset_overlap` (candidate "missing baseline" gaps —
methods never evaluated on a common dataset). Every result carries
`human_verification_required = True` by construction; nothing is
auto-promoted to a hypothesis without a recorded human `ResearchDecision`
(Section 12's explicit requirement).

**Status: NOT VERIFIED against real data.** This build's Neo4j instance was
never successfully populated and queried in this environment (a disk-space
incident took down the local Docker daemon before the knowledge graph could
be exercised — see ADR-007, ADR-008). The Cypher was written and reviewed
for logical correctness but has not produced a single real gap-candidate
output. No fabricated example gaps are presented here in its place.
