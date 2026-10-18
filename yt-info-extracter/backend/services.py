"""
Business logic — video loading, chat management, message handling, MD export.
"""
import asyncio
import json
import os
import re
from datetime import datetime, timezone

import httpx
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from langchain_core.messages import HumanMessage, AIMessage
from langchain_core.prompts import ChatPromptTemplate
from langchain_groq import ChatGroq
from dotenv import load_dotenv

from .models import Video, Chat, Message
from .workflow import (
    get_video_id,
    get_transcript,
    build_vector_store,
    graph,
    llm,
    stream_chat_response,
)
from .prompts import MD_SINGLE_MESSAGE_SYSTEM_PROMPT, MD_FULL_CHAT_SYSTEM_PROMPT

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


async def delete_video(db: AsyncSession, video_pk: int) -> Video | None:
    result = await db.execute(select(Video).where(Video.id == video_pk))
    video = result.scalar_one_or_none()
    if video:
        await db.delete(video)
        await db.commit()
    return video


# ── Chat ─────────────────────────────────────────────────────────────

async def create_chat(db: AsyncSession, video_id: int, title: str = "New Chat") -> Chat:
    chat = Chat(video_id=video_id, title=title)
    db.add(chat)
    await db.commit()
    await db.refresh(chat)
    # Eagerly load relationship so Pydantic serialization doesn't trigger MissingGreenlet
    return await get_chat_with_messages(db, chat.id)


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


async def stream_message(db: AsyncSession, chat_id: int, content: str):
    """
    Stream user and AI messages with real-time SSE chunks.
    Yields Server-Sent Event strings:
      - user_message
      - route
      - delta
      - done
      - error
    """
    chat = await get_chat_with_messages(db, chat_id)
    if not chat:
        yield f"data: {json.dumps({'type': 'error', 'message': 'Chat not found'})}\n\n"
        return

    video = await get_video(db, chat.video_id)
    if not video:
        yield f"data: {json.dumps({'type': 'error', 'message': 'Video not found'})}\n\n"
        return

    # Build LangChain message list
    lc_messages = []
    for msg in chat.messages:
        if msg.role == "user":
            lc_messages.append(HumanMessage(content=msg.content))
        else:
            lc_messages.append(AIMessage(content=msg.content))
    lc_messages.append(HumanMessage(content=content))

    # Persist user message first
    user_msg = Message(chat_id=chat_id, role="user", content=content)
    db.add(user_msg)
    await db.commit()
    await db.refresh(user_msg)

    # Emit user message confirmed event
    yield f"data: {json.dumps({'type': 'user_message', 'message': {'id': user_msg.id, 'chat_id': user_msg.chat_id, 'role': user_msg.role, 'content': user_msg.content, 'created_at': user_msg.created_at.isoformat()}})}\n\n"

    accumulated_content = []
    current_route = "rag"

    try:
        async for event in stream_chat_response(lc_messages, video.transcript_text, video.video_id):
            if event["type"] == "route":
                current_route = event["route"]
                yield f"data: {json.dumps(event)}\n\n"
            elif event["type"] == "delta":
                accumulated_content.append(event["content"])
                yield f"data: {json.dumps(event)}\n\n"

        full_content = "".join(accumulated_content)
        timestamps = extract_timestamps(full_content)

        ai_msg = Message(
            chat_id=chat_id,
            role="assistant",
            content=full_content,
            route=current_route,
            timestamps_json=timestamps,
        )
        db.add(ai_msg)

        if len(chat.messages) <= 1:
            chat.title = content[:60] + ("…" if len(content) > 60 else "")
        chat.updated_at = datetime.now(timezone.utc)

        await db.commit()
        await db.refresh(ai_msg)

        yield f"data: {json.dumps({'type': 'done', 'ai_message': {'id': ai_msg.id, 'chat_id': ai_msg.chat_id, 'role': ai_msg.role, 'content': ai_msg.content, 'route': ai_msg.route, 'timestamps_json': timestamps, 'created_at': ai_msg.created_at.isoformat()}})}\n\n"

    except Exception as e:
        yield f"data: {json.dumps({'type': 'error', 'message': str(e)})}\n\n"



# ── Markdown export ──────────────────────────────────────────────────

# ── Markdown export (Powered by qwen/qwen3.8-27b) ─────────────────────

