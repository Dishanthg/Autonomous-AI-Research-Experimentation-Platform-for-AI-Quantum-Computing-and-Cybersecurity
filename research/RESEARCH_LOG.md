# Research Log

Chronological record of what was tried, what worked, what failed, and why.
Failed/blocked items are kept, not deleted (Section 75).

---

## 2026-09-06 (session 2) — From infrastructure to real results

**Prompted by:** feedback that many `research/` and `agents/`-style
directories from the original repo layout were sitting empty, and a request
to push the platform toward something genuinely presentable (including in
an academic application) rather than infrastructure alone.

**Key architectural change (ADR-009):** split the sandbox into two
pluggable backends - the existing Docker Tier 1, and a new Process Tier 2
with reduced isolation (no network-isolation guarantee, best-effort rlimit
on POSIX only), gated behind `ALLOW_PROCESS_SANDBOX` and a
`caller_declares_trusted_template` flag the orchestrator sets only for its
own reviewed codegen output. This was the unlock: with
`SANDBOX_BACKEND=process` set in `backend/.env`, the full research pipeline
now genuinely executes end-to-end in this Docker-unavailable environment,
producing real conclusions instead of only proving it fails gracefully.

**What this enabled:**
- `test_full_research_pipeline_end_to_end` now asserts on a REAL completed
  run, a real conclusion, real statistics, real limitations, and real
  next-experiment proposals - not a 503. A second test
  (`test_execute_returns_503_when_docker_backend_unavailable`) was added to
  keep the original failure-path guarantee covered by explicitly forcing
  the Docker backend.
- Ran the platform on itself for real: Demonstrations 1-3, Experiment 5 (AI:
  RF/XGBoost vs LogReg on breast_cancer - both NOT_SUPPORTED at n=10 runs,
  an honest null result, not massaged into something more exciting),
  Experiment 6 (cybersecurity: two proposed detectors vs rule-based, both
  SUPPORTED), a real reproducibility run (`reproducibility/experiment-f88e9566/`,
  conclusion matched, only wall-clock timing metrics showed natural
  variance), and two real ablations (memory duplicate-detection, critic
  blocking a constructed flawed design).
- Implemented two previously-missing deterministic pieces from the original
  spec: the Limitation Detector (Section 41) and Next-Experiment Generator
  (Section 42), both now wired into `services/execution/analysis.py` and
  exposed via new endpoints.
