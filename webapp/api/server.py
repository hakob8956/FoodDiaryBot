"""FastAPI server for the Mini App."""
import logging
from pathlib import Path
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from config import settings
from database.migrations import run_migrations

from .routes import calendar, charts, summary, auth, dashboard, profile

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan handler."""
    # Startup
    await run_migrations()
    logger.info("Mini App API started")
    yield
    # Shutdown
    logger.info("Mini App API shutting down")


app = FastAPI(
    title="FoodGPT Mini App API",
    description="API for the FoodGPT Telegram Mini App",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS middleware for Telegram Mini App
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Telegram Mini Apps need this
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth.router, prefix="/api", tags=["auth"])
app.include_router(dashboard.router, prefix="/api", tags=["dashboard"])
app.include_router(profile.router, prefix="/api", tags=["profile"])
app.include_router(calendar.router, prefix="/api", tags=["calendar"])
app.include_router(charts.router, prefix="/api", tags=["charts"])
app.include_router(summary.router, prefix="/api", tags=["summary"])


@app.get("/api/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "ok", "service": "foodgpt-miniapp"}


# Serve static files for frontend (production)
frontend_dist = Path(__file__).parent.parent / "frontend" / "dist"
if frontend_dist.exists():
    app.mount("/", StaticFiles(directory=str(frontend_dist), html=True), name="frontend")
