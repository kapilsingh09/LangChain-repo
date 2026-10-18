"""
FastAPI application – YouTube Researcher API + static‑file serving for the frontend.
"""
import os
from contextlib import asynccontextmanager

from fastapi import FastAPI, Depends, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from sqlalchemy.ext.asyncio import AsyncSession

from .database import init_db, get_db
from .schemas import (
    VideoCreate,
    VideoResponse,
    VideoListResponse,
    ChatCreate,
    ChatResponse,
    ChatListItem,
    MessageCreate,
    MessageResponse,
    MdExportRequest,
)
from .services import (
    load_video,
    list_videos,
    get_video,
    delete_video,
    create_chat,
    list_chats,
    get_chat_with_messages,
    delete_chat,
    send_message,
    stream_message,
    generate_md,
    generate_full_chat_md,
)


# ── Lifespan ─────────────────────────────────────────────────────────

@asynccontextmanager
async def lifespan(_app: FastAPI):
    await init_db()
    yield


app = FastAPI(title="YouTube Researcher", version="1.0.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── Frontend static files ────────────────────────────────────────────

_frontend_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "frontend")


@app.get("/")
async def serve_index():
    index = os.path.join(_frontend_dir, "index.html")
    if os.path.exists(index):
        return FileResponse(index)
    return {"message": "YouTube Researcher API — frontend not found"}


# Mount static AFTER the root route so "/" hits the handler above.
if os.path.exists(_frontend_dir):
    app.mount("/static", StaticFiles(directory=_frontend_dir), name="static")


# ── Video endpoints ──────────────────────────────────────────────────

@app.post("/api/videos", response_model=VideoResponse)
async def api_load_video(data: VideoCreate, db: AsyncSession = Depends(get_db)):
    try:
        video = await load_video(db, data.url)
        return video
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/api/videos", response_model=list[VideoListResponse])
async def api_list_videos(db: AsyncSession = Depends(get_db)):
    return await list_videos(db)


@app.get("/api/videos/{video_pk}", response_model=VideoResponse)
async def api_get_video(video_pk: int, db: AsyncSession = Depends(get_db)):
    video = await get_video(db, video_pk)
    if not video:
        raise HTTPException(status_code=404, detail="Video not found")
    return video


@app.delete("/api/videos/{video_pk}")
async def api_delete_video(video_pk: int, db: AsyncSession = Depends(get_db)):
    video = await delete_video(db, video_pk)
    if not video:
        raise HTTPException(status_code=404, detail="Video not found")
    return {"status": "deleted", "video_id": video_pk}


# ── Chat endpoints ───────────────────────────────────────────────────

@app.post("/api/chats", response_model=ChatResponse)
async def api_create_chat(data: ChatCreate, db: AsyncSession = Depends(get_db)):
    chat = await create_chat(db, data.video_id, data.title or "New Chat")
    return chat


@app.get("/api/chats", response_model=list[ChatListItem])
async def api_list_chats(
    video_id: int = Query(None), db: AsyncSession = Depends(get_db)
):
    return await list_chats(db, video_id)


@app.get("/api/chats/{chat_id}", response_model=ChatResponse)
async def api_get_chat(chat_id: int, db: AsyncSession = Depends(get_db)):
    chat = await get_chat_with_messages(db, chat_id)
    if not chat:
        raise HTTPException(status_code=404, detail="Chat not found")
    return chat


@app.delete("/api/chats/{chat_id}")
async def api_delete_chat(chat_id: int, db: AsyncSession = Depends(get_db)):
    chat = await delete_chat(db, chat_id)
    if not chat:
        raise HTTPException(status_code=404, detail="Chat not found")
    return {"status": "deleted"}


# ── Message endpoints ────────────────────────────────────────────────

