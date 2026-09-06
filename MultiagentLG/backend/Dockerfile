# ─────────────────────────────────────────────────────────────────────────────
# Dockerfile — Build the Deep Research Agent for Google Cloud Run
#
# HOW TO BUILD AND RUN LOCALLY:
#   docker build -t deep-researcher .
#   docker run -p 8080:8080 --env-file .env deep-researcher
#   Then visit: http://localhost:8080/health
#
# HOW CLOUD RUN USES THIS:
#   1. Cloud Run builds this image from your source code
#   2. It injects environment variables (from Cloud Run secrets/env)
#   3. It starts the container and sends traffic to PORT (default 8080)
#
# IMPORTANT CLOUD RUN RULES:
#   - The app MUST listen on 0.0.0.0 (not 127.0.0.1)
#   - The app MUST use the PORT environment variable (Cloud Run sets it)
#   - Both of these are handled in main.py already
# ─────────────────────────────────────────────────────────────────────────────

# ── Base image ────────────────────────────────────────────────────────────────
# python:3.11-slim is a small, official Python image.
# "slim" means it has only the essentials — no unnecessary OS packages.
# This keeps the Docker image small (faster to deploy, cheaper to store).
FROM python:3.11-slim

# ── Set working directory ─────────────────────────────────────────────────────
# All subsequent commands run inside /app inside the container.
# This is just a convention — you can name it anything.
WORKDIR /app

# ── Install system dependencies ───────────────────────────────────────────────
# Some Python packages need system-level libraries to compile.
# We install them here before installing Python packages.
# --no-install-recommends keeps the image lean.
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    curl \
    --no-install-recommends \
    && rm -rf /var/lib/apt/lists/*
#   ↑ Clean up the apt cache after installing — keeps image size down

# ── Install Python dependencies ───────────────────────────────────────────────
# WHY COPY requirements.txt FIRST (before copying the rest of the code)?
# Docker caches each step. If only your code changed (not requirements.txt),
# Docker will reuse the cached pip install layer instead of reinstalling
# everything. This makes rebuilds MUCH faster.

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
#   --no-cache-dir → don't cache downloaded packages (keeps image smaller)

# ── Copy application code ─────────────────────────────────────────────────────
# Copy everything into the container's /app directory.
# Files listed in .dockerignore are excluded (like .env, .git, __pycache__).
COPY . .

# ── Create output directories ─────────────────────────────────────────────────
# The file_saver agent writes to reports/ and the image agent to images/.
# We create these inside the container so the agents don't fail.
# NOTE: On Cloud Run, these are ephemeral (reset on each container restart).
# For persistent file storage, you'd use Google Cloud Storage instead.
RUN mkdir -p reports images

# ── Health check ──────────────────────────────────────────────────────────────
# Docker/Cloud Run uses this to verify the container started successfully.
# It pings /health every 30s. If it fails 3 times, the container is restarted.
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:${PORT:-8080}/health || exit 1

# ── Expose port ───────────────────────────────────────────────────────────────
# This is documentation only — it doesn't actually open a port.
# The real port is set by the PORT environment variable at runtime.
EXPOSE 8080

# ── Start command ─────────────────────────────────────────────────────────────
# This runs when the container starts.
#
# We use uvicorn directly (instead of "python main.py") because:
#   - It reads the PORT env var via the shell command below
#   - It's slightly more standard for production containers
#
# The shell form (CMD ["sh", "-c", "..."]) lets us use $PORT as a variable.
# Cloud Run sets PORT to 8080 by default.
CMD ["sh", "-c", "uvicorn main:app --host 0.0.0.0 --port ${PORT:-8080}"]
