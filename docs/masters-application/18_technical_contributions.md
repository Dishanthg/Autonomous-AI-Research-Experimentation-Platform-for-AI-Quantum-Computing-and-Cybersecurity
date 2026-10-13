# Technical Contributions

Per Section 96, contributions are claimed only where evidence supports them:

- **System contribution**: a working, tested reference implementation of an
  approval-gated, evidence-tagged research pipeline with a deterministic
  statistics/conclusion layer fully decoupled from any LLM call — verified
  by 54 passing tests including one full pipeline integration test.
- **Methodological contribution**: the memory-ablation design pattern (a
  single `enabled` flag shared by the exact same query code path, rather
  than two separately-implemented "with memory"/"without memory" code
  paths) is a small but genuine methodological choice that removes an
  entire class of confound from that planned ablation.
- **Reproducibility contribution**: demonstrating that a research platform
  with this scope can run its entire core-pipeline test suite against local
  SQLite with zero external services, making the correctness of the
  approval-gate/statistics/quantum logic independently verifiable by anyone
  without provisioning Postgres/Neo4j/Docker - and a real, working
  reproducibility package generator (`scripts/reproduce_experiment.py`)
  that diffs a re-run's metrics against the original per-metric, rather
  than asserting reproducibility as a property of the system.
- **Security-engineering contribution (ADR-009)**: a two-tier sandbox
  design that lets a platform keep its Docker-only security guarantee for
  arbitrary/LLM-authored code while still being exercisable end-to-end on
  a machine where Docker is temporarily unavailable, without weakening
  that guarantee - achieved via a capability flag (`caller_declares_trusted_template`)
  that only the orchestrator can set, never a caller-supplied value reachable
  from the API. This is a specific, generalizable pattern (not unique to
  this project) for the common real-world situation of "the sandbox we want
  in production isn't available in this dev/CI environment."
- **Prompt-safety contribution**: `ResearchSynthesizerAgent`'s numeric-
  consistency checker is a small, concrete mechanism (not just a prompt
  instruction) for catching a class of LLM report-writing hallucination -
  a number in generated prose that doesn't trace back to any fact it was
  given - verified against constructed adversarial cases in `test_agents.py`.

No benchmark contribution, no novel ML/quantum-algorithmic contribution, and
no human-AI-interaction finding is claimed — none of those have supporting
completed experiments in this build. The ablation results in
`12_ablation_studies.md` are real but small (n=1 constructed scenarios),
not population-level findings.
