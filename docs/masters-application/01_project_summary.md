# Project Summary

ResearchMind-Q is an evidence-grounded AI research assistant platform spanning
three domains - AI, cybersecurity, and quantum computing - built to test
whether structural constraints (evidence provenance, deterministic statistics,
mandatory human approval gates, sandboxed execution, an independent critic)
can make an LLM-assisted research workflow trustworthy rather than merely
impressive.

The system implements: a research workspace (projects/questions/hypotheses),
a literature engine backed by the live arXiv API, a provenance model that
tags every claim with its evidentiary status, a Neo4j research knowledge
graph for gap detection, a deterministic hypothesis-quality checklist and
research critic (plus an LLM narrative layer that can only add to, never
remove, the critic's findings), an experiment planner with two human
approval gates, a two-tier sandbox (a Docker tier for arbitrary code, and a
resource-limited process tier - added specifically so this platform's own
reviewed templates can run to completion in a Docker-unavailable
environment, see ADR-009) with domain-specific code generation (AI model
comparison, cybersecurity intrusion detection), a deterministic statistical
engine (bootstrap CIs, Welch's t/Mann-Whitney, Cohen's d, Holm-Bonferroni),
a rule-based conclusion classifier, a Limitation Detector and Next-Experiment
Generator, a real Qiskit-based quantum module (Bell state, Grover search,
QFT, noise modeling), a real classical cryptography benchmark for
post-quantum-migration research, real Prometheus observability, and a
small multi-agent layer (hypothesis drafting, gap narration, critic
narration, research synthesis) built against an injectable LLM-provider
interface.

As of this writing, the full research pipeline - hypothesis through
statistically-analyzed, human-approved conclusion - runs end-to-end and
has produced real results in both the AI domain (two honest NOT_SUPPORTED
null findings on the Breast Cancer Wisconsin dataset) and the cybersecurity
domain (SUPPORTED findings on a synthetic, honestly-labeled dataset), plus
a verified reproduction of one experiment and two small real ablation
studies (memory duplicate-detection, critic-blocks-invalid-design). The
quantum and classical-cryptography modules are independently verified
against real computation. The Docker sandbox tier and the Neo4j
knowledge-graph integration remain implemented but not yet verified
against live instances, due to a disk-space constraint on the build
machine (see `FINAL_RESEARCH_AUDIT.md`); the LLM agent layer is unit-tested
against a fake provider but not yet run against a real model, since no API
key was available in this environment.
