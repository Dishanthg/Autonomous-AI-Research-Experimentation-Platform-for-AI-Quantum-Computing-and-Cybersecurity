# Cybersecurity Domain Experiments

`app/services/codegen/cyber_templates.py` generates an intrusion-detection
comparison script: a rule-based static-threshold baseline vs. logistic
regression / random forest / a "graph-enhanced" random forest that adds a
synthetic fan-out-score feature correlated with attack traffic. Data is
synthetic and honestly labeled as such in the generated code's own
docstring - a simplified stand-in for a real IDS dataset (e.g.
CIC-IDS2017/NSL-KDD), not a claim about real network traffic.

**Update (session 2): VERIFIED end-to-end via the real HTTP API**, not just
the codegen level. `test_api_integration.py::test_full_research_pipeline_end_to_end`
runs the complete pipeline - hypothesis ("does graph-based representation
improve cybersecurity anomaly detection?"), quality check (correctly
flagged for missing `dataset_id`), a first config correctly rejected by the
critic (too few runs), a second, properly-specified config approved at both
gates, executed via the process-tier sandbox (ADR-009), and analyzed to a
real conclusion (SUPPORTED, p≈9.4e-11, Cohen's d≈12.46).

`backend/scripts/run_cyber_experiment.py` (Experiment 6, Section 66) ran
two further pairwise hypotheses (logistic_regression vs rule_based,
graph_enhanced_rf vs rule_based) - see
`research/cybersecurity/experiment_6_ids_comparison.json`.

**Caveat repeated deliberately:** the large effect sizes here (d > 12 in
one case) partly reflect that the synthetic data's "graph" feature was
constructed to be informative by design (a fan-out score correlated with
the attack label). This demonstrates the pipeline mechanics work
correctly end-to-end - it is not evidence that graph features help on real
network traffic, which would require a real IDS dataset (tracked in
`17_future_research.md`).

Every run in this section executed under `IsolationLevel.PROCESS_RESOURCE_LIMITED`
(ADR-009), correctly flagged by the Limitation Detector on every result.
