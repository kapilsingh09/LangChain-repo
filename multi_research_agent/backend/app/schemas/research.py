from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field


class ResearchRequest(BaseModel):
    question: str = Field(
        ...,
        description="The research topic or question to investigate.",
        examples=["Optimizing Edge AI and Lightweight Computer Vision Architectures for Real-Time, Offline Accessibility Tools."]
    )
    thread_id: Optional[str] = Field(
        default=None,
        description="Optional execution thread/session ID. An auto-generated UUID is used if omitted."
    )


class ImageSpecModel(BaseModel):
    placeholder: str = Field(..., description="Placeholder in markdown, e.g. [[IMAGE_1]]")
    filename: str = Field(..., description="Target image file name, e.g. pipeline_diagram.png")
    alt: str = Field(..., description="Image alt text")
    caption: str = Field(..., description="Image caption text")
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
    event: str = Field(..., description="Event name, e.g. 'node_update', 'completed', 'error'")
    node: Optional[str] = Field(None, description="Name of the node in LangGraph currently executing")
    data: Dict[str, Any] = Field(default_factory=dict, description="Payload data for the event")