@app.post("/api/chats/{chat_id}/messages")
async def api_send_message(
    chat_id: int, data: MessageCreate, db: AsyncSession = Depends(get_db)
):
    try:
        user_msg, ai_msg = await send_message(db, chat_id, data.content)
        return {
            "user_message": MessageResponse.model_validate(user_msg),
            "ai_message": MessageResponse.model_validate(ai_msg),
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/api/chats/{chat_id}/messages/stream")
async def api_stream_message(
    chat_id: int, data: MessageCreate, db: AsyncSession = Depends(get_db)
):
    """
    Stream AI responses token-by-token via Server-Sent Events (SSE) for ultra-smooth UI updates.
    """
    return StreamingResponse(
        stream_message(db, chat_id, data.content),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


# ── Markdown export / download ───────────────────────────────────────

@app.post("/api/chats/{chat_id}/export-md")
async def api_export_full_chat_md(
    chat_id: int,
    body: MdExportRequest = None,
    db: AsyncSession = Depends(get_db),
):
    """Summarize and export full conversation into an exhaustive Markdown research report via Qwen 27B."""
    instruction = body.instruction if body else "comprehensive"
    try:
        filepath = await generate_full_chat_md(db, chat_id, instruction)
        filename = os.path.basename(filepath)
        return {
            "filepath": filepath,
            "filename": filename,
            "download_url": f"/api/chats/{chat_id}/download-full-md",
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Export generation failed: {str(e)}")


@app.get("/api/chats/{chat_id}/download-full-md")
async def api_download_full_chat_md(
    chat_id: int,
):
    """Download the comprehensive Markdown research report generated by Qwen 27B."""
    filename = f"research_dossier_chat{chat_id}.md"
    filepath = os.path.join(os.path.dirname(__file__), "artifacts", filename)
    if not os.path.exists(filepath):
        raise HTTPException(status_code=404, detail="Markdown dossier not found on disk")
    return FileResponse(
        filepath,
        media_type="text/markdown",
        filename=filename,
    )


@app.post("/api/chats/{chat_id}/messages/{message_id}/export-md")
async def api_export_md(
    chat_id: int,
    message_id: int,
    body: MdExportRequest = None,
    db: AsyncSession = Depends(get_db),
):
    instruction = body.instruction if body else "auto"
    try:
        filepath = await generate_md(db, chat_id, message_id, instruction)
        filename = os.path.basename(filepath)
        return {
            "filepath": filepath,
            "filename": filename,
            "download_url": f"/api/chats/{chat_id}/messages/{message_id}/download-md",
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/api/chats/{chat_id}/messages/{message_id}/download-md")
async def api_download_md(
    chat_id: int, message_id: int, db: AsyncSession = Depends(get_db)
):
    from sqlalchemy import select
    from .models import Message

    result = await db.execute(
        select(Message).where(Message.id == message_id, Message.chat_id == chat_id)
    )
    message = result.scalar_one_or_none()
    if not message or not message.md_file_path:
        raise HTTPException(status_code=404, detail="MD file not generated yet")
    if not os.path.exists(message.md_file_path):
        raise HTTPException(status_code=404, detail="MD file not found on disk")
    return FileResponse(
        message.md_file_path,
        media_type="text/markdown",
        filename=os.path.basename(message.md_file_path),
    )


# ── Chat comparison ──────────────────────────────────────────────────

@app.get("/api/compare")
async def api_compare_chats(
    chat_ids: str = Query(..., description="Comma-separated pair of chat IDs"),
    db: AsyncSession = Depends(get_db),
):
    ids = [int(x.strip()) for x in chat_ids.split(",") if x.strip().isdigit()]
    if len(ids) != 2:
        raise HTTPException(status_code=400, detail="Provide exactly 2 chat IDs")
    chats = []
    for cid in ids:
        chat = await get_chat_with_messages(db, cid)
        if not chat:
            raise HTTPException(status_code=404, detail=f"Chat {cid} not found")
        chats.append(ChatResponse.model_validate(chat))
    return chats


# ── Standalone run ───────────────────────────────────────────────────

if __name__ == "__main__":
    import uvicorn

    uvicorn.run("backend.main:app", host="127.0.0.1", port=8000, reload=True)