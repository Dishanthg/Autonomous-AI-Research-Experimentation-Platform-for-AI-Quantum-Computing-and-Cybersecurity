"""Research Lineage / Timeline. Walks Project -> ResearchQuestion ->
Hypothesis -> Experiment ->
ExperimentRun -> Result -> StatisticalTest/Limitation and returns it as one
nested structure. The data has existed in the relational schema since the
first build session; this is the first traversal endpoint over it - no new
tables, purely a read-side query composition.
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.experiment import Experiment, ExperimentRun
from app.models.hypothesis import Hypothesis
from app.models.project import Project, ResearchQuestion
from app.models.result import Limitation, Result, StatisticalTest
from app.models.user import User
from app.security.rbac import require_any

router = APIRouter(prefix="/projects", tags=["lineage"])


def _serialize_run(run: ExperimentRun) -> dict:
    return {
        "id": run.id,
        "status": run.status.value,
        "isolation_level": run.isolation_level,
        "started_at": run.started_at.isoformat() if run.started_at else None,
        "finished_at": run.finished_at.isoformat() if run.finished_at else None,
        "exit_code": run.exit_code,
    }


def _serialize_result(db: Session, result: Result) -> dict:
    stats = db.query(StatisticalTest).filter(StatisticalTest.result_id == result.id).all()
    return {
        "id": result.id,
        "conclusion_status": result.conclusion_status.value if result.conclusion_status else None,
        "conclusion_rationale": result.conclusion_rationale,
        "human_approved": result.human_approved,
        "statistical_tests": [
            {
                "metric_name": s.metric_name,
                "test_name": s.test_name,
                "p_value": s.p_value,
                "effect_size": s.effect_size,
                "effect_size_type": s.effect_size_type,
            }
            for s in stats
        ],
    }


def _serialize_experiment(db: Session, experiment: Experiment) -> dict:
    runs = (
        db.query(ExperimentRun)
        .filter(ExperimentRun.experiment_id == experiment.id)
        .order_by(ExperimentRun.created_at)
        .all()
    )
    results = (
        db.query(Result).filter(Result.experiment_id == experiment.id).order_by(Result.created_at).all()
    )
    limitations = db.query(Limitation).filter(Limitation.experiment_id == experiment.id).all()
    return {
        "id": experiment.id,
        "domain": experiment.domain.value,
        "objective": experiment.objective,
        "status": experiment.status.value,
        "runs": [_serialize_run(r) for r in runs],
        "results": [_serialize_result(db, r) for r in results],
        "limitations": [{"category": lim.category, "description": lim.description} for lim in limitations],
    }


def _serialize_hypothesis(db: Session, hypothesis: Hypothesis) -> dict:
    experiments = (
        db.query(Experiment)
        .filter(Experiment.hypothesis_id == hypothesis.id)
        .order_by(Experiment.created_at)
        .all()
    )
    return {
        "id": hypothesis.id,
        "null_hypothesis": hypothesis.null_hypothesis,
        "alternative_hypothesis": hypothesis.alternative_hypothesis,
        "status": hypothesis.status.value,
        "experiments": [_serialize_experiment(db, e) for e in experiments],
    }


@router.get("/{project_id}/lineage")
def get_project_lineage(project_id: str, user: User = Depends(require_any), db: Session = Depends(get_db)):
    project = db.get(Project, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    questions = (
        db.query(ResearchQuestion)
        .filter(ResearchQuestion.project_id == project_id)
        .order_by(ResearchQuestion.created_at)
        .all()
    )
    all_hypotheses = db.query(Hypothesis).filter(Hypothesis.project_id == project_id).all()

    question_nodes = []
    for question in questions:
        hyps = [h for h in all_hypotheses if h.research_question_id == question.id]
        question_nodes.append(
            {
                "id": question.id,
                "question_text": question.question_text,
                "is_primary": question.is_primary,
                "hypotheses": [_serialize_hypothesis(db, h) for h in hyps],
            }
        )

    unlinked = [h for h in all_hypotheses if not h.research_question_id]

    return {
        "project_id": project.id,
        "project_title": project.title,
        "questions": question_nodes,
        "unlinked_hypotheses": [_serialize_hypothesis(db, h) for h in unlinked],
    }
