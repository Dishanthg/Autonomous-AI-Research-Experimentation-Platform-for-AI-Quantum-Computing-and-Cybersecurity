from typing import Literal, Optional

from pydantic import BaseModel

from app.models.enums import ClaimType


class LiteratureSearchRequest(BaseModel):
    query: str
    max_results: int = 10
    # Section 9: which real bibliographic API to query. Defaults to arXiv
    # (the originally-wired source); "semantic_scholar" and "crossref" use
    # the same real-API/no-fabrication pattern via their own client modules.
    source: Literal["arxiv", "semantic_scholar", "crossref"] = "arxiv"


class PaperOut(BaseModel):
    id: str
    title: str
    authors: Optional[list] = None
    year: Optional[int] = None
    venue: Optional[str] = None
    doi: Optional[str] = None
    url: Optional[str] = None
    source: str
    abstract: Optional[str] = None

    class Config:
        from_attributes = True


class PaperClaimOut(BaseModel):
    id: str
    paper_id: str
    source_span: str
    claim_text: str
    claim_type: ClaimType
    extracted_by: str
    human_verified: bool

    class Config:
        from_attributes = True
