"""FastAPI API routers package."""
from .routes_video import router as video_router
from .routes_stream import router as stream_router
from .routes_analytics import router as analytics_router
from .routes_reports import router as reports_router

__all__ = ["video_router", "stream_router", "analytics_router", "reports_router"]
