"""Node/edge write helpers for the Research Knowledge Graph (Section 11/K).
Idempotent MERGE-based writes keyed by the Postgres UUID of the source row,
so the graph and the relational DB never drift into inconsistent IDs."""

from app.services.knowledge_graph.client import KnowledgeGraphClient

CONSTRAINTS = [
    "CREATE CONSTRAINT paper_id IF NOT EXISTS FOR (p:Paper) REQUIRE p.id IS UNIQUE",
    "CREATE CONSTRAINT method_id IF NOT EXISTS FOR (m:Method) REQUIRE m.id IS UNIQUE",
    "CREATE CONSTRAINT dataset_id IF NOT EXISTS FOR (d:Dataset) REQUIRE d.id IS UNIQUE",
    "CREATE CONSTRAINT rq_id IF NOT EXISTS FOR (q:ResearchQuestion) REQUIRE q.id IS UNIQUE",
    "CREATE CONSTRAINT hyp_id IF NOT EXISTS FOR (h:Hypothesis) REQUIRE h.id IS UNIQUE",
    "CREATE CONSTRAINT exp_id IF NOT EXISTS FOR (e:Experiment) REQUIRE e.id IS UNIQUE",
    "CREATE CONSTRAINT gap_id IF NOT EXISTS FOR (g:ResearchGap) REQUIRE g.id IS UNIQUE",
]


def apply_constraints(client: KnowledgeGraphClient) -> None:
    with client.session() as session:
        for stmt in CONSTRAINTS:
            session.run(stmt)


def upsert_paper(client: KnowledgeGraphClient, paper_id: str, title: str, year: int | None) -> None:
    with client.session() as session:
        session.run(
            "MERGE (p:Paper {id: $id}) SET p.title = $title, p.year = $year",
            id=paper_id,
            title=title,
            year=year,
        )


def link_paper_uses_method(client: KnowledgeGraphClient, paper_id: str, method_name: str) -> None:
    with client.session() as session:
        session.run(
            """
            MERGE (p:Paper {id: $paper_id})
            MERGE (m:Method {name: $method_name})
            MERGE (p)-[:USES]->(m)
            """,
            paper_id=paper_id,
            method_name=method_name,
        )


def link_paper_uses_dataset(client: KnowledgeGraphClient, paper_id: str, dataset_name: str) -> None:
    with client.session() as session:
        session.run(
            """
            MERGE (p:Paper {id: $paper_id})
            MERGE (d:Dataset {name: $dataset_name})
            MERGE (p)-[:USES]->(d)
            """,
            paper_id=paper_id,
            dataset_name=dataset_name,
        )


def link_experiment_tests_hypothesis(
    client: KnowledgeGraphClient, experiment_id: str, hypothesis_id: str
) -> None:
    with client.session() as session:
        session.run(
            """
            MERGE (e:Experiment {id: $experiment_id})
            MERGE (h:Hypothesis {id: $hypothesis_id})
            MERGE (e)-[:TESTS]->(h)
            """,
            experiment_id=experiment_id,
            hypothesis_id=hypothesis_id,
        )


def link_hypothesis_addresses_gap(client: KnowledgeGraphClient, hypothesis_id: str, gap_id: str) -> None:
    with client.session() as session:
        session.run(
            """
            MERGE (h:Hypothesis {id: $hypothesis_id})
            MERGE (g:ResearchGap {id: $gap_id})
            MERGE (h)-[:ADDRESSES]->(g)
            """,
            hypothesis_id=hypothesis_id,
            gap_id=gap_id,
        )


def link_paper_evaluates_algorithm(client: KnowledgeGraphClient, paper_id: str, algorithm_name: str) -> None:
    """Section 11: paper -[:EVALUATES]-> algorithm."""
    with client.session() as session:
        session.run(
            """
            MERGE (p:Paper {id: $paper_id})
            MERGE (a:Algorithm {name: $algorithm_name})
            MERGE (p)-[:EVALUATES]->(a)
            """,
            paper_id=paper_id,
            algorithm_name=algorithm_name,
        )


def link_paper_reports_result(
    client: KnowledgeGraphClient, paper_id: str, result_id: str, metric_name: str, value: float | None = None
) -> None:
    """Section 11: paper -[:REPORTS]-> result. `result_id` mirrors the
    Postgres `results.id` so the two stores never drift into inconsistent
    IDs (same convention as every other link in this module)."""
    with client.session() as session:
        session.run(
            """
            MERGE (p:Paper {id: $paper_id})
            MERGE (r:Result {id: $result_id})
            SET r.metric_name = $metric_name, r.value = $value
            MERGE (p)-[:REPORTS]->(r)
            """,
            paper_id=paper_id,
            result_id=result_id,
            metric_name=metric_name,
            value=value,
        )


def link_paper_identifies_limitation(
    client: KnowledgeGraphClient, paper_id: str, limitation_description: str
) -> None:
    """Section 11: paper -[:IDENTIFIES]-> limitation. Limitation nodes are
    keyed by description text (no separate Postgres table backs a
    literature-reported limitation the way `limitations` does for an
    experiment run), so MERGE naturally dedupes identical text."""
    with client.session() as session:
        session.run(
            """
            MERGE (p:Paper {id: $paper_id})
            MERGE (l:Limitation {description: $limitation_description})
            MERGE (p)-[:IDENTIFIES]->(l)
            """,
            paper_id=paper_id,
            limitation_description=limitation_description,
        )


def link_paper_proposes_gap(client: KnowledgeGraphClient, paper_id: str, gap_id: str) -> None:
    """Section 11: paper -[:PROPOSES]-> gap (a paper's own stated future-work
    section proposing the same gap this platform later detects
    independently via `find_sparse_method_dataset_pairs` etc.)."""
    with client.session() as session:
        session.run(
            """
            MERGE (p:Paper {id: $paper_id})
            MERGE (g:ResearchGap {id: $gap_id})
            MERGE (p)-[:PROPOSES]->(g)
            """,
            paper_id=paper_id,
            gap_id=gap_id,
        )
