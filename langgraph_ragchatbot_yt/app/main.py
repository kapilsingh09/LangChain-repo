import time
from pathlib import Path
from urllib.parse import urlparse, parse_qs

import uvicorn
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import Literal
from langchain_core.messages import HumanMessage
from dotenv import load_dotenv

load_dotenv()

from app.graph.workflow import graph as chatbot


app = FastAPI(title="YouTube RAG Chatbot API")


# ──────────────────────────────────────────────
# CORS
# ──────────────────────────────────────────────

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ──────────────────────────────────────────────
# Request schema
# ──────────────────────────────────────────────

class AskRequest(BaseModel):
    youtube_url: str
    question: str
    session_id: str
    model: Literal["gemini", "groq"] = "gemini"
    api_key: str | None = None


# ──────────────────────────────────────────────
# Helpers
# ──────────────────────────────────────────────

def extract_video_id(youtube_url: str) -> str:
    """Extract the YouTube video ID from a watch URL."""

    parsed = urlparse(youtube_url)
    params = parse_qs(parsed.query)

    video_ids = params.get("v", [])

    if not video_ids:
        raise HTTPException(
            status_code=400,
            detail=f"Could not extract video ID from URL: {youtube_url}"
        )

    return video_ids[0]


# ──────────────────────────────────────────────
# Routes
# ──────────────────────────────────────────────

@app.get("/")
async def read_root():
    return {
        "message": "YouTube RAG Chatbot API is running."
    }


@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "timestamp": time.time()
    }


@app.post("/ask")
async def ask(request: AskRequest):
    """
    Main chat endpoint.

    Chrome extension sends:

    {
        "youtube_url": "https://www.youtube.com/watch?v=...",
        "question": "...",
        "session_id": "sess_...",
        "model": "gemini",
        "api_key": ""
    }

    The video ID is extracted and the LangGraph workflow
    is executed. The final answer is streamed as plain text.
    """

    # ──────────────────────────────────────────
    # Extract YouTube video ID
    # ──────────────────────────────────────────

    video_id = extract_video_id(request.youtube_url)


    # ──────────────────────────────────────────
    # LangGraph config
    # ──────────────────────────────────────────

    config = {
        "configurable": {
            "thread_id": request.session_id,
            "model": request.model,
        }
    }


    # ──────────────────────────────────────────
    # Initial LangGraph state
    # ──────────────────────────────────────────

    initial_state = {
        "messages": [
            HumanMessage(content=request.question)
        ],
        "video_id": video_id,
    }


    # ──────────────────────────────────────────
    # Generate response
    # ──────────────────────────────────────────

    async def generate():
        try:
            start_time = time.time()
            first_token_received = False

            # stream_mode="messages" streams LLM message chunks as they are generated
            async for event in chatbot.astream(
                initial_state,
                config=config,
                stream_mode="messages"
            ):
                chunk, metadata = event

                # Check if this chunk is from the final generation node (or chat node)
                # and contains actual content
                if metadata.get("langgraph_node") in ["generate", "chat"]:
                    content = chunk.content

                    if content:
                        if not first_token_received:
                            first_token_received = True
                            elapsed = time.time() - start_time
                            print(f"[LLM] First token received after {elapsed:.2f}s")

                        # Handle strings safely
                        if isinstance(content, str):
                            yield content

                        # Handle structured content safely
                        elif isinstance(content, list):
                            for item in content:
                                if isinstance(item, dict):
                                    text = item.get("text")
                                    if text:
                                        yield text
                                elif isinstance(item, str):
                                    yield item

        except Exception as e:
            yield f"\n\n[ERROR]: {str(e)}"


    # ──────────────────────────────────────────
    # Return streaming response
    # ──────────────────────────────────────────

    return StreamingResponse(
        generate(),
        media_type="text/plain"
    )


# ──────────────────────────────────────────────
# Dev server
# ──────────────────────────────────────────────

if __name__ == "__main__":

    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        reload_dirs=[str(Path(__file__).resolve().parents[1])],
    )
