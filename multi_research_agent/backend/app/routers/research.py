import json
import uuid
import asyncio
from fastapi import APIRouter, HTTPException, status
from fastapi.responses import StreamingResponse

from app.schemas.research import ResearchRequest, ResearchResponse
from app.graph.workflow import workflow

router = APIRouter(prefix="/api", tags=["Research"])


@router.post(
    "/research",
    response_model=ResearchResponse,
    summary="Execute End-to-End Deep Research"
)
async def execute_research(request: ResearchRequest):
    """
    Executes the multi-agent deep research pipeline synchronously and returns the complete final state.
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


@router.post(
    "/research/stream",
    summary="Stream Deep Research Execution (Server-Sent Events)"
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
            for chunk in workflow.stream(initial_state, config=config):
                for node_name, node_output in chunk.items():
                    event_payload = {
                        "event": "node_update",
                        "node": node_name,
                        "data": node_output
                    }
                    yield f"data: {json.dumps(event_payload, default=str)}\n\n"
                    await asyncio.sleep(0.01)

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
