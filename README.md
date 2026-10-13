# ResearchMind-Q

An evidence-grounded AI research assistant for the intersection of
**Artificial Intelligence**, **Cybersecurity**, and **Quantum Computing** —
built to investigate, not assume, whether AI agents can meaningfully support
the scientific workflow (literature → hypothesis → experiment → statistics →
critique → conclusion) while preserving reproducibility, evidence grounding,
and human oversight.

See [`FINAL_RESEARCH_AUDIT.md`](./FINAL_RESEARCH_AUDIT.md) for an honest,
component-by-component status (VERIFIED / IMPLEMENTED — NOT VERIFIED /
NOT_IMPLEMENTED) and [`research/RESEARCH_LOG.md`](./research/RESEARCH_LOG.md)
for the build history including failures.

## What this is not

Not a paper-summarization chatbot, not a generic RAG demo, not an automated
paper writer, not a system that claims scientific conclusions without
statistical evidence behind them. See `docs/architecture/adr/` for the design
decisions that enforce this.

## Quickstart (local, no Docker required)

This platform runs entirely on local SQLite for development — no Postgres,
Neo4j, or Docker needed to develop or run the test suite.

```bash
cd backend
python -m venv .venv
source .venv/Scripts/activate   # Windows Git Bash; use .venv/bin/activate on Linux/Mac
pip install -r requirements.txt -r requirements-dev.txt
cp ../.env.example .env         # defaults to sqlite:///./researchmind_dev.db
alembic upgrade head
pytest -v                       # 87 tests, all pass, no external services needed
uvicorn app.main:app --reload   # API at http://localhost:8000/docs, metrics at /metrics
```

```bash
cd frontend
npm install
npm run dev                     # UI at http://localhost:5173
```

Register a user via the UI or `POST /api/v1/auth/register`, then log in.
The `/api/v1/health` endpoint honestly reports which optional subsystems
(Neo4j, Docker sandbox, LLM provider) are configured — none are required for
the core pipeline to function.

### Generate real research artifacts

Set `SANDBOX_BACKEND=process` and `ALLOW_PROCESS_SANDBOX=true` in
`backend/.env` (ADR-009 - a reduced-isolation tier restricted to this
platform's own reviewed codegen templates, for environments without
Docker) and run:

```bash
cd backend
python -m scripts.run_demo               # Demonstrations 1-3 (Sections 91-93)
python -m scripts.run_research_pipeline   # Experiment 5: AI model comparison
python -m scripts.run_cyber_experiment    # Experiment 6: IDS comparison
python -m scripts.run_ablation_memory     # memory-ablation (Section 62)
python -m scripts.run_ablation_critic     # critic-ablation (Section 63)
python -m scripts.generate_figures        # real plots from the JSON above
python -m scripts.generate_research_index # DB-derived index/registry docs
python -m scripts.reproduce_experiment <experiment_id>   # Section 54
```

Every command above writes real output to `research/` or `reproducibility/`
- nothing is pre-generated or fabricated; see `FINAL_RESEARCH_AUDIT.md` for
what's actually been run this way.

## Production topology (Postgres + Neo4j + Docker sandbox)

`docker-compose.yml` documents the production topology. Set `DATABASE_URL`
to a `postgresql+psycopg://...` URL, provide `NEO4J_*` credentials, and run:

```bash
docker compose up -d postgres neo4j backend frontend
```

**Not verified in this repository's own CI or build session** — see
ADR-004, ADR-007, ADR-008 for why (a disk-space incident on the build
machine made Docker unusable partway through development). The code is
written against real Docker/Neo4j SDKs and fails loudly (not silently) if
those services are unreachable; it has simply not yet been exercised against
live instances of them.

## Repository layout

The repository is organized by runtime responsibility, research artifacts, and
operational documentation:

| Area | Contents |
| --- | --- |
| [`backend/`](./backend/) | FastAPI application, SQLAlchemy models, Alembic migrations, and tests |
| [`backend/app/agents/`](./backend/app/agents/) | Injectable LLM agent layer for hypothesis drafting, critique, gap narration, and research synthesis |
| [`backend/app/sandbox/`](./backend/app/sandbox/) | Two-tier experiment executor: Docker Tier 1 and process Tier 2 |
| [`backend/scripts/`](./backend/scripts/) | CLI entry points for demos, experiments, ablations, reports, and reproduction |
| [`frontend/`](./frontend/) | React + TypeScript UI: dashboard, project detail, experiment approval, quantum lab, and audit log |
| [`sandbox/images/`](./sandbox/images/) | Per-domain Docker images used by the experiment sandbox |
| [`knowledge/`](./knowledge/) | Research Knowledge Graph ontology, maintained as schema-as-data |
| [`research/`](./research/) | Experiment and ablation results, figures, tables, and research indexes |
| [`reproducibility/`](./reproducibility/) | Reproduction configurations and generated reports |
| [`infrastructure/`](./infrastructure/) | Prometheus scrape configuration |
| [`docs/architecture/adr/`](./docs/architecture/adr/) | Architecture Decision Records, including sandbox tiering decisions |
| [`docs/masters-application/`](./docs/masters-application/) | Evidence package for the master's application and research build specification |
| [`FINAL_RESEARCH_AUDIT.md`](./FINAL_RESEARCH_AUDIT.md) | Current, honest status of every subsystem |

## Core principles (enforced in code, not just documented)

- Every claim is tagged `REPORTED_IN_LITERATURE | AI_INFERRED | HYPOTHESIZED |
  SIMULATED | EXPERIMENTALLY_OBSERVED | HUMAN_VERIFIED` (`app/models/enums.py`).
- No LLM call anywhere in the statistics/conclusion path
  (`app/services/statistics/`) — every metric and p-value comes from
  `numpy`/`scipy` over real data.
- No experiment executes without two independently-checked, audit-logged
  human approvals (`app/api/v1/experiments.py`).
- Generated code runs only inside a resource-limited sandbox
  (`app/sandbox/`) — a Docker tier for arbitrary code, and a
  reduced-isolation process tier (ADR-009) restricted to this platform's
  own reviewed codegen templates, gated behind an explicit config flag and
  a capability argument no API caller can set directly. If neither can run,
  execution fails loudly rather than falling back to running code
  unsandboxed.
- Every quantum result is labeled `SIMULATOR` or `HARDWARE` from the backend
  record itself (this build only ever produces `SIMULATOR` results — no
  hardware wiring exists, by design).
- Every LLM agent (`app/agents/`) raises rather than fabricates when no
  provider is configured, and each enforces its own structural guardrail:
  fixed-vocabulary rejection (hypothesis drafting), add-only critique
  (critic narration), evidence-derived confidence (gap narration), and a
  numeric-consistency check against invented figures (report synthesis).

## License

MIT — see [`LICENSE`](./LICENSE).