def get_export_llm():
    """
    Get ChatGroq LLM configured with qwen/qwen3.8-27b using API_KEY_2.
    Falls back to GROQ_API_KEY_2 or GROQ_API_KEY if API_KEY_2 is not yet populated.
    """
    env_path = os.path.join(os.path.dirname(__file__), ".env")
    if os.path.exists(env_path):
        load_dotenv(env_path, override=True)

    api_key = (
        os.getenv("API_KEY_2")
        or os.getenv("GROQ_API_KEY_2")
        or os.getenv("GROQ_API_KEY")
    )
    if api_key:
        api_key = api_key.strip("'\" \t\r\n")

    return ChatGroq(
        model="qwen/qwen3.8-27b",
        temperature=0.3,
        max_retries=2,
        api_key=api_key,
    )


async def generate_md(
    db: AsyncSession, chat_id: int, message_id: int, instruction: str = "auto"
) -> str:
    """Generate a polished, in-depth .md file for a given AI message using qwen/qwen3.8-27b."""
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

    export_llm = get_export_llm()

    md_prompt = ChatPromptTemplate.from_messages(
        [
            ("system", MD_SINGLE_MESSAGE_SYSTEM_PROMPT),
            (
                "human",
                "User's Question: {question}\n\n"
                "AI's Answer to Convert into Detailed Markdown:\n{latest_answer}\n\n"
                "Human-in-the-Loop Extra Instruction: {human_instruction}",
            ),
        ]
    )

    md_content = await asyncio.to_thread(
        lambda: (md_prompt | export_llm)
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


async def generate_full_chat_md(
    db: AsyncSession, chat_id: int, instruction: str = "auto"
) -> str:
    """
    Generate an exhaustive, highly detailed .md research report summarizing the entire
    chat session using qwen/qwen3.8-27b with ASCII flowcharts, tables, and verified image references.
    """
    result = await db.execute(
        select(Chat).where(Chat.id == chat_id).options(selectinload(Chat.video), selectinload(Chat.messages))
    )
    chat = result.scalar_one_or_none()
    if not chat:
        raise ValueError("Chat session not found")

    messages = sorted(chat.messages, key=lambda m: m.id)
    if not messages:
        raise ValueError("No messages in this chat to export")

    # Format the chat history into a clean dialogue script
    dialogue_blocks = []
    citations_found = []
    for msg in messages:
        sender = "User" if msg.role == "user" else f"AI Assistant ({msg.route or 'RAG'})"
        dialogue_blocks.append(f"### [{sender}]:\n{msg.content}\n")
        if msg.timestamps:
            try:
                import json
                ts_list = json.loads(msg.timestamps) if isinstance(msg.timestamps, str) else msg.timestamps
                for item in ts_list:
                    citations_found.append(f"- {item.get('timestamp')}: cited in response to user query")
            except Exception:
                pass

    dialogue_transcript = "\n".join(dialogue_blocks)
    citations_str = "\n".join(citations_found) if citations_found else "None cited explicitly."

    video_info = "No specific YouTube video attached."
    if chat.video:
        video_info = (
            f"- Video Title: {chat.video.title}\n"
            f"- Video URL: {chat.video.url}\n"
            f"- Video ID: {chat.video.video_id}\n"
            f"- Video Thumbnail URL: https://img.youtube.com/vi/{chat.video.video_id}/maxresdefault.jpg\n"
        )

    export_llm = get_export_llm()

    system_prompt = MD_FULL_CHAT_SYSTEM_PROMPT

    human_content = (
        f"### Research Session Context:\n"
        f"Chat Title: {chat.title}\n"
        f"Created At: {chat.created_at}\n\n"
        f"### Source Media:\n{video_info}\n\n"
        f"### Explicit Citations Extracted:\n{citations_str}\n\n"
        f"### User/AI Conversation History to Summarize:\n"
        f"{dialogue_transcript}\n\n"
        f"### User's Custom Export Instruction:\n{instruction}\n\n"
        f"Now produce the complete, exhaustive, deeply detailed Markdown research dossier following all guidelines."
    )

    md_prompt = ChatPromptTemplate.from_messages(
        [
            ("system", system_prompt),
            ("human", human_content),
        ]
    )

    md_content = await asyncio.to_thread(
        lambda: (md_prompt | export_llm).invoke({}).content
    )

    filename = f"research_dossier_chat{chat_id}.md"
    filepath = os.path.join(ARTIFACTS_DIR, filename)
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(md_content)

    return filepath

