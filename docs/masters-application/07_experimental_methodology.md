# Experimental Methodology

Every experiment in this platform follows the same pipeline, enforced as a
state machine (`ExperimentStatus`): `DRAFT → PLANNED → PENDING_APPROVAL →
APPROVED → CODE_GENERATED → PENDING_EXECUTION_APPROVAL → RUNNING →
COMPLETED|FAILED → ANALYZED → CRITIQUED → CONCLUDED`.

Key methodological commitments, each backed by a specific code path:

1. **Pre-registration.** A hypothesis's `decision_rule` (metric, alpha,
   minimum effect size, expected direction) is fixed at hypothesis-creation
   time, before any experiment runs. The Conclusion Engine
   (`services/statistics/conclusion.py`) evaluates strictly against this
   pre-registered rule — it cannot be adjusted post-hoc to fit a result.
2. **Immutable configs.** `ExperimentConfig` rows are versioned, never
   edited in place; a "change" creates a new version (`version` increments),
   so any stored result traces to the exact config that produced it.
3. **Two human gates.** Configuration approval (Gate 1) requires the
   deterministic critic to have no unresolved blocking objection. Execution
   (Gate 2) is itself a separate, audit-logged authenticated action.
4. **Deterministic analysis.** Statistics and the SUPPORTED/NOT_SUPPORTED/
   INCONCLUSIVE classification are computed by `scipy`/`numpy` code with no
   LLM involvement (see ADR-006).
5. **Multi-run design.** Experiment configs specify `num_runs`; the critic
   flags configs with fewer than 3 runs as insufficient for a stable
   statistical estimate.

This methodology has been exercised end-to-end for one experiment
(cybersecurity intrusion-detection template, rule-based vs. graph-enhanced
Random Forest) up through the execution-approval gate; sandboxed execution
itself is IMPLEMENTED — NOT VERIFIED in this environment (see
FINAL_RESEARCH_AUDIT.md).
