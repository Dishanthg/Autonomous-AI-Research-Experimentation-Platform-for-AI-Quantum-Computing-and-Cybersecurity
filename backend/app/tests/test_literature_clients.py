"""Section 9: Semantic Scholar and Crossref clients, same real-API /
no-fabrication pattern as arxiv_client.py. Network calls are mocked with
respx (already a dev dependency) so these tests are deterministic and
offline - they exercise real parsing logic against a realistic response
shape, not a live network call.
"""

import httpx
import pytest
import respx

from app.core.config import get_settings
from app.services.literature import crossref_client, semantic_scholar_client
from app.services.literature.ingest import upsert_crossref_paper, upsert_semantic_scholar_paper

settings = get_settings()


@respx.mock
def test_semantic_scholar_search_parses_real_response_shape():
    respx.get(f"{settings.semantic_scholar_api_base}/paper/search").mock(
        return_value=httpx.Response(
            200,
            json={
                "total": 1,
                "data": [
                    {
                        "paperId": "abc123",
                        "title": "Attention Is All You Need",
                        "abstract": "We propose a new architecture...",
                        "year": 2017,
                        "venue": "NeurIPS",
                        "authors": [{"name": "A. Vaswani"}, {"name": "N. Shazeer"}],
                        "externalIds": {"DOI": "10.5555/foo"},
                        "url": "https://www.semanticscholar.org/paper/abc123",
                    }
                ],
            },
        )
    )
    results = semantic_scholar_client.search("transformers", max_results=5)
    assert len(results) == 1
    paper = results[0]
    assert paper.external_id == "abc123"
    assert paper.title == "Attention Is All You Need"
    assert paper.authors == ["A. Vaswani", "N. Shazeer"]
    assert paper.doi == "10.5555/foo"
    assert paper.year == 2017


@respx.mock
def test_semantic_scholar_missing_fields_are_none_not_fabricated():
    respx.get(f"{settings.semantic_scholar_api_base}/paper/search").mock(
        return_value=httpx.Response(200, json={"data": [{"paperId": "x", "title": "Untitled work"}]})
    )
    results = semantic_scholar_client.search("q")
    assert results[0].doi is None
    assert results[0].year is None
    assert results[0].abstract is None


@respx.mock
def test_semantic_scholar_raises_on_http_error():
    respx.get(f"{settings.semantic_scholar_api_base}/paper/search").mock(
        return_value=httpx.Response(503)
    )
    with pytest.raises(semantic_scholar_client.SemanticScholarClientError):
        semantic_scholar_client.search("q")


@respx.mock
def test_crossref_search_parses_real_response_shape():
    respx.get(f"{settings.crossref_api_base}/works").mock(
        return_value=httpx.Response(
            200,
            json={
                "message": {
                    "items": [
                        {
                            "DOI": "10.1000/xyz",
                            "title": ["Deep Learning"],
                            "author": [{"given": "Yann", "family": "LeCun"}],
                            "published-print": {"date-parts": [[2015, 5, 1]]},
                            "container-title": ["Nature"],
                            "URL": "https://doi.org/10.1000/xyz",
                            "type": "journal-article",
                        }
                    ]
                }
            },
        )
    )
    results = crossref_client.search("deep learning", max_results=5)
    assert len(results) == 1
    paper = results[0]
    assert paper.doi == "10.1000/xyz"
    assert paper.title == "Deep Learning"
    assert paper.authors == ["Yann LeCun"]
    assert paper.year == 2015
    assert paper.venue == "Nature"


@respx.mock
def test_crossref_missing_fields_are_none_not_fabricated():
    respx.get(f"{settings.crossref_api_base}/works").mock(
        return_value=httpx.Response(200, json={"message": {"items": [{"DOI": "10.1/x"}]}})
    )
    results = crossref_client.search("q")
    assert results[0].title == ""
    assert results[0].year is None
    assert results[0].venue is None


@respx.mock
def test_crossref_raises_on_http_error():
    respx.get(f"{settings.crossref_api_base}/works").mock(return_value=httpx.Response(500))
    with pytest.raises(crossref_client.CrossrefClientError):
        crossref_client.search("q")


def test_ingest_dedups_semantic_scholar_and_crossref_papers_by_source_and_external_id(db_session):
    ss_paper = semantic_scholar_client.SemanticScholarPaper(
        external_id="dup1", title="T", authors=[], abstract=None, year=None, url=None, doi=None
    )
    first = upsert_semantic_scholar_paper(db_session, ss_paper)
    second = upsert_semantic_scholar_paper(db_session, ss_paper)
    assert first.id == second.id

    cr_paper = crossref_client.CrossrefPaper(
        external_id="10.1/dup", title="T2", authors=[], abstract=None, year=None, url=None, doi="10.1/dup"
    )
    first_cr = upsert_crossref_paper(db_session, cr_paper)
    second_cr = upsert_crossref_paper(db_session, cr_paper)
    assert first_cr.id == second_cr.id
    assert first_cr.id != first.id
