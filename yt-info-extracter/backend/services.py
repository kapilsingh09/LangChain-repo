"""
Business logic — video loading, chat management, message handling, MD export.
"""
import asyncio
import os
import re
from datetime import datetime, timezone

import httpx
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from langchain_core.messages import HumanMessage, AIMessage
from langchain_core.prompts import ChatPromptTemplate

from .models import Video, Chat, Message
from .workflow import get_video_id, get_transcript, build_vector_store, graph, llm

ARTIFACTS_DIR = os.path.join(os.path.dirname(__file__), "artifacts")
os.makedirs(ARTIFACTS_DIR, exist_ok=True)


# ── Helpers ──────────────────────────────────────────────────────────

def extract_timestamps(text: str) -> list:
    """Pull every [M:SS], [MM:SS], or timestamp range like [6:38-7:06] / [6:38‑7:06] out of a string."""
    out = []
    pattern = r"(?:\[|\()(\d+):(\d{2})(?::(\d{2}))?(?:\s*[-‑–—\u2010\u2011\u2012\u2013\u2014to]\s*(\d+):(\d{2})(?::(\d{2}))?)?(?:\]|\))"
    for m in re.finditer(pattern, text):
        mins, secs = int(m.group(1)), int(m.group(2))
        total_seconds = mins * 60 + secs
        out.append(
            {"timestamp": m.group(0), "seconds": total_seconds, "position": m.start()}
        )
    return out


async def _fetch_video_title(video_id: str) -> str:
    """Best-effort fetch of the video title via YouTube oEmbed."""
    try:
        async with httpx.AsyncClient(timeout=5) as client:
            r = await client.get(
                "https://www.youtube.com/oembed",
                params={"url": f"https://www.youtube.com/watch?v={video_id}", "format": "json"},
            )
            if r.status_code == 200:
                return r.json().get("title", f"Video {video_id}")
    except Exception:
        pass
    return f"Video {video_id}"


# ── Video ────────────────────────────────────────────────────────────

async def load_video(db: AsyncSession, url: str) -> Video:
    """Fetch transcript, build vector store, persist to DB (or return cached)."""
    video_id = get_video_id(url)

    # Already in DB?
    result = await db.execute(select(Video).where(Video.video_id == video_id))
    existing = result.scalar_one_or_none()
    if existing:
        # Make sure the in‑memory vector store is ready
        await asyncio.to_thread(build_vector_store, existing.transcript_text, existing.video_id)
        return existing

    # Fetch transcript (blocking) + build vector store (blocking)
    transcript_text, segments = await asyncio.to_thread(get_transcript, url)
    await asyncio.to_thread(build_vector_store, transcript_text, video_id)

    title = await _fetch_video_title(video_id)
    thumbnail_url = f"https://img.youtube.com/vi/{video_id}/maxresdefault.jpg"

    video = Video(
        video_id=video_id,
        url=url,
        title=title,
        thumbnail_url=thumbnail_url,
        transcript_text=transcript_text,
        transcript_segments=segments,
    )
    db.add(video)
    await db.commit()
    await db.refresh(video)
    return video


async def list_videos(db: AsyncSession):
    result = await db.execute(select(Video).order_by(Video.created_at.desc()))
    return result.scalars().all()


async def get_video(db: AsyncSession, video_pk: int):
    result = await db.execute(select(Video).where(Video.id == video_pk))
    return result.scalar_one_or_none()


# ── Chat ─────────────────────────────────────────────────────────────

async def create_chat(db: AsyncSession, video_id: int, title: str = "New Chat") -> Chat:
    chat = Chat(video_id=video_id, title=title)
    db.add(chat)
    await db.commit()
    await db.refresh(chat)
    return chat


async def list_chats(db: AsyncSession, video_id: int | None = None):
    q = select(Chat)
    if video_id is not None:
        q = q.where(Chat.video_id == video_id)
    q = q.order_by(Chat.updated_at.desc())
    result = await db.execute(q)
    return result.scalars().all()


async def get_chat_with_messages(db: AsyncSession, chat_id: int) -> Chat | None:
    result = await db.execute(
        select(Chat).options(selectinload(Chat.messages)).where(Chat.id == chat_id)
    )
    return result.scalar_one_or_none()


