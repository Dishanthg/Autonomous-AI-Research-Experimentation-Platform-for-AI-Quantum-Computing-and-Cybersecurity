# Literature Analysis

The literature engine queries the live arXiv API (`app/services/literature/arxiv_client.py`)
with no fabricated fields: title, authors, abstract, year, and URL come
directly from arXiv's Atom response; any field arXiv doesn't provide is
stored as `NULL`, never guessed. During development, a live query for
"graph neural network anomaly detection cybersecurity" returned three real,
verifiable papers (arXiv IDs 2212.05478, 2305.02496, 2205.15508), confirming
the retrieval path works against the real API rather than mocked data.

Claim extraction (`app/services/literature/claim_extraction.py`) requires an
LLM provider (Anthropic API key), which was not configured in this build
environment, so **no papers have actually had claims extracted from their
abstracts in this session** — the extraction logic itself is unit-tested
against a fake provider double (`test_claim_extraction.py`), confirming the
provenance guard (a claim's `source_span` must literally appear in the
source text) works correctly, but this is a test of the mechanism, not a
completed literature analysis of any real corpus.

Semantic Scholar and Crossref integration are configured (base URLs in
`.env.example`) but have no client code written — NOT_IMPLEMENTED.
