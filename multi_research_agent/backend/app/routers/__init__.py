from app.routers.general import router as general_router
from app.routers.research import router as research_router
from app.routers.reports import router as reports_router

__all__ = [
    "general_router",
    "research_router",
    "reports_router"
]
