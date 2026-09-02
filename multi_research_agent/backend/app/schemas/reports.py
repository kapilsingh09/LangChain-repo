from typing import Dict
from pydantic import BaseModel, Field


class ReportMetadata(BaseModel):
    filename: str
    title: str
    file_path: str
    size_bytes: int
    created_at: str
    download_url: str


class ReportDetailResponse(BaseModel):
    filename: str
    content: str
    metadata: ReportMetadata


class HealthResponse(BaseModel):
    status: str = "healthy"
    version: str = "1.0.0"
    services: Dict[str, bool] = Field(
        default_factory=dict,
        description="Configuration status of all integrated AI services"
    )
