"""
research.py — The /research API routes.

POST /research
  - Requires: Firebase ID token in Authorization header
  - Accepts: { "question": "your research question" }
  - Runs the full LangGraph research pipeline (UNCHANGED)
  - Saves result to Firestore under users/{uid}/researches/{id}
  - Returns: the completed report + metadata (blocks until done)

POST /research/stream  ← NEW
  - Same auth + same pipeline — but streams live progress via SSE
  - Client receives real-time events as each agent node completes
  - Final report arrives in the "complete" event
  - Perfect for the frontend progress UI

HOW TO TEST /research/stream:
  curl -X POST http://localhost:8000/research/stream
    -H "Content-Type: application/json"
    -H "Authorization: Bearer YOUR_TOKEN"
    -H "Accept: text/event-stream"
    -d '{"question": "How does quantum computing work?"}'
"""

import asyncio
import json
import threading
import uuid

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import StreamingResponse

from app.models import ResearchRequest, ResearchResponse
from app.graph import workflow
from app.dependencies.auth import get_current_user
from app.services.firestore import save_research


router = APIRouter()


# ── Streaming helper: map LangGraph node names → SSE events ──────────────────
# The research graph runs these nodes in order:
#   planner → researcher (×3 parallel) → collector → critic → report_writer
#   → image_subgraph → file_saver
#
# workflow.stream(mode="updates") yields {node_name: state_updates} after
# each node completes. We map node names to user-friendly stage events.

def _build_stage_event(node_name: str, updates: dict, researcher_count: int) -> dict | None:
    """
    Convert a LangGraph node completion into a frontend-friendly SSE event.

    Returns a dict that will be JSON-serialized and sent as: data: {...}\n\n
    Returns None if we don't want to emit an event for this node.
    """
    # Base event template
    base = {"type": "stage_update"}

    if node_name == "planner":
        tasks = updates.get("research_tropics_planned", [])
        count = len(tasks)
        return {**base, "stage": "planning", "status": "completed",
                "message": f"Research plan created — {count} topics identified"}

    elif node_name == "researcher":
        # Fires once per parallel researcher. researcher_count tracks how many done.
        web = updates.get("web_search_performed", False)
        event = {**base, "stage": "researching", "status": "running",
                 "message": f"Research task {researcher_count + 1} completed",
                 "researcher_count": researcher_count + 1}
        if web:
            # Also emit a web_search event the first time we detect it
            event["web_search_detected"] = True
        return event

    elif node_name == "collector":
        return {**base, "stage": "collecting", "status": "completed",
                "message": "Evidence organized and deduplicated"}

    elif node_name == "critic":
        # Try to extract the score from the critique text
        critique = updates.get("critique", "")
        score_line = next((l for l in critique.split("\n") if "Score:" in l), "")
        score = score_line.replace("Overall Score:", "").strip() if score_line else ""
        msg = f"Quality check complete — Score: {score}" if score else "Quality check complete"
        return {**base, "stage": "critique", "status": "completed", "message": msg}

    elif node_name == "report_writer":
        return {**base, "stage": "writing", "status": "completed",
                "message": "Research report written"}

    elif node_name in ("image_subgraph", "decide_images", "generate_images"):
        return {**base, "stage": "finalizing", "status": "completed",
                "message": "Visuals and diagrams added"}

    elif node_name == "file_saver":
        return {**base, "stage": "saving", "status": "completed",
                "message": "Report saved to disk"}

    # Unknown node — emit a generic event so frontend knows something happened
    return {**base, "stage": node_name, "status": "completed", "message": f"{node_name} completed"}


# ── POST /research/stream — SSE Streaming Endpoint ───────────────────────────

