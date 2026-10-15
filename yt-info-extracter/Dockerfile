# ── YouTube Researcher — Production Dockerfile ─────────────────────────
# Multi-stage thinking:
#   Stage 1: Install Python dependencies + pre-download the embedding model
#   Stage 2: Copy app code and run
#
# Build:   docker build -t yt-researcher .
# Run:     docker run -d -p 8000:8000 --env-file backend/.env --name yt-researcher yt-researcher
# ────────────────────────────────────────────────────────────────────────

FROM python:3.11-slim

LABEL maintainer="Kapil Singh"
LABEL version="2.0"
LABEL description="YouTube Researcher — LangGraph + Groq + FAISS RAG"

WORKDIR /app

# ── 1. System deps (needed by some Python packages) ──────────────────
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        build-essential \
        gcc \
    && rm -rf /var/lib/apt/lists/*

# ── 2. Python dependencies (cached layer — only rebuilds on requirements change) ─
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# ── 3. Pre-download the HuggingFace embedding model at build time ────
#    This avoids a slow first-startup download and works offline.
RUN python -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2')"

# ── 4. Copy application code ─────────────────────────────────────────
#    .dockerignore ensures .env, __pycache__, .db, notebooks, etc. are excluded
COPY . .

# ── 5. Create runtime directories ────────────────────────────────────
RUN mkdir -p /app/backend/artifacts

# ── 6. Expose port ───────────────────────────────────────────────────
EXPOSE 8000

# ── 7. Health check ──────────────────────────────────────────────────
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/')" || exit 1

# ── 8. Start the server ─────────────────────────────────────────────
#    Module path is "backend.main:app" because we run from /app (project root)
#    and the backend/ directory is a Python package with __init__.py.
#
#    Environment variables (GROQ_API_KEY, API_KEY_2) are injected at runtime
#    via: docker run --env-file backend/.env ...
CMD ["uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8000"]
