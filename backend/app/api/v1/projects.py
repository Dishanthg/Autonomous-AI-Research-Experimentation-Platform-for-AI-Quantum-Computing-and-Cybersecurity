from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.project import Project, ResearchQuestion
from app.models.user import User
from app.schemas.project import ProjectCreate, ProjectOut, ResearchQuestionCreate, ResearchQuestionOut
from app.security.rbac import require_any, require_researcher
from app.services.audit import record_audit

router = APIRouter(prefix="/projects", tags=["projects"])


@router.post("", response_model=ProjectOut, status_code=201)
def create_project(
    payload: ProjectCreate, user: User = Depends(require_researcher), db: Session = Depends(get_db)
):
    project = Project(
        title=payload.title, domain=payload.domain, owner_id=user.id, objectives=payload.objectives
    )
    db.add(project)
    db.flush()
    record_audit(
        db, actor_user_id=user.id, action="project.create", resource_type="project", resource_id=project.id
    )
    db.commit()
    db.refresh(project)
    return project


@router.get("", response_model=list[ProjectOut])
def list_projects(user: User = Depends(require_any), db: Session = Depends(get_db)):
    return db.query(Project).order_by(Project.created_at.desc()).all()


@router.get("/{project_id}", response_model=ProjectOut)
def get_project(project_id: str, user: User = Depends(require_any), db: Session = Depends(get_db)):
    project = db.get(Project, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    return project


@router.post("/{project_id}/questions", response_model=ResearchQuestionOut, status_code=201)
def create_research_question(
    project_id: str,
    payload: ResearchQuestionCreate,
    user: User = Depends(require_researcher),
    db: Session = Depends(get_db),
):
    project = db.get(Project, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    rq = ResearchQuestion(
        project_id=project_id,
        question_text=payload.question_text,
        domain=payload.domain,
        is_primary=payload.is_primary,
    )
    db.add(rq)
    db.flush()
    record_audit(
        db,
        actor_user_id=user.id,
        action="research_question.create",
        resource_type="research_question",
        resource_id=rq.id,
    )
    db.commit()
    db.refresh(rq)
    return rq


@router.get("/{project_id}/questions", response_model=list[ResearchQuestionOut])
def list_research_questions(
    project_id: str, user: User = Depends(require_any), db: Session = Depends(get_db)
):
    return db.query(ResearchQuestion).filter(ResearchQuestion.project_id == project_id).all()
