from fastapi import APIRouter
from sqlalchemy import text

from app.core.config import get_settings
from app.db.session import engine
from app.sandbox.executor import SandboxUnavailableError
from app.sandbox.executor import _get_client as get_docker_client
from app.services.knowledge_graph.client import get_kg_client

router = APIRouter(prefix="/health", tags=["health"])
settings = get_settings()


@router.get("")
def health():
    """Section 82: reports real subsystem status, never a blanket 'ok'
    that papers over a down dependency (Section 81)."""
    status = {"status": "ok", "checks": {}}

    db_kind = "sqlite" if settings.database_url.startswith("sqlite") else "postgres"
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        status["checks"][f"database_{db_kind}"] = "ok"
    except Exception as exc:
        status["checks"][f"database_{db_kind}"] = f"unavailable: {exc}"
        status["status"] = "degraded"

    try:
        kg_ok = get_kg_client().verify_connectivity()
        status["checks"]["neo4j"] = "ok" if kg_ok else "unavailable"
        if not kg_ok:
            status["status"] = "degraded"
    except Exception as exc:
        status["checks"]["neo4j"] = f"unavailable: {exc}"
        status["status"] = "degraded"

    try:
        get_docker_client()
        status["checks"]["sandbox_docker"] = "ok"
    except SandboxUnavailableError as exc:
        status["checks"]["sandbox_docker"] = f"unavailable: {exc}"
        status["status"] = "degraded"

    status["checks"]["llm_provider"] = "configured" if settings.llm_configured else "NOT_CONFIGURED"

    return status
