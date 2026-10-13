from typing import Optional

from pydantic import BaseModel


class DatasetCreate(BaseModel):
    name: str
    source: str
    license: str
    description: Optional[str] = None
    features: Optional[list[str]] = None
    limitations: Optional[str] = None
    citation: Optional[str] = None


class DatasetOut(BaseModel):
    id: str
    name: str
    source: str
    license: str
    description: Optional[str] = None
    features: Optional[list] = None
    limitations: Optional[str] = None
    citation: Optional[str] = None

    class Config:
        from_attributes = True


class DatasetVersionCreate(BaseModel):
    version_tag: str
    checksum: Optional[str] = None
    preprocessing: Optional[str] = None
    row_count: Optional[int] = None


class DatasetVersionOut(BaseModel):
    id: str
    dataset_id: str
    version_tag: str
    checksum: Optional[str] = None
    preprocessing: Optional[str] = None
    row_count: Optional[int] = None

    class Config:
        from_attributes = True
