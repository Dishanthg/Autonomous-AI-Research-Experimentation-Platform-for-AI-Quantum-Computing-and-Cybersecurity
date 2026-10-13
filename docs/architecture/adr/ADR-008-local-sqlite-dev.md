# ADR-008: Local SQLite for Development, Postgres for Production

## Status
Accepted, implemented (`app/core/config.py`, `app/models/mixins.py`).

## Context
Partway through this build, the development machine's system drive (`C:`)
reached 0 bytes free, which made Docker Desktop's daemon (whose virtual disk
lives on `C:` regardless of project location) unreliable and, per explicit
user instruction, off-limits for further use in this environment ("dont try
to run docker and all which uses drive space try to do it locally"). The
project directory itself lives on a separate drive (`D:`) with ample free
space, so the constraint is specifically about Docker/system-drive usage,
not about disk space in general.

## Decision
- `Settings.database_url` defaults to `sqlite:///./researchmind_dev.db`
  instead of a Postgres URL. `app/db/session.py` adds
  `connect_args={"check_same_thread": False}` only when the URL is SQLite.
- All primary keys use `String(36)` (a plain UUID string) instead of
  Postgres's native `UUID` type (`app/models/mixins.py::UUIDPKMixin`), so the
  exact same SQLAlchemy models work unmodified against SQLite or Postgres.
- `docker-compose.yml` and the Postgres/Neo4j service definitions remain the
  documented production topology; `DATABASE_URL` in `.env.example` shows both
  options with the Postgres line commented out.
- The full backend test suite (54 tests, including a complete API
  integration test) runs against an ephemeral SQLite file via a
  dependency-override fixture (`app/tests/conftest.py`), with no Docker,
  Postgres, or Neo4j dependency.

## Consequences
- Local development and CI (`.github/workflows/ci.yml`) never need Docker.
- Postgres-specific features (if any were added later - e.g. native JSONB
  operators) would need testing against a real Postgres instance separately;
  none are currently used, so this is a theoretical, not actual, gap.
- Knowledge-graph (Neo4j) and sandbox (Docker) integrations remain
  IMPLEMENTED - NOT VERIFIED as a direct consequence (see ADR-004, ADR-007).

## Verification status
IMPLEMENTED - VERIFIED. 54/54 backend tests pass against local SQLite,
including the full research-pipeline integration test.
