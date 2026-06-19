"""
main.py

FastAPI application entry point.
Handles:
- App creation and configuration
- Startup and shutdown lifecycle (DB pools, Redis)
- CORS (so the React frontend can call the API)
- Mounting all routes

Run with:
    uv run uvicorn main:app --reload --port 8000
"""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from core.config import settings
from api.v1.router import router as v1_router
from db.connection import create_pools, close_pools
from services.cache_service import close_redis

# ─────────────────────────────────────────────────────────────
# Logging — structured, consistent across the app
# ─────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.DEBUG if settings.is_development else logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
)
logger = logging.getLogger(__name__)


# ─────────────────────────────────────────────────────────────
# Lifespan — startup and shutdown logic
# This is the modern FastAPI pattern (replaces @app.on_event)
# ─────────────────────────────────────────────────────────────
@asynccontextmanager
async def lifespan(app: FastAPI):
    # ── Startup ───────────────────────────────────────────────
    logger.info(f"Starting {settings.app_name} v{settings.app_version}")
    logger.info(f"Environment: {settings.app_env}")

    # Create DB connection pools — must happen before any request
    await create_pools()
    logger.info("✓ Database pools ready")

    yield  # app runs here

    # ── Shutdown ──────────────────────────────────────────────
    logger.info("Shutting down...")
    await close_pools()
    await close_redis()
    logger.info("✓ Connections closed cleanly")


# ─────────────────────────────────────────────────────────────
# App creation
# ─────────────────────────────────────────────────────────────
app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="AI-powered natural language data agent",
    lifespan=lifespan,
    # Hide docs in production
    docs_url="/docs" if settings.is_development else None,
    redoc_url="/redoc" if settings.is_development else None,
)


# ─────────────────────────────────────────────────────────────
# CORS — allows the React frontend to call this API
# In production, replace "*" with your actual frontend domain
# ─────────────────────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ─────────────────────────────────────────────────────────────
# Routes
# ─────────────────────────────────────────────────────────────
app.include_router(v1_router)


# ─────────────────────────────────────────────────────────────
# Root
# ─────────────────────────────────────────────────────────────
@app.get("/")
async def root():
    return {
        "name": settings.app_name,
        "version": settings.app_version,
        "environment": settings.app_env,
        "docs": "/docs" if settings.is_development else "disabled in production",
    }