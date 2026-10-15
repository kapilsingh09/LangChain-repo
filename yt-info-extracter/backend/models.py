"""
SQLAlchemy ORM models for Video, Chat, and Message.
"""
from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, JSON
from sqlalchemy.orm import relationship

from .database import Base


def _utcnow():
    return datetime.now(timezone.utc)


class Video(Base):
    __tablename__ = "videos"

    id = Column(Integer, primary_key=True, index=True)
    video_id = Column(String(20), unique=True, index=True, nullable=False)
    url = Column(String(500), nullable=False)
    title = Column(String(500), default="")
    thumbnail_url = Column(String(500), default="")
    transcript_text = Column(Text, nullable=False)
    transcript_segments = Column(JSON, default=list)   # [{text, start, duration, timestamp}, ...]
    created_at = Column(DateTime, default=_utcnow)

    chats = relationship("Chat", back_populates="video", cascade="all, delete-orphan")


class Chat(Base):
    __tablename__ = "chats"

    id = Column(Integer, primary_key=True, index=True)
    video_id = Column(Integer, ForeignKey("videos.id"), nullable=False)
    title = Column(String(500), default="New Chat")
    created_at = Column(DateTime, default=_utcnow)
    updated_at = Column(DateTime, default=_utcnow, onupdate=_utcnow)

    video = relationship("Video", back_populates="chats")
    messages = relationship(
        "Message",
        back_populates="chat",
        cascade="all, delete-orphan",
        order_by="Message.created_at",
    )


class Message(Base):
    __tablename__ = "messages"

    id = Column(Integer, primary_key=True, index=True)
    chat_id = Column(Integer, ForeignKey("chats.id"), nullable=False)
    role = Column(String(20), nullable=False)          # "user" | "assistant"
    content = Column(Text, nullable=False)
    route = Column(String(20), nullable=True)           # "chat" | "rag" | "summarize"
    timestamps_json = Column(JSON, nullable=True)       # extracted [MM:SS] timestamps
    md_file_path = Column(String(500), nullable=True)
    created_at = Column(DateTime, default=_utcnow)

    chat = relationship("Chat", back_populates="messages")
