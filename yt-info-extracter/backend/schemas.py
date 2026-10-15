"""
Pydantic request / response schemas for the API.
"""
from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel


# ── Video ──────────────────────────────────────────────

class VideoCreate(BaseModel):
    url: str


class VideoResponse(BaseModel):
    id: int
    video_id: str
    url: str
    title: str
    thumbnail_url: str
    transcript_segments: Optional[list] = None
    created_at: datetime

    class Config:
        from_attributes = True


class VideoListResponse(BaseModel):
    """Lightweight version without transcript segments."""
    id: int
    video_id: str
    url: str
    title: str
    thumbnail_url: str
    created_at: datetime

    class Config:
        from_attributes = True


# ── Chat ───────────────────────────────────────────────

class ChatCreate(BaseModel):
    video_id: int
    title: Optional[str] = "New Chat"


# ── Message ────────────────────────────────────────────

class MessageCreate(BaseModel):
    content: str
    md_instruction: Optional[str] = None


class MdExportRequest(BaseModel):
    instruction: Optional[str] = "auto"


class MessageResponse(BaseModel):
    id: int
    chat_id: int
    role: str
    content: str
    route: Optional[str] = None
    timestamps_json: Optional[list] = None
    md_file_path: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


class ChatResponse(BaseModel):
    id: int
    video_id: int
    title: str
    created_at: datetime
    updated_at: Optional[datetime] = None
    messages: List[MessageResponse] = []

    class Config:
        from_attributes = True


class ChatListItem(BaseModel):
    id: int
    video_id: int
    title: str
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True
