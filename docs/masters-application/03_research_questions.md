# Research Questions

**Primary:** To what extent can an evidence-grounded AI research agent assist
with hypothesis generation, experiment design, execution and evaluation in
AI, cybersecurity and quantum computing while maintaining scientific
reproducibility and minimizing unsupported conclusions?

**Secondary:**
- RQ1: Can AI identify meaningful research gaps from a structured literature
  collection? *(infrastructure built — Neo4j gap queries — not yet run
  against live data; UNRESOLVED)*
- RQ2: Can AI generate testable, falsifiable hypotheses rather than vague
  research questions? *(the deterministic quality checklist is verified to
  correctly reject under-specified hypotheses — see
  `test_hypothesis_quality.py`; whether an LLM reliably produces
  quality-passing hypotheses unassisted is UNRESOLVED, since LLM-drafted
  hypothesis generation is NOT_IMPLEMENTED in this build)*
- RQ3: Can AI-generated experiments be executed reproducibly? *(codegen
  templates are deterministic and version-pinned; sandboxed reproduction
  itself is IMPLEMENTED — NOT VERIFIED)*
- RQ4: Does evidence grounding reduce unsupported claims? *(the provenance
  guard demonstrably rejects ungrounded claims at the unit level; a
  comparative experiment against an ungrounded baseline — Section 61 — has
  not been run; UNRESOLVED)*
- RQ5: Does an independent research critic improve experimental validity?
  *(the critic demonstrably blocks specific invalid configs — small sample
  size, zero effect-size threshold, missing metrics; a comparative ablation
  — Section 63/36 — has not been run; UNRESOLVED)*
- RQ6: Can AI research memory improve subsequent experiment design?
  *(query infrastructure built; ablation not run; UNRESOLVED)*
- RQ7: What research tasks remain unsafe/difficult to automate? *(partially
  answered by this build's own experience — see
  `14_failed_experiments.md` and `16_limitations.md`)*
- RQ8: Does AI-assistance effectiveness differ across domains? *(UNRESOLVED
  — no cross-domain comparative experiment run yet)*
