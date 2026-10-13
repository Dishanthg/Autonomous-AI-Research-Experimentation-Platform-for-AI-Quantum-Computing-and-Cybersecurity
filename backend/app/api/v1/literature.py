from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.user import User
from app.schemas.literature import LiteratureSearchRequest, PaperOut
from app.security.rbac import require_researcher
from app.services.audit import record_audit
from app.services.literature import arxiv_client, crossref_client, semantic_scholar_client
from app.services.literature.ingest import upsert_arxiv_paper, upsert_crossref_paper, upsert_semantic_scholar_paper

router = APIRouter(prefix="/literature", tags=["literature"])

_SEARCH_BY_SOURCE = {
    "arxiv": (arxiv_client.search, arxiv_client.ArxivClientError, upsert_arxiv_paper),
    "semantic_scholar": (
        semantic_scholar_client.search,
        semantic_scholar_client.SemanticScholarClientError,
        upsert_semantic_scholar_paper,
    ),
    "crossref": (crossref_client.search, crossref_client.CrossrefClientError, upsert_crossref_paper),
}


@router.post("/search", response_model=list[PaperOut])
def search_and_ingest(
    payload: LiteratureSearchRequest, user: User = Depends(require_researcher), db: Session = Depends(get_db)
):
    """Section 9: real bibliographic retrieval (arXiv / Semantic Scholar /
    Crossref), deterministic dedup, no fabricated bibliographic fields.
    Fails loudly (503) rather than returning a fabricated result set if the
    selected source is unreachable (Section 81)."""
    search_fn, error_cls, upsert_fn = _SEARCH_BY_SOURCE[payload.source]
    try:
        papers = search_fn(payload.query, max_results=payload.max_results)
    except error_cls as exc:
        raise HTTPException(status_code=503, detail=str(exc))

    rows = [upsert_fn(db, p) for p in papers]
    record_audit(
        db,
        actor_user_id=user.id,
        action="literature.search",
        resource_type="paper",
        after_state={"query": payload.query, "count": len(rows)},
    )
    db.commit()
    for r in rows:
        db.refresh(r)
    return rows
