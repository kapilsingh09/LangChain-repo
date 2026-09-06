"""
auth.py — Firebase Authentication Dependency.

WHAT IS A FASTAPI DEPENDENCY?
  A "dependency" is a function FastAPI calls automatically before
  your route handler runs. Think of it like a security guard at the
  door — it checks credentials and only lets the request through
  if everything is valid.

HOW FIREBASE AUTH WORKS IN THIS APP:
  1. User logs in on the React frontend using Firebase Authentication
  2. Firebase gives the frontend an "ID token" (a long JWT string)
  3. The frontend sends every API request with:
       Authorization: Bearer <the_token_here>
  4. THIS FILE verifies that token using Firebase Admin SDK
  5. If the token is valid → the route runs normally
  6. If the token is missing or invalid → HTTP 401 is returned immediately

USAGE IN ROUTES:
  Just add this as a parameter to any route function:

    from app.dependencies.auth import get_current_user

    @router.post("/research")
    async def run_research(
        request: ResearchRequest,
        current_user: dict = Depends(get_current_user)  ← add this
    ):
        uid = current_user["uid"]  ← now you have the user's ID

WHAT get_current_user() RETURNS:
  A dict with the user's decoded Firebase token info:
    {
      "uid": "firebase_user_id_string",
      "email": "user@example.com",   (if available)
      ...other Firebase token fields
    }
"""

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from firebase_admin import auth


# ── HTTP Bearer Token extractor ───────────────────────────────────────────────
# HTTPBearer is a FastAPI built-in that reads the "Authorization: Bearer ..."
# header and extracts the token part automatically.
# auto_error=False means we handle the "missing header" case ourselves
# (so we can return a more helpful error message).
_bearer_scheme = HTTPBearer(auto_error=False)


# ── The main dependency function ──────────────────────────────────────────────

async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(_bearer_scheme),
) -> dict:
    """
    FastAPI dependency: Verify Firebase ID token and return the user's info.

    How to use in a route:
        current_user: dict = Depends(get_current_user)

    Returns:
        dict with at minimum {"uid": "..."}

    Raises:
        HTTP 401 if token is missing, expired, or invalid.
    """

    # ── Step 1: Check that a token was actually sent ──────────────────────────
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            # Tell the client HOW to authenticate correctly
            headers={"WWW-Authenticate": "Bearer"},
            detail="Authentication required. Please include your Firebase ID token in the Authorization header.",
        )

    token = credentials.credentials  # This is the raw JWT string

    # ── Step 2: Verify the token with Firebase Admin SDK ─────────────────────
    # firebase_admin.auth.verify_id_token() checks:
    #   - The token's signature (was it actually signed by Firebase?)
    #   - The token's expiry (has it expired?)
    #   - The token's audience (was it issued for YOUR project?)
    # If any of these checks fail → it raises an exception
    try:
        decoded_token = auth.verify_id_token(token)

    except auth.ExpiredIdTokenError:
        # Token was valid but has expired — user needs to refresh their login
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            headers={"WWW-Authenticate": "Bearer"},
            detail="Your session has expired. Please log in again.",
        )

    except auth.InvalidIdTokenError:
        # Token is malformed, tampered with, or just wrong
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            headers={"WWW-Authenticate": "Bearer"},
            detail="Invalid authentication token. Please log in again.",
        )

    except Exception:
        # Catch-all for unexpected Firebase errors (network issues, etc.)
        # We intentionally don't leak the internal error message to the client
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            headers={"WWW-Authenticate": "Bearer"},
            detail="Authentication failed. Please try again.",
        )

    # ── Step 3: Return the decoded token info ─────────────────────────────────
    # decoded_token is a dict that always contains "uid" (the user's Firebase ID)
    # It may also contain "email", "name", etc. depending on how Firebase was set up.
    return decoded_token
