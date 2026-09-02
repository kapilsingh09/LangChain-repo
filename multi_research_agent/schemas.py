from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field


class ResearchRequest(BaseModel):
    question: str = Field(
        ...,
        description="The research question or topic to investigate in depth.",
        examples=["Optimizing Edge AI and Lightweight Computer Vision Architectures for Real-Time, Offline Accessibility Tools."]
    )
    thread_id: Optional[str] = Field(
        default=None,
        description="Optional unique identifier for the execution thread / session. If omitted, a unique ID will be generated."
    )


class ImageSpecModel(BaseModel):
    placeholder: str = Field(..., description="e.g. [[IMAGE_1]]")
    filename: str = Field(..., description="Filename under images/, e.g. qkv_flow.png")
    alt: str = Field(..., description="Alt text for the image")
    caption: str = Field(..., description="Caption displayed below the image")
    prompt: str = Field(..., description="Prompt sent to the image model")
    size: str = "1024x1024"
    quality: str = "medium"


class ResearchResponse(BaseModel):
    thread_id: str
    question: str
    status: str = "completed"
    research_topics_planned: List[str] = Field(default_factory=list)
    research_results: List[str] = Field(default_factory=list)
    critique: Optional[str] = None
    final_report: str
    saved_file_path: Optional[str] = None
    web_search_performed: bool = False
    image_specs: List[Dict[str, Any]] = Field(default_factory=list)


class StreamEvent(BaseModel):
    event: str = Field(..., description="Type of stream event, e.g. 'node_update', 'final_result', 'error'")
    node: Optional[str] = Field(None, description="Name of the executing LangGraph node")
    data: Dict[str, Any] = Field(default_factory=dict, description="Payload data for the event")


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
        description="Status of configured API keys and dependencies"
    )
