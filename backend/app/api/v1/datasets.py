"""Dataset registry API.

Registering a real `Dataset` + `DatasetVersion` row and referencing it from
an `ExperimentConfig.dataset_version_id` is what makes the deterministic
Limitation Detector's `reproducibility_limitation` finding
(app/services/limitations/detector.py) go away for a given experiment -
this endpoint exists so that's a real, queryable fact instead of a bare
string inside `codegen_spec`.
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.literature import Dataset, DatasetVersion
from app.models.user import User
from app.schemas.dataset import DatasetCreate, DatasetOut, DatasetVersionCreate, DatasetVersionOut
from app.security.rbac import require_any, require_researcher
from app.services.audit import record_audit

router = APIRouter(prefix="/datasets", tags=["datasets"])


@router.post("", response_model=DatasetOut, status_code=201)
def create_dataset(
    payload: DatasetCreate, user: User = Depends(require_researcher), db: Session = Depends(get_db)
):
    existing = db.query(Dataset).filter(Dataset.name == payload.name).one_or_none()
    if existing:
        raise HTTPException(status_code=409, detail=f"Dataset '{payload.name}' already registered")

    dataset = Dataset(**payload.model_dump())
    db.add(dataset)
    db.flush()
    record_audit(
        db, actor_user_id=user.id, action="dataset.create", resource_type="dataset", resource_id=dataset.id
    )
    db.commit()
    db.refresh(dataset)
    return dataset


@router.get("", response_model=list[DatasetOut])
def list_datasets(user: User = Depends(require_any), db: Session = Depends(get_db)):
    return db.query(Dataset).order_by(Dataset.name).all()


@router.get("/{dataset_id}", response_model=DatasetOut)
def get_dataset(dataset_id: str, user: User = Depends(require_any), db: Session = Depends(get_db)):
    dataset = db.get(Dataset, dataset_id)
    if not dataset:
        raise HTTPException(status_code=404, detail="Dataset not found")
    return dataset


@router.post("/{dataset_id}/versions", response_model=DatasetVersionOut, status_code=201)
def create_dataset_version(
    dataset_id: str,
    payload: DatasetVersionCreate,
    user: User = Depends(require_researcher),
    db: Session = Depends(get_db),
):
    dataset = db.get(Dataset, dataset_id)
    if not dataset:
        raise HTTPException(status_code=404, detail="Dataset not found")

    version = DatasetVersion(dataset_id=dataset_id, **payload.model_dump())
    db.add(version)
    db.flush()
    record_audit(
        db,
        actor_user_id=user.id,
        action="dataset_version.create",
        resource_type="dataset_version",
        resource_id=version.id,
    )
    db.commit()
    db.refresh(version)
    return version


@router.get("/{dataset_id}/versions", response_model=list[DatasetVersionOut])
def list_dataset_versions(
    dataset_id: str, user: User = Depends(require_any), db: Session = Depends(get_db)
):
    dataset = db.get(Dataset, dataset_id)
    if not dataset:
        raise HTTPException(status_code=404, detail="Dataset not found")
    return (
        db.query(DatasetVersion)
        .filter(DatasetVersion.dataset_id == dataset_id)
        .order_by(DatasetVersion.created_at.desc())
        .all()
    )
