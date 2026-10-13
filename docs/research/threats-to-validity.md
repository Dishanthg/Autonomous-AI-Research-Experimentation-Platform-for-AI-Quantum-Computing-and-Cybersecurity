# Threats to Validity

Section 98. This document applies the standard experimental-design
validity taxonomy (internal / external / construct / statistical
conclusion) to ResearchMind-Q's own empirical claims - it is a different
lens than `docs/masters-application/16_limitations.md` (a flat list of
what's unverified or missing) and should be read alongside it, not instead
of it. Every threat below is scoped to the actual experiments that have
been run (`research/ai/`, `research/cybersecurity/`, `research/quantum/`,
`research/pqc/`), not to hypothetical future ones.

## 1. Internal validity

Internal validity asks: within an experiment that *was* run, is the
observed effect actually caused by the manipulated variable, or by some
confound?

- **Cybersecurity codegen's synthetic fan-out feature is informative by
  construction.** `app/services/codegen/cyber_templates.py::make_synthetic_traffic`
  generates a `fanout` feature drawn from `Normal(3.0, 1.0)` for the attack
  class and `Normal(0.5, 0.5)` for the benign class *before* the
  graph-enhanced arm ever sees it. Any SUPPORTED conclusion for
  "graph-enhanced RF outperforms rule-based" (see
  `research/cybersecurity/experiment_6_ids_comparison.json`) is therefore
  partly a restatement of how the synthetic generator was built, not
  independent evidence that graph-based representations help on real
  network traffic. This is flagged elsewhere as a dataset-bias limitation;
  framed as an internal-validity threat, the risk is specifically that the
  causal story ("graph features cause better detection") is confounded
  with ("the generator was constructed so a graph-adjacent feature
  correlates with the label").
- **Shared random seeds across arms remove one confound but not all.**
  `base_seed` is fixed per experiment and each per-run seed
  (`base_seed + i`) is shared between the baseline and proposed arm within
  a run (see `ai_templates.py`, `cyber_templates.py`,
  `quantum_runner.py`), so train/test splits and data draws are identical
  across arms - this correctly isolates the *method* as the manipulated
  variable. It does **not** control for hyperparameter selection: baseline
  and proposed models use their library defaults (e.g. scikit-learn's
  default `RandomForestClassifier`/`LogisticRegression` parameters), so an
  observed effect could partly reflect default-hyperparameter mismatch
  rather than a genuine method difference.
- **Quantum noise ablation (Experiment 8) uses one noise model at one
  error rate.** The ideal-vs-noisy comparison
  (`research/quantum/experiment_8_noise_ablation.json`) isolates "noise
  present vs. absent" cleanly (same circuit, same seed, same shots), but
  the *specific* depolarizing-error model and rate (0.05) is a modeling
  choice (`app/quantum/runner.py::build_depolarizing_noise_model`), not a
  measured property of any real device - the internal validity of "noise
  reduces success probability" is solid for *this* noise model, but should
  not be read as validating the magnitude for real quantum hardware noise.
- **PQC signing-latency comparison (Experiment 9) times single-threaded,
  single-process operations only.** No control for OS scheduler
  interference, thermal throttling, or background process load on the
  build machine; the mitigation is measuring `num_runs` (10-30)
  independent draws rather than a single timing, which the statistics
  engine's confidence interval already reflects.

## 2. External validity

External validity asks: do findings generalize beyond this specific
experimental setup?

- **Synthetic datasets dominate the cybersecurity domain.**
  `synthetic_traffic_v1` (now a registered `DatasetVersion`, see
  `research/datasets/README.md`) is explicitly a simplified stand-in for
  real IDS traffic (e.g. CIC-IDS2017/NSL-KDD) - no cybersecurity finding in
  this build generalizes to real network traffic.
- **Single real dataset in the AI domain.** `breast_cancer` (569 rows) is
  the only real dataset exercised end-to-end so far (Experiment 5); a
  finding on one small, well-separated binary-classification dataset does
  not generalize to other AI tasks, dataset sizes, or class-imbalance
  regimes.
- **Single-machine, single-session execution.** Every result in
  `research/` was produced on one development machine, in a small number
  of build sessions, under the process-tier sandbox (ADR-009) rather than
  the fully-isolated Docker tier. Timing-sensitive metrics
  (`latency_ms`, `sign_latency_seconds`, quantum `execution_time_seconds`)
  in particular may not transfer to different hardware, OS, or container
  environments.
- **Small `num_runs` throughout.** Every experiment run so far uses
  `num_runs` between 5 and 30 (the Limitation Detector's own
  `MIN_ROBUST_SAMPLE_SIZE` threshold is 30) - conclusions are about *this*
  sample, and the width of the reported confidence intervals should be
  read as part of the finding, not a footnote to it.
- **Quantum results are simulator-only.** Every `QuantumRun` row is
  labeled `backend_type=SIMULATOR` (`app/models/enums.py::BackendType`) by
  construction - there is no hardware wiring in this build (Section 27/59)
  - so no quantum finding generalizes to real NISQ-era hardware, which has
  qualitatively different (and much larger) noise characteristics than the
  depolarizing model used here.
- **PQC comparison is classical-only in this environment.**
  `research/pqc/experiment_9_classical_signing_latency.json` compares
  RSA-2048 vs. ECDSA-P256 only; liboqs/oqs-python is not installed here, so
  no finding about genuine post-quantum schemes (ML-KEM, ML-DSA) has been
  produced - the execution path supports it
  (`app/services/execution/pqc_runner.py`) and is unit-tested against the
  "unavailable" case, but the post-quantum arm itself remains
  NOT_IMPLEMENTED in this environment.

## 3. Construct validity

Construct validity asks: does the thing actually measured
(`conclusion_status`, a metric name, a decision rule) capture the
theoretical construct the research question is really about?

- **`ConclusionStatus` measures statistical rigor against a pre-registered
  rule, not research importance or novelty.** SUPPORTED means "the
  pre-registered decision rule's significance and effect-size thresholds
  were met on this run" (`app/services/statistics/conclusion.py`) - it
  says nothing about whether the underlying question was worth asking, or
  whether the result is novel relative to prior literature. A trivial,
  well-known effect (e.g. ECDSA signing is faster than RSA signing,
  Experiment 9) can be SUPPORTED with an extremely small p-value while
  contributing nothing new to the field. The platform does not conflate
  these two things in its own output (the conclusion is always paired with
  its rationale and the specific metric/decision rule that produced it),
  but a downstream reader could still make that conflation if the
  conclusion label is quoted out of context.
- **A single evaluation metric under-represents "performance."** Several
  experiments request only one `metrics_requested` entry (flagged by the
  Limitation Detector's own `measurement_limitation` category) - e.g. an F1
  or success-probability comparison says nothing about calibration,
  latency/throughput trade-offs, or worst-case behavior, all of which are
  part of what "a better method" usually means in practice.
- **Cohen's d as the universal effect-size measure.** `compare_two_groups`
  (`app/services/statistics/engine.py`) reports Cohen's d for every metric
  regardless of its underlying distribution or scale (e.g. a 0-1 bounded
  probability like `success_probability`, vs. an unbounded latency in
  seconds) - Cohen's d's standard interpretation bands (0.2/0.5/0.8 =
  small/medium/large) were derived for roughly-normal, unbounded outcome
  measures and may not carry the same practical meaning for a bounded
  proportion metric.
- **"Isolation level" is a security/reproducibility construct, not a
  performance one, but shares columns with performance data.** A
  `PROCESS_RESOURCE_LIMITED` run's `resource_usage`/timing fields are
  honestly labeled as not cgroup-enforced (Limitation Detector's
  `sandbox_isolation_limitation`), which is the correct construct-validity
  mitigation: the label prevents a `DOCKER`-tier and
  `PROCESS_RESOURCE_LIMITED`-tier latency number from being silently
  treated as the same construct ("resource-constrained execution time").

## 4. Statistical conclusion validity

Statistical conclusion validity asks: given the data actually collected, is
the statistical inference itself sound?

- **Small n throughout (5-30 per arm).** Every experiment in `research/`
  falls below the Limitation Detector's own 30-run "stable effect-size
  estimate" threshold except Experiment 9 (`num_runs=30`, right at the
  boundary) - `sample_limitation` is correctly flagged on every other run.
  Small n inflates the variance of the effect-size estimate itself: two
  re-runs with different seeds could plausibly produce visibly different
  Cohen's d point estimates even though the underlying data-generating
  process hasn't changed.
- **Effect sizes and CIs are reported, partially mitigating the bare
  p-value problem** - `StatisticalTest` always carries `effect_size`,
  `ci_lower`/`ci_upper` alongside `p_value`
  (`app/services/statistics/engine.py`), and `evaluate_hypothesis`
  requires *both* significance *and* a minimum pre-registered effect size
  before returning SUPPORTED - this is a real mitigation, not just a
  reported number nobody reads. It does not, by itself, fix the small-n
  variance problem above.
- **No multiple-comparisons correction across sibling experiments.**
  `StatisticalTest.correction_method` exists as a column but has never
  been populated (`grep -rn "correction_method" app/services/` finds only
  the model/schema declaration) - Experiment 5 runs two comparisons
  (random_forest vs. LR, xgboost vs. LR) against the same baseline without
  a Bonferroni/Holm adjustment across them. At two comparisons the risk is
  modest, but this does not scale safely if a future session runs many
  pairwise comparisons against a shared baseline without addressing it.
- **Welch's t-test / Mann-Whitney U selection is automatic, not manually
  verified per experiment.** `compare_two_groups`
  (`app/services/statistics/engine.py`) picks a test based on a
  distributional check on the actual sample, which is the right
  deterministic default, but has not been manually spot-checked against
  every individual experiment's realized sample shape in this session -
  the "which test ran" field (`test_name` on `StatisticalTest`) is at
  least always recorded, so this is independently auditable rather than a
  hidden assumption.
- **Extremely large effect sizes on some runs are a real result, not a
  computation error, but warrant scrutiny.** Experiment 7's
  Grover-vs-random comparison reports Cohen's d ≈ 131 (see
  `research/quantum/experiment_7_grover_vs_classical.json`) - this is
  expected for two success-probability distributions with near-zero
  variance and a large mean gap (a near-deterministic quantum circuit vs.
  a `1/8` classical baseline), not a statistical-conclusion validity bug,
  but such an extreme value would ordinarily prompt a check for a
  degenerate-variance failure mode; documenting it here is that check.

## Where this leaves the platform's own claims

None of the above invalidates a `SUPPORTED`/`NOT_SUPPORTED`/`INCONCLUSIVE`
label as *a correct computation given its inputs* - every conclusion in
`research/` is a real, reproducible function of real data
(`FINAL_RESEARCH_AUDIT.md`'s honesty checks hold). What these threats
constrain is how far each conclusion can be read: as evidence about *this*
dataset, *this* seed range, *this* sample size, and *this* pre-registered
decision rule - not as a general claim about the method, the domain, or
(for quantum/PQC) real hardware. Section 42's Next-Experiment Generator
proposals (`test_generalization`, `test_robustness`, `ablation`) exist
specifically to narrow these threats incrementally, one experiment at a
time, rather than asking a single run to bear more evidential weight than
its design supports.
