from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.config import settings
from app.routers import general_router, research_router, reports_router

app = FastAPI(
    title=settings.PROJECT_NAME,
    description="""
A clean, modular, production-ready FastAPI backend for the LangGraph Multi-Agent Research System.

### Capabilities:
- **Planning & Decomposition**: Automatically segments queries into targeted parallel research missions.
- **Deep Web Intelligence**: Parallel researcher agents query Tavily for empirical data & benchmarks.
- **Evidence Collector & QA Critic**: Synthesizes and scores evidence rigor before writing.
- **Authoritative Technical Synthesis**: Writes 1000–1500 word Markdown reports with Groq LLMs.
- **Autonomous Diagram Generation**: Designs and renders technical architecture diagrams via HuggingFace.
- **Live Server-Sent Events (SSE)**: Real-time event streaming for interactive frontends.
    """,
    version=settings.VERSION
)

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount Static Storage Directories
app.mount("/images", StaticFiles(directory=str(settings.IMAGES_DIR)), name="images")
app.mount("/reports", StaticFiles(directory=str(settings.REPORTS_DIR)), name="reports")

# Register Routers
app.include_router(general_router)
app.include_router(research_router)
app.include_router(reports_router)
