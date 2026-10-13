# Final Research Audit

Status as of 2026-09-06 (session 2 - see `research/RESEARCH_LOG.md` for the
full chronology). Every line below uses the project's own status
vocabulary (Rule 12): **NOT_IMPLEMENTED**, **IMPLEMENTED — NOT VERIFIED**,
or **VERIFIED**. Nothing here is aspirational.

## System components

| Component | Status | Evidence |
|---|---|---|
| Research workspace (projects, questions) | VERIFIED | API integration test; real rows in `research/projects/INDEX.md` |
| Literature engine (arXiv) | VERIFIED | Live arXiv queries via `app.services.literature.cli`, real results ingested |
| Literature engine (Semantic Scholar / Crossref) | NOT_IMPLEMENTED | Config placeholders only; no client code written |
| Evidence/provenance model (ClaimType, span-grounding) | VERIFIED | `test_claim_extraction.py` |
| Research knowledge graph (Neo4j) | IMPLEMENTED — NOT VERIFIED | Code + Cypher + `knowledge/ontology.yaml` written; never run against a live Neo4j in this environment (disk-space incident, ADR-008) |
| Gap analyzer | IMPLEMENTED — NOT VERIFIED | Deterministic Cypher queries + `GapNarrativeAgent` LLM framing written; depends on knowledge graph above and an LLM key |
| Hypothesis generator (LLM) | IMPLEMENTED — NOT VERIFIED | `app.agents.hypothesis_agent.HypothesisAgent` built and unit-tested against a fake provider (13 agent tests); never run against a real Anthropic key in this session |
| Hypothesis quality check | VERIFIED | `test_hypothesis_quality.py` (4 tests) + real use in `run_demo.py`/`run_experiment.py` |
| Experiment planner / baseline registry | VERIFIED (as fixed vocabulary) | Baselines are a reviewed, hardcoded allowlist in codegen templates (Section 16); `research/baselines/REGISTRY.md` is generated from real DB rows |
| Human approval gates (plan + execution) | VERIFIED | `test_api_integration.py::test_full_research_pipeline_end_to_end` - both gates exercised, including a rejected first config (critic-blocked, too few runs) |
| Code generation (AI, cybersecurity templates) | VERIFIED | `test_codegen.py` — generated scripts actually run and produce metrics |
| Secure sandbox - Docker Tier 1 | IMPLEMENTED — NOT VERIFIED (happy path) / VERIFIED (failure path) | `test_execute_returns_503_when_docker_backend_unavailable`; live container execution not exercised in this environment |
| Secure sandbox - Process Tier 2 (ADR-009) | VERIFIED | `test_sandbox_executor.py` (real subprocess execution, timeout enforcement, secret-leak prevention) + used for real in every experiment below |
| Experiment execution orchestration | VERIFIED | Full pipeline runs end-to-end via the real HTTP API in the process-tier sandbox |
| Result analyzer / statistical analyst | VERIFIED | `test_statistics_engine.py` (8 tests) + real results in `research/*/*.json` |
| Conclusion engine (SUPPORTED/NOT_SUPPORTED/INCONCLUSIVE) | VERIFIED | 5 SUPPORTED + 2 NOT_SUPPORTED real conclusions recorded this session (`research/evaluation/summary.md`) |
| Limitation Detector (Section 41) | VERIFIED | `test_limitations_and_next_experiment.py` (6 tests) + real findings attached to every experiment run |
| Next-Experiment Generator (Section 42) | VERIFIED | 4 tests + real proposals returned via `GET /experiments/{id}/next-experiments` |
| Research critic (deterministic checklist) | VERIFIED | `test_critic.py` (5 tests) + `run_ablation_critic.py` real ablation |
| Research critic (LLM narrative pass) | IMPLEMENTED — NOT VERIFIED | `app.agents.critic_narrative_agent.CriticNarrativeAgent` built, unit-tested against a fake provider; never run against a real LLM |
| Research memory (structured queries) | VERIFIED | `run_ablation_memory.py` - real with/without-memory contrast against a populated project |
| AI experiment domain | VERIFIED end-to-end | `research/ai/experiment_5_model_comparison.json` - two real, concluded hypotheses (RF, XGBoost vs LogReg on breast_cancer) |
| Cybersecurity experiment domain | VERIFIED end-to-end | `research/cybersecurity/*.json` - three real, concluded hypotheses |
| Quantum experiment domain | VERIFIED | `test_quantum.py` (8 tests) + `research/quantum/demo_grover_vs_classical.json` |
| PQC experiment domain (classical) | VERIFIED | `test_pqc.py` + `research/tables/pqc_classical_benchmark.md` |
| PQC experiment domain (post-quantum) | NOT_IMPLEMENTED | liboqs not installed in this environment; honestly reported, not fabricated |
| Reproducibility packaging | VERIFIED | `reproducibility/experiment-f88e9566/` - real MATCH/DEVIATION report, `conclusion_status_matches: true` |
| Ablation studies (memory, critic) | VERIFIED (n=1 constructed scenario each) | `research/ablations/*.json` - see caveats in each file; not yet a large-scale study |
| Dashboard / core UI (7 of 20 spec pages) | VERIFIED (compiles, calls real API) | Login, Dashboard, Project Detail, Experiment Approval (+ Limitations/Next-Experiments panels), Quantum Lab, Audit Log; shared `Badge`/`Card` components; `tsc -b` clean |
| Remaining 13 UI pages (Literature, Knowledge Graph, Gaps, Statistics detail, Cybersecurity/AI Labs, Reproducibility, Timeline, etc.) | NOT_IMPLEMENTED | — |
| Authentication (JWT) | VERIFIED | `test_auth_security.py`, integration test |
| RBAC | VERIFIED | `test_api_integration.py::test_rbac_viewer_cannot_create_project` |
| Audit logging | VERIFIED | `AuditLogPage.tsx` + `GET /api/v1/audit`, exercised implicitly by every mutating endpoint call in tests |
| Observability (Prometheus) | VERIFIED | `test_observability.py` - real `/metrics` endpoint, `infrastructure/prometheus.yml` scrape config |
| Observability (Grafana) | NOT_IMPLEMENTED | — |
| CI/CD | IMPLEMENTED — NOT VERIFIED (never run on a real CI runner) | `.github/workflows/ci.yml` mirrors the exact local commands that pass locally |
| Docker Compose topology (Postgres/Neo4j/backend/frontend) | IMPLEMENTED — NOT VERIFIED | Written; not run to completion in this environment |
| Multi-agent layer (`app/agents/`) | VERIFIED (parsing/safety logic) / NOT VERIFIED (real LLM calls) | 13 tests against a FakeProvider double; no `ANTHROPIC_API_KEY` configured in this session |

