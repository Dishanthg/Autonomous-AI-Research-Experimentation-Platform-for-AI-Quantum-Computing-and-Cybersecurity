"""Real Semantic Scholar Graph API client (Section 9). No API key required
for the public rate-limited tier. Never fabricates bibliographic data: any
field the API doesn't return is left None, matching `arxiv_client.py`'s
honesty rule.
"""

from dataclasses import dataclass
from typing import Optional

import httpx

from app.core.config import get_settings

settings = get_settings()

FIELDS = "title,abstract,year,venue,authors,externalIds,url"


@dataclass
class SemanticScholarPaper:
    external_id: str
    title: str
    authors: list
    abstract: Optional[str]
    year: Optional[int]
    url: Optional[str]
    doi: Optional[str]
    venue: Optional[str] = None
    raw_metadata: Optional[dict] = None


class SemanticScholarClientError(RuntimeError):
    """Raised on network/parsing failure. Callers must surface this, not
    silently return an empty/fabricated result set (Section 81)."""


def search(query: str, max_results: int = 10, timeout: float = 15.0) -> list[SemanticScholarPaper]:
    params = {"query": query, "limit": max_results, "fields": FIELDS}
    try:
        resp = httpx.get(f"{settings.semantic_scholar_api_base}/paper/search", params=params, timeout=timeout)
        resp.raise_for_status()
    except httpx.HTTPError as exc:
        raise SemanticScholarClientError(f"Semantic Scholar API request failed: {exc}") from exc

    try:
        body = resp.json()
    except ValueError as exc:
        raise SemanticScholarClientError(f"Semantic Scholar API returned unparseable JSON: {exc}") from exc

    papers = []
    for item in body.get("data", []):
        external_ids = item.get("externalIds") or {}
        authors = [a.get("name", "") for a in (item.get("authors") or [])]
        papers.append(
            SemanticScholarPaper(
                external_id=item.get("paperId", ""),
                title=item.get("title") or "",
                authors=authors,
                abstract=item.get("abstract"),
                year=item.get("year"),
                url=item.get("url"),
                doi=external_ids.get("DOI"),
                venue=item.get("venue"),
                raw_metadata={"externalIds": external_ids},
            )
        )
    return papers
