# Failed Experiments and Attempts

Kept deliberately, per Section 75 ("include failed experiments").

1. **Docker Compose (Postgres + Neo4j) bring-up.** Succeeded initially
   (containers started, Postgres passed its healthcheck), but subsequent
   `alembic revision --autogenerate` failed outright with `No space left on
   device` — traced to the host `C:` drive being at 0 bytes free, which
   made Docker Desktop's daemon unresponsive/unreliable for the remainder of
   the session. Containers, volumes, and pulled images (`postgres:16-alpine`,
   `neo4j:5-community`) were removed to reclaim whatever space could be
   recovered. This is an environment failure, not a design failure, but it
   directly blocked verifying the Docker sandbox and Neo4j knowledge-graph
   paths in this session.
2. **First `ExperimentConfig` creation attempt** raised
   `TypeError: got multiple values for keyword argument 'experiment_id'`
   because the Pydantic request schema included `experiment_id` alongside
   the path parameter of the same name, and both were passed to the ORM
   constructor. Fixed by excluding it from the dumped payload
   (`app/api/v1/experiments.py`).
3. **bcrypt/passlib incompatibility.** `passlib[bcrypt]==1.7.4` probes
   `bcrypt.__about__.__version__`, which was removed in `bcrypt>=4.1`,
   causing every password-hash test to fail with
   `ValueError: password cannot be longer than 72 bytes...` (a misleading
   downstream symptom of the real incompatibility). Fixed by pinning
   `bcrypt==4.0.1`.
4. **Sandbox output retrieval bug** (caught before it shipped, not in
   production): the original executor implementation deleted the temp
   workspace directory before the orchestrator could read back
   `output/metrics.json`, which would have silently discarded every
   experiment's results. Fixed by reading the bind-mounted output directory
   before teardown.
5. **liboqs / post-quantum crypto**: not attempted to install in this
   environment given the disk-space constraint and the added complexity of
   compiling a native library; the PQC arm remains NOT_IMPLEMENTED rather
   than worked around with a fake measurement.
6. **(Session 2) Numeric-consistency regex false positive.**
   `ResearchSynthesizerAgent`'s number-extraction regex (`-?\d+\.?\d*%?`)
   matched a sentence-ending period after an integer (e.g. "a series of 3."
   was captured as the token "3."), which then failed the small-integer
   tolerance check and was incorrectly flagged as a possibly-invented
   number. Caught by `test_check_numeric_consistency_tolerates_small_prose_integers`
   failing on first run. Fixed by requiring a digit after the decimal point
   for a match to count as a decimal (`-?\d+(?:\.\d+)?%?`).
7. **(Session 2) Enabling the process-tier sandbox changed a test's
   expected outcome.** `test_full_research_pipeline_up_to_execution_gate`
   (session 1) asserted a `503 Sandbox unavailable` response, which was
   correct for that session's Docker-only configuration. Once
   `SANDBOX_BACKEND=process` was set in `backend/.env` (ADR-009), the same
   call started genuinely succeeding (200, `COMPLETED`), breaking that
   assertion. This was not a bug - it was the test correctly detecting that
   the system's real behavior had changed - so the test was rewritten
   (renamed `test_full_research_pipeline_end_to_end`) to assert on the new,
   better outcome, and a separate test was added
   (`test_execute_returns_503_when_docker_backend_unavailable`) to keep the
   original Docker-unavailable failure path covered.
