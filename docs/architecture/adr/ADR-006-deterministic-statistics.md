# ADR-006: Deterministic Statistical Engine and Conclusion Rule

## Status
Accepted, implemented (`app/services/statistics/engine.py`, `conclusion.py`).

## Context
Rule 4: never claim a hypothesis was supported without actual experimental
evidence. An LLM asked "was H1 supported?" will answer fluently regardless of
whether the underlying numbers justify it.

## Decision
- All descriptive stats, effect sizes (Cohen's d), hypothesis tests
  (Welch's t-test or Mann-Whitney U, chosen by a deterministic Shapiro-Wilk
  normality check - not LLM judgment), bootstrap confidence intervals, and
  Holm-Bonferroni correction are computed by `numpy`/`scipy` in
  `services/statistics/engine.py`. No LLM call exists anywhere in this file.
- `services/statistics/conclusion.py::evaluate_hypothesis` classifies a result
  as `SUPPORTED` / `NOT_SUPPORTED` / `INCONCLUSIVE` using ONLY the
  hypothesis's pre-registered `decision_rule` (metric, alpha, min effect
  size, direction) fixed before the experiment ran, and the computed
  `ComparisonResult`. An LLM may narrate the rationale text afterward but
  cannot change the classification.
- `Result`/`Metric`/`StatisticalTest` rows are written exclusively by
  `services/execution/analysis.py`, which imports only the statistics engine
  and no LLM provider.

## Consequences
- A hypothesis cannot be marked SUPPORTED by a persuasive-sounding LLM
  response; it requires a real effect that clears a pre-registered bar.
- Directionality is checked explicitly: `test_conclusion_engine_wrong_direction_not_supported`
  confirms a "proposed" arm doing *worse* than baseline is classified
  `NOT_SUPPORTED`, not silently ignored.

## Verification status
IMPLEMENTED - VERIFIED. `test_statistics_engine.py` (8 tests: descriptive
stats, effect size sanity checks, real-difference detection, no-spurious-
effect, Holm-Bonferroni conservatism, and all three conclusion outcomes).