@router.post(
    "/stream",
    summary="Run Deep Research with Live Progress (SSE)",
    description=(
        "Same as POST /research but streams real-time progress events via "
        "Server-Sent Events (text/event-stream). Each agent node completion "
        "emits an event. The final 'complete' event contains the full report."
    ),
)
async def stream_research(
    request: ResearchRequest,
    http_request: Request,
    current_user: dict = Depends(get_current_user),
):
    """
    SSE streaming research endpoint.

    The frontend connects to this and receives events like:
        data: {"type": "stage_update", "stage": "planning", "status": "completed", ...}
        data: {"type": "stage_update", "stage": "researching", ...}
        data: {"type": "complete", "research_id": "...", "data": {...}}
        data: {"type": "error", "message": "..."}

    HOW IT WORKS INTERNALLY:
        1. workflow.stream() is a synchronous generator — it yields state updates
           after each LangGraph node completes
        2. We run it in a background thread (so it doesn't block the async server)
        3. The thread puts events into an asyncio.Queue via loop.call_soon_threadsafe()
        4. The async generator reads from the queue and yields SSE-formatted text
        5. If client disconnects, cancel_event aborts the background thread to prevent token waste
    """
    uid = current_user["uid"]
    question = request.question.strip()
    thread_id = str(uuid.uuid4())
    config = {"configurable": {"thread_id": thread_id}}

    # Get the currently running event loop safely
    loop = asyncio.get_running_loop()

    # asyncio.Queue is the bridge between the sync thread and async generator
    queue: asyncio.Queue = asyncio.Queue()

    # Cancellation event to stop the pipeline if the client disconnects
    cancel_event = threading.Event()

    def run_pipeline():
        """
        Runs in a background thread.
        Uses workflow.stream() to get real node-by-node events.
        Pushes SSE events into the asyncio queue.
        Halts immediately if cancel_event is set.
        """
        try:
            final_state: dict = {"question": question}
            researcher_count = 0

            for chunk in workflow.stream(
                {"question": question},
                config=config,
                stream_mode="updates",
            ):
                # Check for cancellation before processing next node
                if cancel_event.is_set():
                    print(f"🛑 Stream research cancelled by client for thread {thread_id}")
                    return

                # Each chunk is {node_name: {field: value, ...}}
                node_name = list(chunk.keys())[0]
                updates = chunk[node_name] or {}

                # Accumulate state, handling special merge rules
                for key, val in updates.items():
                    if key in ("research_results", "messages") and isinstance(val, list):
                        final_state.setdefault(key, [])
                        final_state[key] = final_state[key] + val
                    elif key == "web_search_performed":
                        final_state[key] = final_state.get(key, False) or bool(val)
                    else:
                        final_state[key] = val

                # Build and emit the SSE event for this node
                event = _build_stage_event(node_name, updates, researcher_count)

                if node_name == "researcher":
                    researcher_count += 1
                    if updates.get("web_search_performed"):
                        web_event = {
                            "type": "stage_update",
                            "stage": "web_search",
                            "status": "completed",
                            "message": f"Web search completed for task {researcher_count}",
                        }
                        loop.call_soon_threadsafe(
                            queue.put_nowait, f"data: {json.dumps(web_event)}\n\n"
                        )

                if event:
                    loop.call_soon_threadsafe(
                        queue.put_nowait, f"data: {json.dumps(event)}\n\n"
                    )

            if cancel_event.is_set():
                return

            # ── Pipeline complete — save to Firestore ─────────────────────────
            final_report = final_state.get("final_report", "")
            critique = final_state.get("critique", "")
            web_searched = final_state.get("web_search_performed", False)
            saved_path = final_state.get("saved_file_path", "")

            try:
                save_research(
                    uid=uid,
                    question=question,
                    final_report=final_report,
                    critique=critique,
                    web_search_performed=web_searched,
                    saved_file_path=saved_path,
                    research_id=thread_id,
                )
            except Exception as e:
                print(f"⚠️  Warning: Firestore save failed in stream: {e}")

            # Emit the final "complete" event with the full research data
            complete_event = {
                "type": "complete",
                "research_id": thread_id,
                "data": {
                    "question": question,
                    "final_report": final_report,
                    "web_search_performed": web_searched,
                    "critique": critique,
                    "saved_file_path": saved_path,
                },
            }
            loop.call_soon_threadsafe(
                queue.put_nowait, f"data: {json.dumps(complete_event)}\n\n"
            )

        except Exception as e:
            if not cancel_event.is_set():
                print(f"❌ Stream research pipeline error: {e}")
                error_event = {"type": "error", "message": "Research pipeline failed. Please try again."}
                loop.call_soon_threadsafe(
                    queue.put_nowait, f"data: {json.dumps(error_event)}\n\n"
                )
        finally:
            # Sentinel: None signals the async generator to stop
            loop.call_soon_threadsafe(queue.put_nowait, None)

    # Start the pipeline in a background thread
    thread = threading.Thread(target=run_pipeline, daemon=True)
    thread.start()

    # Emit the first "researching started" event immediately so the UI responds right away
    start_event = json.dumps({
        "type": "stage_update",
        "stage": "planning",
        "status": "running",
        "message": "Creating your research plan...",
    })

    async def generate():
        """
        Async generator that reads events from the queue and yields SSE text.
        Each SSE message format: "data: {json}\n\n"
        """
        try:
            # Immediately tell the frontend we've started
            yield f"data: {start_event}\n\n"

            keepalive_counter = 0

            while True:
                # If client has disconnected, stop generating and abort pipeline
                if await http_request.is_disconnected():
                    cancel_event.set()
                    break

                try:
                    # Wait up to 15 seconds for the next event
                    item = await asyncio.wait_for(queue.get(), timeout=15.0)
                except asyncio.TimeoutError:
                    if await http_request.is_disconnected():
                        cancel_event.set()
                        break
                    keepalive_counter += 1
                    yield f": keepalive {keepalive_counter}\n\n"
                    continue

                if item is None:
                    # Sentinel received — pipeline finished
                    break

                yield item
        finally:
            # Signal the background thread to halt if disconnected early
            cancel_event.set()

    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


