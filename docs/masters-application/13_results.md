# Results

Real, verified results (all reproducible - see commands at the bottom of
`FINAL_RESEARCH_AUDIT.md`; no external services required).

## Test suite
87/87 backend tests passing (54 from session 1, ~33 added in session 2:
sandbox refactor, limitations/next-experiment generators, agent layer,
observability), zero regressions.

## Full-pipeline execution (new in session 2)
With the process-tier sandbox (ADR-009) enabled, the complete research
pipeline now executes for real via the HTTP API - not just up to an
approval gate. `test_full_research_pipeline_end_to_end` exercises: register
→ login → project → research question → hypothesis (correctly flagged for
missing dataset by the quality check) → experiment → a first config
correctly rejected by the critic (num_runs too small) → a second config
approved (Gate 1) → executed (Gate 2) → COMPLETED with a real conclusion,
real statistics, real limitations, and real next-experiment proposals.

## Domain experiment results (real, from `research/`)

| Experiment | Comparison | Conclusion | p-value | Effect size |
|---|---|---|---|---|
| Demo (cybersecurity) | graph_enhanced_rf vs rule_based | **SUPPORTED** | 9.4e-11 | d=12.46 |
| Experiment 6 arm 1 | logistic_regression vs rule_based | SUPPORTED | see `research/cybersecurity/experiment_6_ids_comparison.json` | — |
| Experiment 6 arm 2 | graph_enhanced_rf vs rule_based | SUPPORTED | ″ | — |
| Experiment 5 arm 1 | random_forest vs logistic_regression (breast_cancer) | **NOT_SUPPORTED** | 0.528 | d=0.29 |
| Experiment 5 arm 2 | xgboost vs logistic_regression (breast_cancer) | **NOT_SUPPORTED** | 0.067 | d=0.88 |

The two NOT_SUPPORTED results are deliberately kept and reported as-is: at
only 10 runs, neither tree-based method's improvement over logistic
regression on the (fairly easy) Breast Cancer Wisconsin dataset cleared the
pre-registered significance threshold. This is the Conclusion Engine
working as designed (ADR-006) - it does not inflate a borderline,
non-significant result into a positive finding. `research/tables/ai_experiment_5_comparison.md`
has the full table.

## Quantum results (real Aer simulator runs)
- Bell state: 00/11 split within [0.4, 0.6] over 4000 shots.
- Grover search (n=4 qubits, marked state `1011`): 96.4% measured success
  probability vs. a 6.25% random-guessing baseline (>15x).
- Noisy Grover (depolarizing error rate 0.02): success probability dropped
  to 13.7% - see `research/figures/quantum_grover_success_probability.png`.

## PQC results (real timing measurements, classical arm)
ECDSA-P256 sign/verify/keygen all measured faster than RSA-2048's - see
`research/tables/pqc_classical_benchmark.md`. Post-quantum (ML-KEM/ML-DSA)
arm remains NOT_IMPLEMENTED (liboqs not installed in this environment) -
never fabricated in its place.

## Reproducibility (real, new in session 2)
`reproducibility/experiment-f88e9566/reproduction_report.json`: re-executed
the cybersecurity demo experiment's approved config with the same seed.
Every accuracy-type metric (F1, PR-AUC, false-positive rate) matched
exactly; only wall-clock timing metrics (train_time_ms std) showed natural
variance, correctly flagged `DEVIATION` rather than silently passed. The
conclusion status matched (`SUPPORTED` both times).

## Ablations (real, small-scale, new in session 2)
See `12_ablation_studies.md` and `04_hypotheses.md`.

## What this project still does NOT have
A completed grounding ablation (Experiment 1), a completed human-AI
collaboration study (Experiment 4), a large-scale (n>1) version of the
memory/critic ablations, any result produced through the fully-isolated
Docker sandbox tier, or any gap-analysis result from a live knowledge
graph.
