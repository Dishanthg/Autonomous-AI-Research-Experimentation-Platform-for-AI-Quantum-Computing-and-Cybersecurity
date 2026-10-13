"""Deterministic gap-candidate detection over the knowledge graph
(Section 12/L). These are candidate generators only - every result is
returned with human_verification_required=True and must go through an
LLM narrative-framing pass (see app.services.gap.narrative) and then a
recorded human ResearchDecision before it can back a hypothesis.
"""

from dataclasses import dataclass

from app.services.knowledge_graph.client import KnowledgeGraphClient


@dataclass
class GapCandidate:
    category: str
    description: str
    evidence: dict


def find_sparse_method_dataset_pairs(client: KnowledgeGraphClient, min_papers: int = 1) -> list[GapCandidate]:
    """Method x Dataset combinations covered by fewer than `min_papers`
    papers in the current literature collection - a candidate
    'unexplored dataset' / 'unexplored combination of methods' gap."""
    query = """
        MATCH (m:Method)<-[:USES]-(p:Paper)-[:USES]->(d:Dataset)
        WITH m, d, count(DISTINCT p) AS paper_count
        WHERE paper_count <= $min_papers
        RETURN m.name AS method, d.name AS dataset, paper_count
        ORDER BY paper_count ASC
        LIMIT 20
    """
    with client.session() as session:
        rows = session.run(query, min_papers=min_papers)
        return [
            GapCandidate(
                category="unexplored_combination_of_methods",
                description=f"Method '{r['method']}' has only {r['paper_count']} paper(s) "
                f"evaluating it on dataset '{r['dataset']}'.",
                evidence={"method": r["method"], "dataset": r["dataset"], "paper_count": r["paper_count"]},
            )
            for r in rows
        ]


def find_methods_with_no_dataset_overlap(client: KnowledgeGraphClient) -> list[GapCandidate]:
    """Methods that have never been evaluated on any dataset another
    (otherwise similar) method has been evaluated on - candidate 'missing
    baseline' gaps."""
    query = """
        MATCH (m1:Method), (m2:Method)
        WHERE m1.name < m2.name
        OPTIONAL MATCH (m1)<-[:USES]-(:Paper)-[:USES]->(d:Dataset)<-[:USES]-(:Paper)-[:USES]->(m2)
        WITH m1, m2, count(DISTINCT d) AS shared_datasets
        WHERE shared_datasets = 0
        RETURN m1.name AS method_a, m2.name AS method_b
        LIMIT 20
    """
    with client.session() as session:
        rows = session.run(query)
        return [
            GapCandidate(
                category="missing_baseline",
                description=f"'{r['method_a']}' and '{r['method_b']}' have never been "
                f"evaluated on a common dataset in this literature collection.",
                evidence={"method_a": r["method_a"], "method_b": r["method_b"]},
            )
            for r in rows
        ]
