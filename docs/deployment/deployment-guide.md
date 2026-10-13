# Deployment Guide

## Local development (verified, no external services)
See the root `README.md` Quickstart. SQLite + in-process execution; the
full backend test suite (85 tests as of this writing) runs this way with
zero external dependencies.

## Production topology (documented, not yet verified end-to-end in this
build's environment - see ADR-008/README for why)

```
                     ┌─────────────┐
                     │  frontend   │  (React/Vite, served statically or via
                     │  (nginx or  │   the dev server behind a reverse proxy)
                     │   similar)  │
                     └──────┬──────┘
                            │ HTTPS
                     ┌──────▼──────┐
                     │   backend   │  (FastAPI + Uvicorn, multiple workers)
                     └───┬─────┬───┘
              ┌──────────┘     └───────────┐
        ┌─────▼─────┐                ┌─────▼─────┐
        │ PostgreSQL│                │   Neo4j   │
        └───────────┘                └───────────┘
                            │
                     ┌──────▼──────┐
                     │   Docker    │  (sandbox executor - Tier 1 only in
                     │   daemon    │   production; ALLOW_PROCESS_SANDBOX
                     │  (isolated  │   must remain false)
                     │   host)     │
                     └─────────────┘
```

Steps (`docker-compose.yml` in the repo root defines this topology):

1. Set `DATABASE_URL` to a `postgresql+psycopg://...` URL and provide
   `NEO4J_URI`/`NEO4J_USER`/`NEO4J_PASSWORD`.
2. Set `SANDBOX_BACKEND=docker` and leave `ALLOW_PROCESS_SANDBOX=false`
   (the `.env.example` defaults - do not change these in production).
3. Set a real `JWT_SECRET_KEY` (64+ random bytes) - never the dev default.
4. Build the sandbox images (`sandbox/images/{ai,cyber,quantum}-image/`) and
   push them somewhere the backend's Docker daemon can pull from, or build
   them on the same host.
5. Run `alembic upgrade head` against the production database before first
   boot.
6. Mount `/var/run/docker.sock` into the backend container (as
   `docker-compose.yml` does) ONLY if the backend container itself runs on
   a host you trust to grant it sibling-container access - this is a real
   privilege; do not do this in a multi-tenant environment without
   additional isolation (e.g. a dedicated Docker-in-Docker or Sysbox setup)
   this build does not implement.

## What's NOT verified yet (see FINAL_RESEARCH_AUDIT.md)
- This exact topology has not been run end-to-end in this build's
  environment (a disk-space incident took down local Docker mid-build -
  see ADR-008). The Docker Tier 1 sandbox's *failure* path (daemon
  unreachable → clean error, no fallback) is verified; its *success* path
  (a real container actually executing a template) is not yet verified
  here.
- No CI job currently deploys or smoke-tests this topology (Section 83
  deliberately excludes expensive/Docker-dependent jobs from per-commit CI).
