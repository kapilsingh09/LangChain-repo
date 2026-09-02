from fastapi import APIRouter
from app.config import settings
from app.schemas.reports import HealthResponse

router = APIRouter(tags=["General"])


@router.get("/")
async def root():
    return {
        "message": "Welcome to Deep Multi-Agent Research API",
        "version": settings.VERSION,
        "docs_url": "/docs",
        "health_url": "/health",
        "endpoints": {
            "research_sync": "POST /api/research",
            "research_stream": "POST /api/research/stream",
            "list_reports": "GET /api/reports",
            "get_report": "GET /api/reports/{filename}",
            "static_images": "/images/{filename}",
            "static_reports": "/reports/{filename}"
        }
    }


@router.get("/health", response_model=HealthResponse)
async def health_check():
    services = {
        "google_api_key_configured": bool(settings.GOOGLE_API_KEY),
        "google_api_key_secondary_configured": bool(settings.GOOGLE_API_KEY2),
        "groq_api_key_configured": bool(settings.GROQ_API_KEY),
        "tavily_api_key_configured": bool(settings.TAVILY_API_KEY),
        "huggingface_token_configured": bool(settings.HF_TOKEN),
    }
    all_critical_present = bool(settings.GOOGLE_API_KEY and settings.GROQ_API_KEY)
    return HealthResponse(
        status="healthy" if all_critical_present else "degraded",
        services=services,
        version=settings.VERSION
    )
