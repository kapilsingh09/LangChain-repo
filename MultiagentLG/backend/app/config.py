"""
config.py — Load and validate all environment variables (API keys).

We load from a .env file using python-dotenv.
If any required key is missing, we raise a clear error message
so the developer knows exactly what to fix.
"""

import os
from dotenv import load_dotenv

# Load variables from the .env file into the environment.
# This must happen BEFORE we try to read os.getenv().
load_dotenv()


def _require(key: str) -> str:
    """
    Get an environment variable or raise a helpful error if it's missing.
    This prevents the server from starting with broken config.
    """
    value = os.getenv(key)
    if not value:
        raise ValueError(
            f"❌ Missing required environment variable: '{key}'\n"
            f"   Add it to your .env file:  {key}=your_value_here"
        )
    return value


# ---------------------------------------------------------
# Required API Keys — existing (DO NOT CHANGE)
# These MUST be present in your .env file.
# ---------------------------------------------------------
HF_TOKEN = _require("HF_TOKEN")                  # Hugging Face (image generation)
GOOGLE_API_KEY = _require("GOOGLE_API_KEY")       # Google Gemini (main LLM)
GOOGLE_API_KEY2 = _require("GOOGLE_API_KEY2")     # Google Gemini (secondary LLM)
GROQ_API_KEY = _require("GROQ_API_KEY")           # Groq (report writer LLM)
TAVILY_API_KEY = _require("TAVILY_API_KEY")       # Tavily (web search)

# ---------------------------------------------------------
# Firebase — NEW (required for authentication + database)
# Get these from Firebase Console → Project Settings → Service Accounts
# → Generate new private key → copy values from downloaded JSON
# ---------------------------------------------------------
FIREBASE_PROJECT_ID = _require("FIREBASE_PROJECT_ID")       # e.g. "my-project-12345"
FIREBASE_CLIENT_EMAIL = _require("FIREBASE_CLIENT_EMAIL")   # service account email
FIREBASE_PRIVATE_KEY = _require("FIREBASE_PRIVATE_KEY")     # long key starting with -----BEGIN...

# ---------------------------------------------------------
# CORS — Optional (has a safe default for local development)
# In production, set this to your actual frontend URL.
# e.g. FRONTEND_URL=https://my-app.web.app
# ---------------------------------------------------------
# os.getenv() with a default means this variable is OPTIONAL.
# If not set in .env, the fallback "http://localhost:5173" is used.
# (5173 is the default port for Vite — the React dev server)
FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:5173")
