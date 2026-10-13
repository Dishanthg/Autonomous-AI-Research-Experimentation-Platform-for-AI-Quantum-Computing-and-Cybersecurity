"""`make literature` - CLI for real arXiv literature search + ingestion
(Section 9). No fabricated bibliographic data - every field comes from
arXiv's own API response or is left null.

Usage: python -m app.services.literature.cli "graph neural network anomaly detection" --max-results 5
"""

import argparse
import sys

from app.db.session import SessionLocal
from app.services.literature.arxiv_client import ArxivClientError, search
from app.services.literature.ingest import upsert_arxiv_paper


def main() -> int:
    parser = argparse.ArgumentParser(description="ResearchMind-Q literature search CLI")
    parser.add_argument("query", type=str)
    parser.add_argument("--max-results", type=int, default=10)
    parser.add_argument("--no-ingest", action="store_true", help="Search only, do not write to the database")
    args = parser.parse_args()

    try:
        papers = search(args.query, max_results=args.max_results)
    except ArxivClientError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1

    if not papers:
        print("No papers found.")
        return 0

    db = None if args.no_ingest else SessionLocal()
    try:
        for p in papers:
            print(f"\n[{p.external_id}] {p.title}")
            print(f"  authors: {', '.join(p.authors) if p.authors else '(none listed)'}")
            print(f"  year: {p.year or 'unknown'}   url: {p.url}")
            if db is not None:
                row = upsert_arxiv_paper(db, p)
                print(f"  stored as paper id: {row.id}")
        if db is not None:
            db.commit()
    finally:
        if db is not None:
            db.close()

    print(f"\n{len(papers)} paper(s) retrieved from arXiv.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
