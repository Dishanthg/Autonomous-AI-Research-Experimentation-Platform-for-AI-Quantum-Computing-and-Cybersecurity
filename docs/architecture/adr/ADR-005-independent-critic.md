# ADR-005: Independent, Deterministic-First Research Critic

## Status
Accepted, implemented (`app/services/critic/checklist.py`).

## Context
Section 30/31: a critic that shares context or an LLM call with the agent
that drafted a hypothesis/config tends to agree with it (the same biases
produced the draft). Section 31 also says: use deterministic code where LLM
reasoning isn't actually required.

## Decision
The critic's *first* pass is a deterministic structural checklist
(`critique_hypothesis`, `critique_experiment_config`) that runs with zero LLM
involvement and cannot be argued out of an objection: missing dataset,
zero/absent minimum-effect-size threshold, too few runs, missing metrics, and
missing pinned dataset version all fire regardless of what any LLM narrative
says. An optional LLM narrative critique (not yet implemented - see
FINAL_RESEARCH_AUDIT.md) would run afterward, in a separate call with no
shared conversation state with the drafting agent, and could only add
objections, never remove ones the checklist raised.

## Consequences
- The critic's core guarantee (a hypothesis with a `min_effect_size` of 0, or
  a config with `num_runs=1`, cannot pass) is auditable and doesn't depend on
  LLM behavior at all.
- Cost: the checklist only catches what it explicitly checks for; genuinely
  novel methodological problems still need a human reviewer or a future LLM
  pass.

## Verification status
IMPLEMENTED - VERIFIED. `test_critic.py` (5 tests) and the API integration
test both confirm blocking objections are raised correctly and that Gate 1
approval is refused while a blocking objection is open.