- Implemented a real LLM agent layer (`app/agents/`): HypothesisAgent (fixed
  vocabulary enforcement, rejects out-of-list baselines/datasets and
  zero-effect-size drafts), CriticNarrativeAgent (can only ADD objections to
  the deterministic checklist's report, never remove one), GapNarrativeAgent
  (confidence computed deterministically from evidence shape, not
  self-reported by the model), ResearchSynthesizerAgent (flags numbers in
  its own prose that don't trace back to the facts it was given). All four
  are unit-tested against a fake provider double (13 tests) since no
  `ANTHROPIC_API_KEY` was available in this session - real-LLM verification
  remains a documented next step.
- Added real observability: `prometheus-fastapi-instrumentator` wired into
  `main.py`, a genuine `/metrics` endpoint (verified, not mocked), and
  `infrastructure/prometheus.yml`.
- Fixed the Makefile: every target (`literature`, `research`, `experiment`,
  `quantum`, `cybersecurity`, `pqc`, `reproduce`, `demo`) pointed at a CLI
  module that didn't exist yet from session 1. All were implemented for
  real this session and manually verified to run.
- Cleaned up every empty directory left over from the original repo
  scaffold - either populated with real, DB-derived or code-derived
  content, or removed as redundant (the top-level `agents/`/`scripts/`
  dirs, superseded by `backend/app/agents/` and `backend/scripts/`).

**Bugs found and fixed (kept here per Section 75):**
- `ExperimentConfigCreate` sample-size critic test passed but the config's
  metrics-requested field was empty in an early draft of `run_experiment.py`
  - caught by the critic itself blocking approval as designed, not by a
  human noticing first.
- A regex in `ResearchSynthesizerAgent`'s numeric-consistency checker
  (`-?\d+\.?\d*%?`) matched a sentence-ending period after an integer
  (e.g. "a series of 3." captured as "3."), which then failed the
  small-integer tolerance check as a false positive. Fixed by requiring a
  digit after the decimal point to count as a decimal.

**Result:** the project moved from "the pipeline correctly refuses to fake
a result" to "the pipeline produces real results, some of which are
honestly null" - full test suite now 87/87 passing, ~30 new tests added
this session, zero regressions in the 54 tests written in session 1.

**Next steps (unchanged in priority from session 1, still pending):**
1. Free disk space / use a machine with a healthy system drive; re-verify
   the Docker sandbox and Neo4j knowledge-graph paths.
2. Provide a real `ANTHROPIC_API_KEY` and re-verify the four agents against
   an actual model rather than only the FakeProvider double.
3. Run a proper (n>1, ideally human-subjects-informed) version of the
   memory and critic ablations - this session's ablations are real but
   small, constructed scenarios, honestly labeled as such.
4. Register real `Dataset`/`DatasetVersion` rows so experiments stop
   referencing a bare string in `codegen_spec`.

---

## 2026-09-06 (session 1) — Initial build

**Question:** Can an evidence-grounded AI research agent assist with the
research workflow across AI/cybersecurity/quantum while staying reproducible
and avoiding unsupported conclusions?

**What was built this session:**
- Full backend schema (26 tables) covering the entities in Section 44.
- FastAPI app with auth/RBAC, projects, hypotheses (+ deterministic quality
  check + deterministic critic), experiments (+ config versioning + two
  human-approval gates), quantum runs, literature search, memory queries,
  audit log, health check.
- Deterministic statistical engine (bootstrap CIs, Welch's t/Mann-Whitney
  auto-selection, Cohen's d, Holm-Bonferroni) and a pre-registration-based
  Conclusion Engine.
- Real Qiskit Aer quantum module: Bell state, Grover search (with the
  standard `floor(pi/4 * sqrt(N))` iteration count), QFT, and ideal-vs-noisy
  comparison via a depolarizing noise model.
- Real classical PQC benchmark (RSA-2048, ECDSA-P256 via the `cryptography`
  library); PQC (ML-KEM/ML-DSA via liboqs) wired but reports
  `NOT_IMPLEMENTED` honestly since liboqs isn't installed in this
  environment.
- Docker-based sandbox executor (CPU/memory limits, network=none by default,
  host-side timeout watchdog, non-root/read-only image) plus deterministic
  code-generation templates for AI model-comparison and cybersecurity
  intrusion-detection experiments.
- Minimal but functional React/TypeScript frontend (login, dashboard,
  project detail with hypothesis/critique workflow, experiment
  approval/execution UI, quantum lab).
- 54 backend tests, all passing; frontend type-checks clean.

**Failure encountered:** Attempted to bring up Postgres + Neo4j via
`docker compose` to run a real integration test. Docker Desktop's daemon
(virtual disk on `C:`) became unresponsive because `C:` had reached 0 bytes
free (a pre-existing condition on this machine, not caused by this project's
disk usage - the project itself lives on `D:`, which has ~170GB free).
`alembic revision --autogenerate` against a temp file literally failed with
`No space left on device`.

**Decision:** Per explicit user instruction, stopped all Docker usage for
the remainder of this session. Removed the Postgres/Neo4j containers,
volumes, and images that had already been pulled to return whatever space
could be reclaimed. Pivoted local dev/test to SQLite (ADR-008), keeping the
Postgres/Neo4j/Docker topology as the documented production path but marking
sandbox execution and knowledge-graph integration as
IMPLEMENTED - NOT VERIFIED rather than pretending they were exercised.

**Bugs found and fixed during self-testing (kept here, not hidden per
Section 75):**
- `passlib[bcrypt]==1.7.4` + `bcrypt>=4.1` incompatibility (bcrypt dropped
  the `__about__` attribute passlib probes for) - pinned `bcrypt==4.0.1`.
- `ExperimentConfigCreate` schema included `experiment_id`, which collided
  with the path-derived `experiment_id` kwarg when constructing the ORM
  object - excluded it from the dumped dict.
- Sandbox executor originally discarded `output/metrics.json` before the
  orchestrator could read it (workspace was deleted right after container
  teardown) - fixed by reading the bind-mounted output directory back before
  `shutil.rmtree`.
- `alembic`'s generated `env.py` didn't know about the app's models/settings
  - wired it to import `Base.metadata` and the real `DATABASE_URL`.

**Result:** Core pipeline (project → research question → hypothesis →
quality-check → critic → experiment config → critique → Gate 1 approval →
Gate 2 execution-attempt) verified end-to-end via
`test_full_research_pipeline_up_to_execution_gate`. Quantum module verified
with real Aer simulator runs showing Grover's expected advantage over random
guessing and a noisy run showing measurably lower success probability than
the ideal run. PQC classical benchmark verified with real timing
measurements (ECDSA signing faster than RSA signing, as expected).

**Next steps (proposed, awaiting researcher approval per Section 42):**
1. Free disk space on `C:` and re-verify the Docker sandbox + Postgres +
   Neo4j paths that are currently IMPLEMENTED - NOT VERIFIED.
2. Run Experiment 2 (Memory Ablation) and Experiment 3 (Critic Ablation)
   with a populated multi-experiment project.
3. Wire an LLM narrative pass onto the Gap Analyzer and Research Critic
   (currently deterministic-only) - requires `ANTHROPIC_API_KEY`.
4. Populate `datasets`/`dataset_versions` with a real registered dataset
   (currently hypotheses can be created with `dataset_id=None`, which the
   quality check correctly flags but nothing stops).
