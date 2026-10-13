"""Real Crossref REST API client (Section 9). No API key required. Never
fabricates bibliographic data: any field Crossref doesn't return is left
None, matching `arxiv_client.py`'s honesty rule.
"""

from dataclasses import dataclass
from typing import Optional

import httpx

from app.core.config import get_settings

settings = get_settings()


@dataclass
class CrossrefPaper:
    external_id: str  # the DOI
    title: str
    authors: list
    abstract: Optional[str]
    year: Optional[int]
    url: Optional[str]
    doi: Optional[str]
    venue: Optional[str] = None
    raw_metadata: Optional[dict] = None


class CrossrefClientError(RuntimeError):
    """Raised on network/parsing failure. Callers must surface this, not
    silently return an empty/fabricated result set (Section 81)."""


def _extract_year(item: dict) -> Optional[int]:
    for key in ("published-print", "published-online", "published", "issued"):
        parts = (item.get(key) or {}).get("date-parts")
        if parts and parts[0] and parts[0][0]:
            return int(parts[0][0])
    return None


def _format_author(author: dict) -> str:
    given, family = author.get("given"), author.get("family")
    return " ".join(part for part in (given, family) if part) or (author.get("name") or "")


def search(query: str, max_results: int = 10, timeout: float = 15.0) -> list[CrossrefPaper]:
    params = {"query": query, "rows": max_results}
    try:
        resp = httpx.get(f"{settings.crossref_api_base}/works", params=params, timeout=timeout)
        resp.raise_for_status()
    except httpx.HTTPError as exc:
        raise CrossrefClientError(f"Crossref API request failed: {exc}") from exc

    try:
        body = resp.json()
    except ValueError as exc:
        raise CrossrefClientError(f"Crossref API returned unparseable JSON: {exc}") from exc

    papers = []
    for item in body.get("message", {}).get("items", []):
        doi = item.get("DOI")
        titles = item.get("title") or []
        container = item.get("container-title") or []
        papers.append(
            CrossrefPaper(
                external_id=doi or "",
                title=titles[0] if titles else "",
                authors=[_format_author(a) for a in (item.get("author") or [])],
                abstract=item.get("abstract"),
                year=_extract_year(item),
                url=item.get("URL"),
                doi=doi,
                venue=container[0] if container else None,
                raw_metadata={"type": item.get("type")},
            )
        )
    return papers
