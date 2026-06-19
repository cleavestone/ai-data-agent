"""
api/v1/health.py

Health check endpoint.
Used by Docker, load balancers, and monitoring tools
to know if the application is ready to serve traffic.

GET /api/v1/health
"""

from fastapi import APIRouter
from models.chat import HealthResponse
from db.connection import health_check as db_health_check
from services.cache_service import health_check as redis_health_check
from core.config import settings

router = APIRouter()


@router.get("/health", response_model=HealthResponse)
async def health():
    """
    Check all infrastructure dependencies are reachable.
    Returns 200 even when degraded so load balancers
    keep routing traffic — the status field tells the full story.
    """
    db_status = await db_health_check()
    redis_ok = await redis_health_check()

    postgres_admin    = db_status.get("admin", False)
    postgres_readonly = db_status.get("readonly", False)

    # Determine overall status
    if postgres_admin and postgres_readonly and redis_ok:
        status = "healthy"
    elif postgres_admin or postgres_readonly:
        status = "degraded"
    else:
        status = "unhealthy"

    return HealthResponse(
        status=status,
        postgres_admin=postgres_admin,
        postgres_readonly=postgres_readonly,
        redis=redis_ok,
        version=settings.app_version,
    )