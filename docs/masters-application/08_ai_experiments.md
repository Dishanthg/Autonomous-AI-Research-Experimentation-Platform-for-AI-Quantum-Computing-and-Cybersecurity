# AI Domain Experiments

`app/services/codegen/ai_templates.py` generates a model-comparison script
(baseline vs. proposed, e.g. logistic regression vs. random forest/XGBoost/
MLP) over either a synthetic (`make_classification`) or a real bundled
sklearn dataset (breast cancer, digits), measuring F1, PR-AUC, per-sample
latency, and training time across `num_runs` seeded repetitions.

**Update (session 2): now VERIFIED end-to-end, not just at the codegen
level.** `backend/scripts/run_research_pipeline.py` (Experiment 5, Section
65) ran two real hypotheses through the complete pipeline - quality-check,
critic, both approval gates, execution via the process-tier sandbox
(ADR-009), statistical analysis, limitation detection - on the real
`breast_cancer` dataset:

| Proposed | vs. Baseline | Conclusion | p-value | Cohen's d |
|---|---|---|---|---|
| random_forest | logistic_regression | NOT_SUPPORTED | 0.528 | 0.29 |
| xgboost | logistic_regression | NOT_SUPPORTED | 0.067 | 0.88 |

Both are honest null results at n=10 runs - reported as-is, not
re-run with different seeds until something "worked." See
`research/ai/experiment_5_model_comparison.json` and
`research/tables/ai_experiment_5_comparison.md`.

**Still not run:** the synthetic-classification codegen path (verified at
the unit-test level in `test_codegen.py` but not carried through a full
pipeline execution this session) and any MLP-based comparison.
