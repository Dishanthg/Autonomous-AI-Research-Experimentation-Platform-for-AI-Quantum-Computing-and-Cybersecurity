# Limitations

- **LLM hallucination**: not eliminated, only structurally constrained. The
  four agents in `app/agents/` (hypothesis drafting, gap narration, critic
  narration, research synthesis) each enforce a specific structural
  guardrail (fixed vocabulary, evidence-only confidence, add-only
  objections, numeric-consistency checking) but are unit-tested only
  against a fake LLM provider double - **none has been run against a real
  model in this build** (no `ANTHROPIC_API_KEY` was available), so their
  behavior against genuine LLM output/failure modes remains unverified.
- **Retrieval coverage**: only arXiv is wired; Semantic Scholar and Crossref
  are not, so literature coverage is narrower than the spec envisions.
- **Dataset bias**: the cybersecurity codegen template uses synthetic data
  constructed so its "graph-enhanced" feature is informative by design — any
  result from it says nothing about real network traffic. The AI-domain
  experiment used a real dataset (`breast_cancer`) but a small `num_runs`
  (10), which the Limitation Detector itself correctly flags on every run.
- **Sandbox verification gap**: the Docker Tier 1 sandbox execution path is
  implemented but has not been run to completion against a live container in
  this environment (disk-space incident) — this is the single largest
  verification gap in the current build. A second, reduced-isolation
  process tier (ADR-009) was added and IS verified, but it provides weaker
  guarantees (no network isolation, no cross-platform resource cgroup
  enforcement) and is explicitly restricted to this platform's own reviewed
  codegen templates, never arbitrary code - every result produced under it
  is labeled `PROCESS_RESOURCE_LIMITED` and flagged by the Limitation
  Detector, never presented as equivalent to a Docker-tier result.
- **Knowledge graph verification gap**: same root cause: Neo4j gap-detection
  queries are written but unverified against live data.
- **Ablation scope**: the two ablations run in session 2 (memory,
  critic) are each a single constructed scenario (n=1), demonstrating the
  mechanism works as designed, not a population-level measurement of
  duplicate-experiment rates or critic hit rates in general.
- **Compute**: quantum experiments are limited to small qubit counts (Aer
  simulator, tested up to 3-6 qubits) — no claim about scaling behavior.
- **Statistical**: bootstrap CIs and Cohen's d are appropriate for the small
  (n<20) run counts used here, but no experiment in this build has yet used
  a large enough `num_runs` to distinguish a small real effect from noise
  with high confidence.
- **Human-approval dependence**: by design (Section 7), throughput is
  bounded by researcher availability — this is treated as a feature, not
  measured as a limitation.
- **Generalization**: every finding in this document is scoped to this one
  build session on one machine; no claim of external validity is made.
