"""
firestore.py — All Firestore Database Operations.

WHAT IS FIRESTORE?
  Firestore is a cloud database by Google/Firebase.
  Think of it like a JSON tree stored in the cloud.
  Each "document" is like a Python dict.

OUR DATA STRUCTURE:
  Firestore
  └── users/
      └── {firebase_uid}/          ← one entry per logged-in user
          └── researches/
              └── {research_id}/   ← one entry per research run
                  ├── research_id
                  ├── user_id
                  ├── question
                  ├── status
                  ├── final_report
                  ├── critique
                  ├── web_search_performed
                  ├── saved_file_path
                  ├── created_at
                  └── completed_at

SECURITY:
  Every function here takes a `uid` parameter.
  We always filter by that uid — so User A can NEVER
  read or overwrite User B's data.
  (Firestore Security Rules on the Firebase Console
   provide an additional layer of protection.)

FUNCTIONS IN THIS FILE:
  save_research()         → Save a completed research doc
  get_research_history()  → List all docs for a user
  get_research_by_id()    → Fetch one specific doc (with ownership check)
"""

import uuid
from datetime import datetime, timezone
from typing import Optional

from firebase_admin import firestore


def _get_db():
    """
    Get a Firestore client.

    We call this lazily (inside each function) instead of at module
    import time, because Firebase must be initialized first (in main.py).
    Calling firestore.client() before initialize_app() would crash.
    """
    return firestore.client()


# ── Save Research ─────────────────────────────────────────────────────────────

def save_research(
    uid: str,
    question: str,
    final_report: str,
    critique: str = "",
    web_search_performed: bool = False,
    saved_file_path: str = "",
    research_id: Optional[str] = None,
) -> str:
    """
    Save a completed research result to Firestore.

    Parameters:
      uid                   → The Firebase UID of the logged-in user
      question              → The original research question
      final_report          → The full markdown research report
      critique              → The critic agent's evaluation text
      web_search_performed  → Whether any researcher used web search
      saved_file_path       → Path where the .md file was saved on disk
      research_id           → Optional: supply your own ID (default: auto-generated)

    Returns:
      The research_id (string) — useful so the API can return it in the response.

    Path written to:
      users/{uid}/researches/{research_id}
    """
    db = _get_db()

    # Generate a unique ID for this research if not provided
    if not research_id:
        research_id = str(uuid.uuid4())

    # Get current UTC time — always store timestamps in UTC
    now = datetime.now(timezone.utc)

    # Build the document that will be saved to Firestore
    doc_data = {
        "research_id": research_id,
        "user_id": uid,                   # Owner of this research
        "question": question,
        "status": "completed",
        "final_report": final_report,
        "critique": critique,
        "web_search_performed": web_search_performed,
        "saved_file_path": saved_file_path,
        "created_at": now,
        "completed_at": now,
    }

    # Path: users/{uid}/researches/{research_id}
    # .set() creates or overwrites the document at this exact path
    db.collection("users").document(uid).collection("researches").document(research_id).set(doc_data)

    print(f"✅ Research saved to Firestore: users/{uid}/researches/{research_id}")
    return research_id


# ── Get Research History ──────────────────────────────────────────────────────

def get_research_history(uid: str) -> list[dict]:
    """
    Return a list of all research documents for the given user.

    Only returns summary fields (not the full report) to keep the
    response payload small. The frontend can fetch the full report
    separately using get_research_by_id().

    Parameters:
      uid → The Firebase UID of the logged-in user

    Returns:
      A list of dicts, each with: research_id, question, status, created_at
      Sorted newest-first.
    """
    db = _get_db()

    # Query all documents in users/{uid}/researches/
    # Ordered by created_at descending (newest first)
    docs = (
        db.collection("users")
        .document(uid)
        .collection("researches")
        .order_by("created_at", direction=firestore.Query.DESCENDING)  # type: ignore[attr-defined]
        .stream()
    )

    results = []
    for doc in docs:
        data = doc.to_dict()

        # Return only the summary fields — not the full report (can be very large)
        results.append({
            "research_id": data.get("research_id", doc.id),
            "question": data.get("question", ""),
            "status": data.get("status", "unknown"),
            "web_search_performed": data.get("web_search_performed", False),
            # Convert Firestore timestamp to ISO 8601 string for JSON serialization
            "created_at": (
                data["created_at"].isoformat()
                if data.get("created_at")
                else None
            ),
        })

    return results


# ── Get Single Research ───────────────────────────────────────────────────────

def get_research_by_id(uid: str, research_id: str) -> Optional[dict]:
    """
    Fetch a single research document by ID.

    SECURITY: Also verifies that the document belongs to `uid`.
    If User A tries to access User B's research_id, this returns None
    (and the route will return HTTP 404 — we never reveal ownership).

    Parameters:
      uid         → The Firebase UID of the requesting user
      research_id → The ID of the research document

    Returns:
      The full document dict (including final_report), or None if:
        - The document doesn't exist
        - The document doesn't belong to `uid` (ownership check)
    """
    db = _get_db()

    # Direct path lookup: users/{uid}/researches/{research_id}
    # Because we use the uid in the path, a user can ONLY ever access
    # documents inside their own subtree — Firestore enforces this structurally.
    doc_ref = (
        db.collection("users")
        .document(uid)
        .collection("researches")
        .document(research_id)
    )

    doc = doc_ref.get()

    if not doc.exists:
        return None

    data = doc.to_dict()

    # Extra safety check: verify the user_id field matches
    # (Defense in depth — in case the path structure ever changes)
    if data.get("user_id") != uid:
        return None

    # Convert Firestore timestamps to ISO strings for JSON serialization
    if data.get("created_at"):
        data["created_at"] = data["created_at"].isoformat()
    if data.get("completed_at"):
        data["completed_at"] = data["completed_at"].isoformat()

    return data
