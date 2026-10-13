# Baseline Registry (observed in this database)

Baselines actually used by experiments recorded so far - drawn from the fixed, reviewed vocabulary in `app/services/codegen/{ai,cyber}_templates.py` (Section 16 - baselines are never invented ad hoc by an LLM).

| Baseline | Compared Against |
|---|---|
| rule_based | graph_enhanced_rf |
| logistic_regression | random_forest |
| logistic_regression | xgboost |
| rule_based | logistic_regression |
