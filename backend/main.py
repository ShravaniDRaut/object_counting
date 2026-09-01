"""
Main FastAPI Application Entrypoint.
Initializes the application, mounts routes, static files, and database.
"""
from contextlib import asynccontextmanager
from pathlib import Path
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from backend.config import settings
from backend.database.connection import init_db
from backend.api import video_router, stream_router, analytics_router, reports_router
from backend.utils.sample_generator import generate_sample_traffic_video
from backend.logger import logger

# Frontend paths
FRONTEND_DIR = Path(__file__).resolve().parent.parent / "frontend"
STATIC_DIR = FRONTEND_DIR / "static"
TEMPLATES_DIR = FRONTEND_DIR / "templates"


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application startup and shutdown hooks."""
    logger.info("Initializing database...")
    init_db()

    # Pre-generate sample test video if not already present
    sample_file = settings.SAMPLE_DIR / "sample_traffic.mp4"
    if not sample_file.exists():
        logger.info("Generating initial sample traffic video for testing...")
        try:
            generate_sample_traffic_video(sample_file)
        except Exception as e:
            logger.warning(f"Could not pre-generate sample video: {e}")

    logger.info(f"{settings.APP_NAME} started successfully!")
    yield
    logger.info("Shutting down application...")


app = FastAPI(
    title=settings.APP_NAME,
    description="Real-Time AI Object Detection, Tracking & Line-Crossing Counting System using YOLOv8 & ByteTrack.",
    version=settings.APP_VERSION,
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS middleware for open development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API Routers
app.include_router(video_router)
app.include_router(stream_router)
app.include_router(analytics_router)
app.include_router(reports_router)

# Mount Static Files & Templates
STATIC_DIR.mkdir(parents=True, exist_ok=True)
TEMPLATES_DIR.mkdir(parents=True, exist_ok=True)
app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")

@app.get("/", response_class=HTMLResponse)
async def serve_index():
    """Serve modern single-page dashboard."""
    index_file = TEMPLATES_DIR / "index.html"
    return HTMLResponse(content=index_file.read_text(encoding="utf-8"))


@app.get("/api/health")
def health_check():
    """Health check status endpoint."""
    return {
        "status": "healthy",
        "app": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "model": settings.MODEL_PATH
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.main:app", host=settings.HOST, port=settings.PORT, reload=settings.DEBUG)
