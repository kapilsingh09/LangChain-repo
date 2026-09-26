# ```python
import time
from urllib.parse import urlparse, parse_qs

import uvicorn
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
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
    model: str | None = None
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
        "model": "free",
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
            "thread_id": request.session_id
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

    def generate():
        try:

            # stream_mode="values"
            # gives the complete state after every node
            for chunk in chatbot.stream(
                initial_state,
                config=config,
                stream_mode="values"
            ):

                messages = chunk.get("messages", [])

                if not messages:
                    continue

                last = messages[-1]


                # Ignore user's HumanMessage
                if isinstance(last, HumanMessage):
                    continue


                if not hasattr(last, "content"):
                    continue


                content = last.content


                # ──────────────────────────────
                # Case 1: normal string response
                # ──────────────────────────────

                if isinstance(content, str):
                    yield content


                # ──────────────────────────────
                # Case 2: Gemini structured content
                # ──────────────────────────────

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
        reload=True
    )
# ```

# The key fix is this part:

# ```python
# content = last.content

# if isinstance(content, str):
#     yield content

# elif isinstance(content, list):
#     for item in content:
#         if isinstance(item, dict):
#             text = item.get("text")
#             if text:
#                 yield text
# ```

# Now `StreamingResponse` will receive **strings**, not a list, so the:

# ```text
# AttributeError: 'list' object has no attribute 'encode'
# ```

# error should be gone.

# Also, your duplicate:

# ```python
# model
# api_key
# model
# api_key
# ```

# has been fixed.
