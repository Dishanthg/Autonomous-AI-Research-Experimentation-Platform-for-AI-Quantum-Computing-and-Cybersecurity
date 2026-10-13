# Hypotheses (H1-H7)

All seven hypotheses from the project spec remain formally **UNRESOLVED**
in the sense of a proper, large-scale ablation study - none has been tested
across enough trials to support a general claim. But two now have a real,
if small, first data point (session 2), and a third has strong procedural
support:

**H3 (an independent critic improves experimental validity):** real
evidence. `research/ablations/critic_ablation.json` constructs a
deliberately flawed hypothesis/config (no dataset, no baseline, zero
minimum-effect-size threshold, `num_runs=1`, no metrics requested) and runs
it through the platform's actual `critique_hypothesis`/
`critique_experiment_config` code. With the critic active: 4 hypothesis
objections + 2 config objections, `would_be_approved: false`. Modeled
"critic off" (i.e. what would happen if that check were skipped, as it
would be if removed from `api/v1/experiments.py`): `would_be_approved:
true`. n=1 constructed scenario - directional evidence for H3, not proof.

**H2/H6 (memory improves plan consistency / reduces duplicate effort):**
real evidence. `research/ablations/memory_ablation.json` populates a real
project with two experiments proposing the identical (domain, baseline,
proposed) combination, then calls `services.memory.queries.find_duplicate_experiment`
- the actual production function - with `enabled=True` vs `enabled=False`.
With memory: the duplicate is detected before execution. Without: it is
not. n=1 duplicate scenario in one project - directional evidence, not a
population-level duplicate-rate measurement.

**H5 (human approval reduces unsafe/invalid experimental actions):**
procedural evidence, now stronger than session 1's. The full pipeline test
(`test_api_integration.py::test_full_research_pipeline_end_to_end`) shows
a first, under-specified config (num_runs=1) correctly rejected by the
critic before Gate 1, then a properly-specified second config passing
Gate 1 and Gate 2 to real execution. A separate test
(`test_execute_returns_503_when_docker_backend_unavailable`) confirms
execution cannot proceed by falling back to an unsandboxed path when the
primary (Docker) backend is unavailable.

**H1, H4, H7** remain untested by a dedicated experiment. H4
(sandboxing increases reproducibility) has partial support from the
reproducibility run in `reproducibility/experiment-f88e9566/` (same seed,
same codegen template → identical F1/PR-AUC/false-positive-rate metrics on
reproduction; only wall-clock timing metrics showed natural variance,
correctly flagged as `DEVIATION` rather than silently treated as a match),
but that is one reproduction of one experiment, not a study of
reproducibility rates across many.

Registering and lightly testing a hypothesis is still not the same as
resolving it at the standard the spec asks for (Section 70's full ablation
studies) - see `12_ablation_studies.md` for the honest scope of what was
and wasn't run.
