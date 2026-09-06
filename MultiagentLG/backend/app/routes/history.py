"""
history.py — Research History and Single-Research API Routes.

ENDPOINTS IN THIS FILE:
  GET /research/history
    → Returns a list of all research runs for the logged-in user
    → Requires Firebase authentication

  GET /research/{research_id}
    → Returns the full details of one specific research run
    → Requires Firebase authentication
    → Ownership check: you can only access YOUR OWN research

SECURITY:
  Both routes require a valid Firebase ID token.
  User A can NEVER access User B's research — not even if they guess
  the research_id, because we always filter by uid.

HOW TO REGISTER THESE ROUTES:
  In main.py:
    from app.routes.history import router as history_router
    app.include_router(history_router, prefix="/research", tags=["Research History"])
"""

from fastapi import APIRouter, Depends, HTTPException, status

from app.dependencies.auth import get_current_user
from app.services.firestore import (
    get_research_history,
    get_research_by_id,
    delete_research,
    delete_all_research,
)


# Create a router — main.py will register this with the /research prefix
router = APIRouter()


# ── GET /research/history ─────────────────────────────────────────────────────

@router.get(
    "/history",
    summary="Get My Research History",
    description=(
        "Returns a list of all past research runs for the authenticated user. "
        "Requires a valid Firebase ID token in the Authorization header."
    ),
    tags=["Research History"],
)
async def get_history(
    # This line does all the auth work automatically!
    # FastAPI calls get_current_user() before this function runs.
    # If the token is missing/invalid → 401 is returned, this function never runs.
    current_user: dict = Depends(get_current_user),
) -> dict:
    """
    Return the authenticated user's full research history.

    Response example:
    {
      "researches": [
        {
          "research_id": "abc-123",
          "question": "How does transformer attention work?",
          "status": "completed",
          "web_search_performed": true,
          "created_at": "2024-01-15T10:30:00+00:00"
        },
        ...
      ]
    }
    """
    # Extract the user's Firebase UID from the verified token
    uid = current_user["uid"]

    try:
        # Fetch all research docs for this user from Firestore
        # This function already filters by uid — User A can't see User B's data
        researches = get_research_history(uid)

        return {"researches": researches}

    except Exception as e:
        # Don't leak internal error details to the client
        print(f"❌ Error fetching history for user {uid}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch research history. Please try again.",
        )


# ── DELETE /research/history ──────────────────────────────────────────────────

@router.delete(
    "/history",
    summary="Clear All Research History",
    description=(
        "Deletes all past research runs for the authenticated user. "
        "Requires a valid Firebase ID token in the Authorization header."
    ),
    tags=["Research History"],
)
async def clear_all_history(
    current_user: dict = Depends(get_current_user),
) -> dict:
    """Delete all research documents for the current user."""
    uid = current_user["uid"]

    try:
        deleted_count = delete_all_research(uid=uid)
        return {
            "status": "ok",
            "message": f"Successfully cleared {deleted_count} research records.",
            "deleted_count": deleted_count,
        }

    except Exception as e:
        print(f"❌ Error clearing history for user {uid}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to clear research history. Please try again.",
        )


# ── GET /research/{research_id} ───────────────────────────────────────────────

@router.get(
    "/{research_id}",
    summary="Get a Single Research Result",
    description=(
        "Returns the full details of a specific research run, including the final report. "
        "Only the owner of the research can access it. "
        "Returns 404 if not found OR if it belongs to another user (for security)."
    ),
    tags=["Research History"],
)
async def get_single_research(
    research_id: str,
    current_user: dict = Depends(get_current_user),  # Auth check happens here
) -> dict:
    """
    Return one specific research document (full details including report).

    SECURITY NOTE:
      We return HTTP 404 (not 403) when a user tries to access
      another user's research. This is intentional — revealing that
      a resource EXISTS (even with 403) leaks information. 404 tells
      the requester nothing useful about ownership.

    Response example:
    {
      "research_id": "abc-123",
      "user_id": "firebase-uid-here",
      "question": "How does transformer attention work?",
      "status": "completed",
      "final_report": "# Transformer Attention...\n\n## Executive Summary...",
      "critique": "Sufficient Evidence: True\nOverall Score: 8/10...",
      "web_search_performed": true,
      "saved_file_path": "reports/how_does_transformer..._report.md",
      "created_at": "2024-01-15T10:30:00+00:00",
      "completed_at": "2024-01-15T10:35:42+00:00"
    }
    """
    # Extract the user's Firebase UID from the verified token
    uid = current_user["uid"]

    try:
        # Fetch the doc — this function does the ownership check internally.
        # If research_id doesn't exist OR belongs to a different user → returns None.
        research = get_research_by_id(uid=uid, research_id=research_id)

    except Exception as e:
        # Unexpected error (e.g., Firestore connectivity issue)
        print(f"❌ Error fetching research {research_id} for user {uid}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch research. Please try again.",
        )

    # Return 404 whether the doc doesn't exist OR belongs to another user.
    # NEVER reveal WHY the 404 happened — that's a security best practice.
    if research is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Research not found.",
        )

    return research


# ── DELETE /research/{research_id} ────────────────────────────────────────────

@router.delete(
    "/{research_id}",
    summary="Delete a Single Research Result",
    description=(
        "Deletes a specific research document. Only the owner can delete it. "
        "Returns 404 if not found or if it belongs to another user."
    ),
    tags=["Research History"],
)
async def delete_single_research(
    research_id: str,
    current_user: dict = Depends(get_current_user),
) -> dict:
    """Delete a specific research document for the authenticated user."""
    uid = current_user["uid"]

    try:
        deleted = delete_research(uid=uid, research_id=research_id)
    except Exception as e:
        print(f"❌ Error deleting research {research_id} for user {uid}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete research. Please try again.",
        )

    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Research not found.",
        )

    return {
        "status": "ok",
        "message": "Research deleted successfully.",
        "research_id": research_id,
    }