async def delete_chat(db: AsyncSession, chat_id: int) -> Chat | None:
    result = await db.execute(select(Chat).where(Chat.id == chat_id))
    chat = result.scalar_one_or_none()
    if chat:
        await db.delete(chat)
        await db.commit()
    return chat


# ── Messaging ────────────────────────────────────────────────────────

async def send_message(db: AsyncSession, chat_id: int, content: str):
    """Send a user message, invoke the LangGraph pipeline, persist both messages."""
    chat = await get_chat_with_messages(db, chat_id)
    if not chat:
        raise ValueError("Chat not found")

    video = await get_video(db, chat.video_id)
    if not video:
        raise ValueError("Video not found")

    # Ensure vector store is ready
    await asyncio.to_thread(build_vector_store, video.transcript_text, video.video_id)

    # Build LangChain message list from DB history + new user message
    lc_messages = []
    for msg in chat.messages:
        if msg.role == "user":
            lc_messages.append(HumanMessage(content=msg.content))
        else:
            lc_messages.append(AIMessage(content=msg.content))
    lc_messages.append(HumanMessage(content=content))

    # Invoke the graph (blocking – run in thread)
    result = await asyncio.to_thread(
        graph.invoke,
        {
            "messages": lc_messages,
            "transcript": video.transcript_text,
            "video_id": video.video_id,
        },
    )

    ai_content = result["messages"][-1].content
    route = result.get("route", "")
    timestamps = extract_timestamps(ai_content)

    # Persist user message
    user_msg = Message(chat_id=chat_id, role="user", content=content)
    db.add(user_msg)

    # Persist AI message
    ai_msg = Message(
        chat_id=chat_id,
        role="assistant",
        content=ai_content,
        route=route,
        timestamps_json=timestamps,
    )
    db.add(ai_msg)

    # Update chat title on first message
    if len(chat.messages) == 0:
        chat.title = content[:60] + ("…" if len(content) > 60 else "")
    chat.updated_at = datetime.now(timezone.utc)

    await db.commit()
    await db.refresh(user_msg)
    await db.refresh(ai_msg)

    return user_msg, ai_msg


# ── Markdown export ──────────────────────────────────────────────────

async def generate_md(
    db: AsyncSession, chat_id: int, message_id: int, instruction: str = "auto"
) -> str:
    """Generate a polished .md file for a given AI message."""
    result = await db.execute(
        select(Message).where(Message.id == message_id, Message.chat_id == chat_id)
    )
    message = result.scalar_one_or_none()
    if not message or message.role != "assistant":
        raise ValueError("AI message not found")

    # Grab the preceding user question
    result = await db.execute(
        select(Message)
        .where(Message.chat_id == chat_id, Message.id < message_id, Message.role == "user")
        .order_by(Message.id.desc())
    )
    user_msg = result.scalar_one_or_none()
    user_question = user_msg.content if user_msg else ""

    md_prompt = ChatPromptTemplate.from_messages(
        [
            (
                "system",
                "You are an expert technical writer creating a clean `.md` study note "
                "from the AI's latest response.\n\n"
                "### SMART DESIGN RULES (FOLLOW STRICTLY):\n"
                "1. Write clean, natural Markdown using `# Headings`, `> Callout quotes`, "
                "bullet points, and **bold** key terms.\n"
                "2. Include a visual ASCII diagram ONLY IF the user explicitly asked for one "
                "or the topic genuinely needs structural visualization.\n"
                "3. For comparisons/timestamps use a clean Markdown table.\n\n"
                "Keep the formatting classy, readable, and well-spaced.",
            ),
            (
                "human",
                "User's Question: {question}\n\n"
                "AI's Answer to Convert into Markdown:\n{latest_answer}\n\n"
                "Human-in-the-Loop Extra Instruction: {human_instruction}",
            ),
        ]
    )

    md_content = await asyncio.to_thread(
        lambda: (md_prompt | llm)
        .invoke(
            {
                "question": user_question,
                "latest_answer": message.content,
                "human_instruction": instruction,
            }
        )
        .content
    )

    filename = f"notes_chat{chat_id}_msg{message_id}.md"
    filepath = os.path.join(ARTIFACTS_DIR, filename)
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(md_content)

    message.md_file_path = filepath
    await db.commit()
    return filepath
