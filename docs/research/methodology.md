# Research Methodology

This document describes the methodological commitments that distinguish
this platform from a demo that merely looks like a research tool. See
`docs/masters-application/07_experimental_methodology.md` for the
experiment-level version; this document is the platform-wide version.

## Pre-registration
Every hypothesis fixes its `decision_rule` (metric, alpha, minimum effect
size, expected direction) at creation time, before any experiment using it
runs. The Conclusion Engine (`app/services/statistics/conclusion.py`)
evaluates strictly against that stored rule - there is no code path that
lets a rule be edited after a result exists to make a borderline finding
look better.

## Falsifiability as a gate, not a suggestion
The Hypothesis Quality Check (`app/services/hypothesis/quality_check.py`)
mechanically verifies eight properties (testability, specificity,
measurability, falsifiability, dataset availability, experimental
feasibility, baseline availability, confounders considered) and a
hypothesis scoring below threshold cannot be marked `QUALITY_CHECKED` - a
status the state machine requires before critique and approval can proceed.

## Independent critique before trust
The Research Critic's deterministic checklist (`app/services/critic/checklist.py`)
runs on every hypothesis and config, with zero shared context with whatever
process (human or LLM) drafted them - see ADR-005. A blocking objection
cannot be waived by re-running the same critique; it requires either fixing
the underlying flaw or an explicit, audit-logged human override for that
specific objection (an override path exists at the `ResearchDecision` model
level - `DecisionOutcome.ACKNOWLEDGED_OVERRIDE` - though no API endpoint
currently exposes it for critic objections specifically; see
`docs/masters-application/17_future_research.md`).

## Statistics separated from narrative
`app/services/statistics/engine.py` and `conclusion.py` never import an LLM
provider. The choice between a parametric (Welch's t) and non-parametric
(Mann-Whitney U) test is itself decided deterministically by a Shapiro-Wilk
normality check, not left to judgment. Confidence intervals are
bootstrap-based (5000 resamples, fixed seed for reproducibility of the CI
itself, not just the underlying experiment).

## Limitation detection as a standing check, not an afterthought
Every analyzed experiment is run through `app/services/limitations/detector.py`,
which mechanically flags small sample sizes, missing dataset version pins,
low resource limits, single-metric evaluation, and reduced-isolation
sandbox execution. These findings are stored (`limitations` table) and
surfaced in the API/reports alongside the result they apply to - a
SUPPORTED conclusion is never displayed without its limitations attached.

## What this methodology does not claim
It does not claim the platform's hypotheses are *interesting* or its
experiments are *well-designed research questions* - a human or an LLM can
still propose a well-formed but scientifically uninteresting hypothesis,
and the checklist will happily pass it. Methodological rigor (this
document) and scientific judgment (still substantially a human
responsibility in this build - see `docs/masters-application/16_limitations.md`)
are different things.
