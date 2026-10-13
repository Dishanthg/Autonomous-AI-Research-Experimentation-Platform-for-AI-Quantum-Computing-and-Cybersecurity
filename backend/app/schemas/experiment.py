from typing import Optional

from pydantic import BaseModel

from app.models.enums import Domain, ExperimentStatus, RunStatus


class ExperimentCreate(BaseModel):
    project_id: str
    hypothesis_id: str
    domain: Domain
    objective: str
    num_runs_planned: int = 5


class ExperimentOut(BaseModel):
    id: str
    project_id: str
    hypothesis_id: str
    domain: Domain
    objective: str
    status: ExperimentStatus
    num_runs_planned: int

    class Config:
        from_attributes = True


class ExperimentConfigCreate(BaseModel):
    experiment_id: str
    dataset_id: Optional[str] = None
    dataset_version_id: Optional[str] = None
    model_spec: Optional[str] = None
    baseline_spec: Optional[str] = None
    features: Optional[list[str]] = None
    hyperparameters: Optional[dict] = None
    random_seed: int = 42
    num_runs: int = 5
    metrics_requested: list[str]
    resource_limits: dict
    software_environment: Optional[dict] = None
    # Domain-specific codegen spec, e.g. {"dataset": "synthetic_classification", ...}
    codegen_spec: dict


class ExperimentConfigOut(BaseModel):
    id: str
    experiment_id: str
    version: int
    approved: bool
    approved_by_user_id: Optional[str] = None
    num_runs: int
    metrics_requested: list

    class Config:
        from_attributes = True


class ApprovalRequest(BaseModel):
    rationale: Optional[str] = None
    # Gate 1 approval is blocked if
    # Research Memory finds an identical (domain, baseline, proposed,
    # dataset) experiment already exists in this project, unless the
    # researcher explicitly acknowledges it here.
    override_duplicate_warning: bool = False


class ExperimentRunOut(BaseModel):
    id: str
    experiment_id: str
    config_id: str
    status: RunStatus
    exit_code: Optional[int] = None
    stdout: Optional[str] = None
    stderr: Optional[str] = None
    isolation_level: Optional[str] = None

    class Config:
        from_attributes = True


class ArtifactOut(BaseModel):
    id: str
    run_id: str
    artifact_type: str
    path: str
    checksum: Optional[str] = None

    class Config:
        from_attributes = True
