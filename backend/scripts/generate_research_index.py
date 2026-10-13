"""Generates index/registry markdown files under research/ by querying the
REAL database state (whatever projects/hypotheses/experiments/results exist
after running run_demo.py / run_research_pipeline.py / run_cyber_experiment.py
/ the ablation scripts) - not hand-authored placeholder content.

Usage: python -m scripts.generate_research_index
"""

import sys

from app.models.experiment import Experiment, ExperimentConfig
from app.models.hypothesis import Hypothesis
from app.models.project import Project
from app.models.result import Result
from scripts._pipeline import RESEARCH_DIR, ensure_schema, get_session


def _write(relative_path: str, lines: list[str]) -> None:
    path = RESEARCH_DIR / relative_path
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"wrote {path}")


def generate_projects_index(db) -> None:
    projects = db.query(Project).order_by(Project.created_at).all()
    lines = [
        "# Projects Index",
        "",
        f"{len(projects)} project(s) recorded in the database.",
        "",
        "| ID | Title | Domain | Created (UTC) |",
        "|---|---|---|---|",
    ]
    for p in projects:
        lines.append(f"| `{p.id[:8]}` | {p.title} | {p.domain.value} | {p.created_at} |")
    lines += [
        "",
        "_Generated from live database state via `scripts.generate_research_index` - "
        "not hand-authored. Full detail (objectives, conclusions, limitations) is queryable "
        "via `GET /api/v1/projects/{id}`._",
    ]
    _write("projects/INDEX.md", lines)


def generate_hypotheses_registry(db) -> None:
    hyps = db.query(Hypothesis).order_by(Hypothesis.created_at).all()
    lines = [
        "# Hypothesis Registry",
        "",
        f"{len(hyps)} hypothesis/hypotheses recorded.",
        "",
        "| ID | Alternative Hypothesis | Status | Quality Score | Decision Rule |",
        "|---|---|---|---|---|",
    ]
    for h in hyps:
        rule = h.decision_rule or {}
        rule_str = f"metric={rule.get('metric')}, α={rule.get('alpha')}, min_effect={rule.get('min_effect_size')}, dir={rule.get('direction')}"
        lines.append(
            f"| `{h.id[:8]}` | {h.alternative_hypothesis} | {h.status.value} | {h.quality_score} | {rule_str} |"
        )
    lines += [
        "",
        "_Every row's decision_rule was fixed at hypothesis-creation time, before its "
        "experiment ran (pre-registration - see ADR-006)._",
    ]
    _write("hypotheses/REGISTRY.md", lines)


def generate_experiments_index(db) -> None:
    experiments = db.query(Experiment).order_by(Experiment.created_at).all()
    lines = [
        "# Experiments Index",
        "",
        f"{len(experiments)} experiment(s) recorded.",
        "",
        "| ID | Domain | Objective | Status | Conclusion |",
        "|---|---|---|---|---|",
    ]
    for e in experiments:
        result = (
            db.query(Result).filter(Result.experiment_id == e.id).order_by(Result.created_at.desc()).first()
        )
        conclusion = result.conclusion_status.value if result and result.conclusion_status else "(none yet)"
        lines.append(f"| `{e.id[:8]}` | {e.domain.value} | {e.objective} | {e.status.value} | {conclusion} |")
    lines += [
        "",
        "_See `research/<domain>/` for the full JSON result of each concluded experiment, "
        "and `reproducibility/experiment-<id>/` where a reproduction has been run._",
    ]
    _write("experiments/INDEX.md", lines)


def generate_baselines_registry(db) -> None:
    configs = db.query(ExperimentConfig).all()
    seen = set()
    rows = []
    for c in configs:
        key = (c.baseline_spec, c.model_spec)
        if key in seen or not c.baseline_spec:
            continue
        seen.add(key)
        rows.append(key)
    lines = [
        "# Baseline Registry (observed in this database)",
        "",
        "Baselines actually used by experiments recorded so far - drawn from the fixed, "
        "reviewed vocabulary in `app/services/codegen/{ai,cyber}_templates.py` "
        "(Section 16 - baselines are never invented ad hoc by an LLM).",
        "",
        "| Baseline | Compared Against |",
        "|---|---|",
    ]
    for baseline, proposed in rows:
        lines.append(f"| {baseline} | {proposed or '(n/a)'} |")
    _write("baselines/REGISTRY.md", lines)


def generate_evaluation_summary(db) -> None:
    results = db.query(Result).all()
    total = len(results)
    supported = sum(1 for r in results if r.conclusion_status and r.conclusion_status.value == "SUPPORTED")
    not_supported = sum(
        1 for r in results if r.conclusion_status and r.conclusion_status.value == "NOT_SUPPORTED"
    )
    inconclusive = sum(
        1 for r in results if r.conclusion_status and r.conclusion_status.value == "INCONCLUSIVE"
    )

    lines = [
        "# Evaluation Summary (Section 72)",
        "",
        f"- Total concluded results: {total}",
        f"- SUPPORTED: {supported}",
        f"- NOT_SUPPORTED: {not_supported}",
        f"- INCONCLUSIVE: {inconclusive}",
        "",
        "Every conclusion above was produced by the deterministic Conclusion Engine "
        "(`app/services/statistics/conclusion.py`) evaluating a pre-registered decision "
        "rule against real computed statistics - none were asserted by an LLM (ADR-006).",
        "",
        "This is a small, single-session evaluation batch, not a large-scale benchmark - "
        "see `docs/masters-application/13_results.md` for the full context and caveats.",
    ]
    _write("evaluation/summary.md", lines)


def main() -> int:
    ensure_schema()
    db = get_session()
    try:
        generate_projects_index(db)
        generate_hypotheses_registry(db)
        generate_experiments_index(db)
        generate_baselines_registry(db)
        generate_evaluation_summary(db)
    finally:
        db.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
