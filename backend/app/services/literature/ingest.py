from typing import Union

from sqlalchemy.orm import Session

from app.models.literature import Paper
from app.services.literature.arxiv_client import ArxivPaper
from app.services.literature.crossref_client import CrossrefPaper
from app.services.literature.semantic_scholar_client import SemanticScholarPaper

SourcePaper = Union[ArxivPaper, SemanticScholarPaper, CrossrefPaper]


def _upsert(db: Session, source: str, paper: SourcePaper) -> Paper:
    """Deterministic dedup by (source, external_id). Never overwrites a
    stored field with a fabricated value - only refreshes from the source
    API's own response."""
    existing = (
        db.query(Paper).filter(Paper.source == source, Paper.external_id == paper.external_id).one_or_none()
    )
    if existing:
        return existing

    row = Paper(
        title=paper.title,
        authors=paper.authors,
        year=paper.year,
        venue=paper.venue,
        doi=paper.doi,
        url=paper.url,
        source=source,
        external_id=paper.external_id,
        abstract=paper.abstract,
        keywords=None,
        raw_metadata=paper.raw_metadata,
    )
    db.add(row)
    db.flush()
    return row


def upsert_arxiv_paper(db: Session, paper: ArxivPaper) -> Paper:
    return _upsert(db, "arxiv", paper)


def upsert_semantic_scholar_paper(db: Session, paper: SemanticScholarPaper) -> Paper:
    return _upsert(db, "semantic_scholar", paper)


def upsert_crossref_paper(db: Session, paper: CrossrefPaper) -> Paper:
    return _upsert(db, "crossref", paper)
