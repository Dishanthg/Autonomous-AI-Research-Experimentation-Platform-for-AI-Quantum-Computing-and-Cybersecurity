"""Neo4j-backed Research Knowledge Graph (Section 11/K).

Fails loudly, not silently, when Neo4j is unreachable (Section 81) - callers
must catch KnowledgeGraphUnavailableError and surface it rather than
proceeding as if the graph query returned "no results found".
"""

from contextlib import contextmanager

from neo4j import GraphDatabase
from neo4j.exceptions import Neo4jError, ServiceUnavailable

from app.core.config import get_settings

settings = get_settings()


class KnowledgeGraphUnavailableError(RuntimeError):
    pass


class KnowledgeGraphClient:
    def __init__(self):
        self._driver = GraphDatabase.driver(
            settings.neo4j_uri, auth=(settings.neo4j_user, settings.neo4j_password)
        )

    def close(self):
        self._driver.close()

    @contextmanager
    def session(self):
        try:
            with self._driver.session() as session:
                yield session
        except (ServiceUnavailable, Neo4jError) as exc:
            raise KnowledgeGraphUnavailableError(f"Neo4j unreachable or query failed: {exc}") from exc

    def verify_connectivity(self) -> bool:
        try:
            self._driver.verify_connectivity()
            return True
        except (ServiceUnavailable, Neo4jError):
            return False


_client: KnowledgeGraphClient | None = None


def get_kg_client() -> KnowledgeGraphClient:
    global _client
    if _client is None:
        _client = KnowledgeGraphClient()
    return _client
