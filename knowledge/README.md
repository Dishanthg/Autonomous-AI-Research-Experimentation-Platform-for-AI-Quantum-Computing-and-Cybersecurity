# Knowledge

This directory documents the Research Knowledge Graph's schema
(`ontology.yaml`) as data, separate from the Neo4j driver code in
`backend/app/services/knowledge_graph/`. It exists so the graph's shape is
reviewable without reading Cypher, and so `schema.py`'s constraints can be
checked against a single source of truth.

**Status:** documented and implemented in code
(`backend/app/services/knowledge_graph/schema.py`); not yet verified
against a live Neo4j instance in this build (ADR-007/ADR-008).
