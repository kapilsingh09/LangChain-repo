import os
import json
import uuid
import asyncio
from datetime import datetime
from pathlib import Path
from typing import List, Optional

from fastapi import FastAPI, HTTPException, BackgroundTasks, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse, FileResponse
from fastapi.staticfiles import StaticFiles

from schemas import (
    ResearchRequest,
    ResearchResponse,
    ReportMetadata,
    ReportDetailResponse,
    HealthResponse,
    StreamEvent
)
from graph import (
    workflow,
    BASE_DIR,
    IMAGES_DIR,
    REPORTS_DIR,
    GOOGLE_API_KEY,
    GOOGLE_API_KEY2,
    GROQ_API_KEY,
    TAVILY_API_KEY,
    HF_TOKEN
)

app = FastAPI(
    title="Deep Multi-Agent Research System API",
    description="""
A production-ready FastAPI backend powered by LangGraph, Google Gemini, Groq, Tavily, and HuggingFace.

### Architecture Features:
- **Planner Agent**: Breaks complex technical questions into parallel sub-tasks.
- **Parallel Researchers**: Uses Tavily web search to gather deep technical evidence.
- **Evidence Collector**: Consolidates, categorizes, and deduplicates research findings.
- **QA Critic**: Scores evidence quality and provides constructive feedback.
- **Report Writer**: Generates comprehensive 1000-1500 word Markdown technical reports.
- **Diagram & Visual Generator**: Plans and synthesizes architecture diagrams via HuggingFace.
- **File Management & Streaming**: Real-time SSE streaming and report management endpoints.
    """,
    version="1.0.0"
)

# Enable CORS for cross-origin web apps
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount Static Directories for images and reports
IMAGES_DIR.mkdir(parents=True, exist_ok=True)
REPORTS_DIR.mkdir(parents=True, exist_ok=True)

app.mount("/images", StaticFiles(directory=str(IMAGES_DIR)), name="images")
app.mount("/reports", StaticFiles(directory=str(REPORTS_DIR)), name="reports")


@app.get("/", tags=["General"])
async def root():
    return {
        "message": "Welcome to Deep Multi-Agent Research API",
        "docs_url": "/docs",
        "health_url": "/health",
        "endpoints": {
            "research_sync": "POST /api/research",
            "research_stream": "POST /api/research/stream",
            "list_reports": "GET /api/reports",
            "get_report": "GET /api/reports/{filename}"
        }
    }


@app.get("/health", response_model=HealthResponse, tags=["General"])
async def health_check():
    services = {
        "google_api_key_configured": bool(GOOGLE_API_KEY),
        "google_api_key_secondary_configured": bool(GOOGLE_API_KEY2),
        "groq_api_key_configured": bool(GROQ_API_KEY),
        "tavily_api_key_configured": bool(TAVILY_API_KEY),
        "huggingface_token_configured": bool(HF_TOKEN),
    }
    all_critical_present = bool(GOOGLE_API_KEY and GROQ_API_KEY)
    return HealthResponse(
        status="healthy" if all_critical_present else "degraded",
        services=services,
        version="1.0.0"
    )


@app.post(
    "/api/research",
    response_model=ResearchResponse,
    summary="Execute End-to-End Deep Research",
    tags=["Research"]
)
async def execute_research(request: ResearchRequest):
    """
    Executes the complete multi-agent research pipeline synchronously and returns the complete final state.
    """
    thread_id = request.thread_id or f"research_{uuid.uuid4().hex[:10]}"
    config = {
        "configurable": {
            "thread_id": thread_id
        }
    }
    initial_state = {
        "question": request.question
    }

    try:
        # Run workflow in worker thread
        final_state = await asyncio.to_thread(
            workflow.invoke,
            initial_state,
            config=config
        )

        return ResearchResponse(
            thread_id=thread_id,
            question=request.question,
            status="completed",
            research_topics_planned=final_state.get("research_tropics_planned", []),
            research_results=final_state.get("research_results", []),
            critique=final_state.get("critique"),
            final_report=final_state.get("final_report", ""),
            saved_file_path=final_state.get("saved_file_path"),
            web_search_performed=final_state.get("web_search_performed", False),
            image_specs=final_state.get("image_specs", [])
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Research pipeline execution failed: {str(e)}"
        )


