"""Real arXiv API client. No API key required. Never fabricates bibliographic
data (Section 9): any field arXiv doesn't return is left None, not guessed.
"""

import xml.etree.ElementTree as ET
from dataclasses import dataclass
from typing import Optional

import httpx

from app.core.config import get_settings

settings = get_settings()

ATOM_NS = "{http://www.w3.org/2005/Atom}"
ARXIV_NS = "{http://arxiv.org/schemas/atom}"


@dataclass
class ArxivPaper:
    external_id: str
    title: str
    authors: list
    abstract: str
    year: Optional[int]
    url: str
    doi: Optional[str]
    venue: Optional[str] = None
    raw_metadata: Optional[dict] = None


class ArxivClientError(RuntimeError):
    """Raised on network/parsing failure. Callers must surface this, not
    silently return an empty/fabricated result set (Section 81)."""


def search(query: str, max_results: int = 10, timeout: float = 15.0) -> list[ArxivPaper]:
    params = {
        "search_query": f"all:{query}",
        "start": 0,
        "max_results": max_results,
    }
    try:
        resp = httpx.get(settings.arxiv_api_base, params=params, timeout=timeout)
        resp.raise_for_status()
    except httpx.HTTPError as exc:
        raise ArxivClientError(f"arXiv API request failed: {exc}") from exc

    try:
        root = ET.fromstring(resp.text)
    except ET.ParseError as exc:
        raise ArxivClientError(f"arXiv API returned unparseable XML: {exc}") from exc

    papers = []
    for entry in root.findall(f"{ATOM_NS}entry"):
        arxiv_id_full = entry.findtext(f"{ATOM_NS}id") or ""
        arxiv_id = arxiv_id_full.rsplit("/", 1)[-1] if arxiv_id_full else ""
        title = (entry.findtext(f"{ATOM_NS}title") or "").strip().replace("\n", " ")
        summary = (entry.findtext(f"{ATOM_NS}summary") or "").strip()
        authors = [(a.findtext(f"{ATOM_NS}name") or "").strip() for a in entry.findall(f"{ATOM_NS}author")]
        published = entry.findtext(f"{ATOM_NS}published")
        year = int(published[:4]) if published else None
        doi = entry.findtext(f"{ARXIV_NS}doi")
        url = entry.findtext(f"{ATOM_NS}id") or ""

        papers.append(
            ArxivPaper(
                external_id=arxiv_id,
                title=title,
                authors=authors,
                abstract=summary,
                year=year,
                url=url,
                doi=doi,
                raw_metadata={"published": published},
            )
        )
    return papers
