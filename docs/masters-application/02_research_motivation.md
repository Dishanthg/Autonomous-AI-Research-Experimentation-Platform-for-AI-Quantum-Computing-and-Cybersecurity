# Research Motivation

LLM-based research assistants are increasingly proposed for hypothesis
generation, literature review, and even experiment design — but the same
properties that make LLMs useful (fluent, confident generation) make them
dangerous in a scientific context: a fabricated citation and a real one read
identically; an unsupported conclusion and a well-evidenced one are stated
with the same tone.

This project treats "can AI meaningfully assist with research" as an
empirical question, not a premise. Rather than building the most impressive-
looking demo, the build prioritized structural mitigations that can be
independently tested: does tagging every claim with a provenance type
actually stop ungrounded claims from being displayed as fact (verified: see
`test_claim_extraction.py::test_extract_claims_rejects_ungrounded_span`)?
Does forcing statistics through a deterministic engine actually prevent an
LLM from asserting significance that isn't there (verified: the Conclusion
Engine takes no LLM input at all)? Does a mandatory two-gate approval flow
actually block unsandboxed execution (verified: the execute endpoint returns
503, never falls back)?

The motivation is explicitly methodological: build the mitigations, then
measure whether they hold under test, rather than assume they do.