# ── POST /research — Original Blocking Endpoint ───────────────────────────────

@router.post(
    "",
    response_model=ResearchResponse,
    summary="Run Deep Research (Authenticated)",
    description=(
        "Submit a research question and receive a detailed markdown report "
        "generated by a multi-agent AI pipeline with optional web search. "
        "Requires a valid Firebase ID token in the Authorization header. "
        "BLOCKING: waits for full completion. Use /research/stream for live progress."
    ),
)
async def run_research(
    request: ResearchRequest,
    current_user: dict = Depends(get_current_user),
) -> ResearchResponse:
    """Main research endpoint (authenticated, blocking)."""

    question = request.question.strip()
    uid = current_user["uid"]
    thread_id = str(uuid.uuid4())
    config = {"configurable": {"thread_id": thread_id}}

    try:
        final_state = workflow.invoke({"question": question}, config=config)

    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))

    except Exception as e:
        print(f"❌ Research pipeline error: {e}")
        raise HTTPException(
            status_code=500,
            detail="The research pipeline encountered an internal error. Please try again.",
        )

    final_report = final_state.get("final_report", "Report generation failed.")
    saved_file_path = final_state.get("saved_file_path", "")
    web_search_performed = final_state.get("web_search_performed", False)
    critique = final_state.get("critique", "")

    try:
        save_research(
            uid=uid,
            question=question,
            final_report=final_report,
            critique=critique,
            web_search_performed=web_search_performed,
            saved_file_path=saved_file_path,
            research_id=thread_id,
        )
    except Exception as e:
        print(f"⚠️  Warning: Failed to save research to Firestore: {e}")


    # Return the same response structure as before — UNCHANGED
    return ResearchResponse(
        question=question,
        final_report=final_report,
        saved_file_path=saved_file_path,
        web_search_performed=web_search_performed,
        critique=critique,
    )