## Hypotheses (H1-H7, Section 4)

Still formally **UNRESOLVED** (no large-scale ablation study has been run),
but two now have a real, if small, first data point:

- **H3 (critic improves validity):** `research/ablations/critic_ablation.json`
  shows the deterministic critic correctly blocks a constructed
  flawed design (4 hypothesis objections, 2 config objections,
  `would_be_approved: false`) that would otherwise have passed unchecked.
  n=1 constructed scenario - directional evidence, not proof.
- **H2/H6 (memory improves consistency / reduces duplicate effort):**
  `research/ablations/memory_ablation.json` shows the memory query
  correctly identifies a duplicate experiment with `enabled=True` and
  misses it with `enabled=False`, using the platform's actual production
  code path. n=1 duplicate scenario in one project.

H1, H4, H5, H7 remain untested by a dedicated experiment in this session,
though H5 (human approval reduces unsafe actions) has strong procedural
support: the full pipeline test proves execution is unreachable without
both gates, and a deliberately flawed config was rejected before reaching
Gate 1.

## Honesty checks (Section 100 Final Quality Gate)

- No fabricated results exist: every number in `research/` and
  `reproducibility/` was produced by running real code (scipy stats, Qiskit
  Aer, `cryptography` library, live arXiv API, real sklearn/xgboost model
  training inside the process-tier sandbox).
- No fabricated citations exist: the literature client only stores what
  arXiv's API actually returns; unavailable fields are `NULL`.
- No unrestricted code execution exists: the process-tier sandbox
  (ADR-009) only ever runs this platform's own reviewed codegen templates
  (`caller_declares_trusted_template` is set only by the orchestrator,
  never a caller-supplied flag reachable from the API), with a restricted
  environment (verified to not leak host secrets), a wall-clock timeout,
  and an ephemeral workspace; the Docker tier remains required for
  anything else.
- No secrets exist in git: `.env` is gitignored; `.env.example` ships with
  placeholder values only; `ANTHROPIC_API_KEY` is empty by default and every
  LLM-dependent code path (both the original claim-extraction service and
  the four new agents) raises `LLMNotConfiguredError` rather than working
  around its absence.

## Reproducing this audit

```
cd backend
python -m venv .venv && source .venv/Scripts/activate  # or .venv/bin/activate on Linux/Mac
pip install -r requirements.txt -r requirements-dev.txt
alembic upgrade head
pytest -v --tb=short
```
Expected: 87 passed, 0 failed, 0 skipped, no Docker/Postgres/Neo4j required.

To regenerate the real research artifacts under `research/` and
`reproducibility/`:
```
python -m scripts.run_demo
python -m scripts.run_research_pipeline
python -m scripts.run_cyber_experiment
python -m scripts.run_ablation_memory
python -m scripts.run_ablation_critic
python -m scripts.reproduce_experiment <experiment_id printed above>
python -m scripts.generate_figures
python -m scripts.generate_research_index
```
