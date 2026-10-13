# Future Research

Directly follows from `FINAL_RESEARCH_AUDIT.md`'s NOT_IMPLEMENTED /
NOT VERIFIED rows, in priority order (updated after session 2):

1. Free disk space / use a machine with a healthy system drive; re-verify
   the Docker sandbox and Neo4j knowledge-graph integrations end-to-end.
2. Provide a real `ANTHROPIC_API_KEY` and re-verify the four agents
   (`app/agents/`) against an actual model - they are currently unit-tested
   only against a fake provider double.
3. Run a proper, larger-n version of the memory and critic ablations
   (session 2 ran one real but small scenario each - see
   `docs/masters-application/12_ablation_studies.md`), and complete
   Experiments 1 and 4 (grounding and human-AI collaboration ablations),
   which need a real LLM key and/or human participants respectively.
4. Add a real dataset registry (`datasets`/`dataset_versions` rows) so
   hypotheses stop being creatable with `dataset_id=None` in the first
   place, rather than relying on the quality check to catch it after the
   fact - this is the single most common Limitation Detector finding across
   every experiment run so far.
5. Install liboqs and complete the PQC comparison (Experiment 9 / Section 69)
   with a real post-quantum arm.
6. Run the AI/cybersecurity experiments against real (not synthetic)
   datasets to get findings that generalize beyond this platform's own
   demonstration - see the caveats in
   `docs/masters-application/09_cybersecurity_experiments.md`.
7. Add a `DecisionOutcome.ACKNOWLEDGED_OVERRIDE` API endpoint so a human can
   formally override a specific critic objection with a recorded rationale,
   rather than only being able to fix the underlying flaw (the model-level
   support already exists - see `docs/research/methodology.md`).
8. Build the remaining 13 UI pages (Literature, Knowledge Graph, Gaps,
   Reproducibility, Timeline, Statistical Analysis detail, etc.) - Dashboard,
   Project Detail, Experiment Approval, Quantum Lab, and Audit Log now exist.
9. Verify the production Docker Compose topology (Postgres + Neo4j +
   Docker-sandboxed backend) end-to-end once disk space allows.
