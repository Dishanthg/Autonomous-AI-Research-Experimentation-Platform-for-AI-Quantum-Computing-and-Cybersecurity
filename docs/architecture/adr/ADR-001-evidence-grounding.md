# ADR-001: Evidence Grounding for Every Scientific Claim

## Status
Accepted, implemented (`app/models/enums.py::ClaimType`, `app/services/literature/claim_extraction.py`).

## Context
LLMs fabricate citations and results with the same confident tone as real ones. A
research platform that lets an LLM assert "Method X outperformed Method Y" without
a traceable source is not measurably different from a chatbot with good style.

## Decision
Every claim surfaced by the system is tagged with exactly one `ClaimType`:
`REPORTED_IN_LITERATURE | AI_INFERRED | HYPOTHESIZED | SIMULATED |
EXPERIMENTALLY_OBSERVED | HUMAN_VERIFIED` (Rule 11). `EXPERIMENTALLY_OBSERVED`
claims carry a non-null `run_id` foreign key - a DB-level fact, not a UI
convention. Literature claim extraction additionally requires the extracted
`source_span` to literally appear in the source abstract; a claim whose span
can't be found in the original text is dropped, not accepted on the model's
say-so (see `test_claim_extraction.py::test_extract_claims_rejects_ungrounded_span`).

## Consequences
- The Result Analyzer / Statistical Analyst are the only code path allowed to
  write numeric `Metric`/`StatisticalTest` rows (no LLM call appears in that
  module) - see ADR-006.
- Claim extraction over untrusted paper text is prompt-injection-hardened
  (delimited, no tool access) - see the Literature Engine section of the
  architecture document.
- Cost: extra plumbing (every claim needs a type + evidence chain) instead of
  letting the LLM narrate freely.

## Verification status
IMPLEMENTED - VERIFIED (`app/tests/test_claim_extraction.py`, 4 tests passing
against a fake LLM provider double; real Anthropic-backed extraction is
IMPLEMENTED - NOT VERIFIED since no API key was configured in this build
environment).
