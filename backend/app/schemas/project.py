from typing import Optional

from pydantic import BaseModel

from app.models.enums import Domain


class ProjectCreate(BaseModel):
    title: str
    domain: Domain
    objectives: Optional[str] = None


class ProjectOut(BaseModel):
    id: str
    title: str
    domain: Domain
    owner_id: str
    objectives: Optional[str] = None
    conclusions: Optional[str] = None
    limitations: Optional[str] = None
    future_work: Optional[str] = None

    class Config:
        from_attributes = True


class ResearchQuestionCreate(BaseModel):
    question_text: str
    domain: Domain
    is_primary: bool = False


class ResearchQuestionOut(BaseModel):
    id: str
    project_id: str
    question_text: str
    domain: Domain
    is_primary: bool

    class Config:
        from_attributes = True