@app.post(
    "/api/research/stream",
    summary="Stream Deep Research Execution (Server-Sent Events)",
    tags=["Research"]
)
async def stream_research(request: ResearchRequest):
    """
    Streams step-by-step progress and node outputs via Server-Sent Events (SSE).
    """
    thread_id = request.thread_id or f"stream_{uuid.uuid4().hex[:10]}"
    config = {
        "configurable": {
            "thread_id": thread_id
        }
    }
    initial_state = {
        "question": request.question
    }

    async def event_generator():
        yield f"data: {json.dumps({'event': 'started', 'thread_id': thread_id, 'question': request.question})}\n\n"

        try:
            # LangGraph stream runs synchronously so we iterate over chunks
            for chunk in workflow.stream(initial_state, config=config):
                for node_name, node_output in chunk.items():
                    event_payload = {
                        "event": "node_update",
                        "node": node_name,
                        "data": node_output
                    }
                    yield f"data: {json.dumps(event_payload, default=str)}\n\n"
                    # Small async yield to flush buffer to client
                    await asyncio.sleep(0.01)

            # Retrieve final state from checkpointer
            state_snapshot = workflow.get_state(config)
            final_data = state_snapshot.values if state_snapshot else {}

            completion_payload = {
                "event": "completed",
                "thread_id": thread_id,
                "data": {
                    "saved_file_path": final_data.get("saved_file_path"),
                    "final_report": final_data.get("final_report"),
                    "image_specs": final_data.get("image_specs", []),
                    "critique": final_data.get("critique")
                }
            }
            yield f"data: {json.dumps(completion_payload, default=str)}\n\n"

        except Exception as e:
            error_payload = {
                "event": "error",
                "error": str(e)
            }
            yield f"data: {json.dumps(error_payload)}\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"
        }
    )


@app.get(
    "/api/reports",
    response_model=List[ReportMetadata],
    summary="List all generated research reports",
    tags=["Reports"]
)
async def list_reports():
    """
    Returns metadata for all generated research reports saved in the reports directory.
    """
    reports = []
    if REPORTS_DIR.exists():
        for file in sorted(REPORTS_DIR.glob("*.md"), key=lambda f: f.stat().st_mtime, reverse=True):
            stat = file.stat()
            title = file.stem.replace("_report", "").replace("_", " ").title()
            reports.append(
                ReportMetadata(
                    filename=file.name,
                    title=title,
                    file_path=str(file),
                    size_bytes=stat.st_size,
                    created_at=datetime.fromtimestamp(stat.st_mtime).isoformat(),
                    download_url=f"/reports/{file.name}"
                )
            )
    return reports


@app.get(
    "/api/reports/{filename}",
    response_model=ReportDetailResponse,
    summary="Get report markdown content by filename",
    tags=["Reports"]
)
async def get_report(filename: str):
    """
    Fetch the complete Markdown report content and file metadata.
    """
    file_path = REPORTS_DIR / filename
    if not file_path.exists() or not file_path.is_file():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Report '{filename}' not found."
        )

    content = file_path.read_text(encoding="utf-8")
    stat = file_path.stat()
    title = file_path.stem.replace("_report", "").replace("_", " ").title()

    metadata = ReportMetadata(
        filename=file_path.name,
        title=title,
        file_path=str(file_path),
        size_bytes=stat.st_size,
        created_at=datetime.fromtimestamp(stat.st_mtime).isoformat(),
        download_url=f"/reports/{file_path.name}"
    )

    return ReportDetailResponse(
        filename=filename,
        content=content,
        metadata=metadata
    )


@app.delete(
    "/api/reports/{filename}",
    summary="Delete a report file",
    tags=["Reports"]
)
async def delete_report(filename: str):
    """
    Deletes a generated report from the reports directory.
    """
    file_path = REPORTS_DIR / filename
    if not file_path.exists():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Report '{filename}' does not exist."
        )
    file_path.unlink()
    return {"message": f"Report '{filename}' successfully deleted."}
