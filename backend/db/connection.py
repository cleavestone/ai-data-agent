"""
db/connection.py

Manages two async connection pools:
- admin_pool    → full access, used for internal operations only
- readonly_pool → SELECT only, used by the AI agent for all queries

Why two pools?
The AI agent connects exclusively through readonly_pool. Even if
the AI generates DROP TABLE or DELETE, the database rejects it
at the permission level — not just at the application level.

Usage:
    from db.connection import get_readonly_pool, get_admin_pool

    async with get_readonly_pool() as pool:
        rows = await pool.fetch("SELECT * FROM customers LIMIT 10")
"""

import asyncpg
import logging
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from core.config import settings

logger = logging.getLogger(__name__)

# ─────────────────────────────────────────────────────────────
# Module-level pool instances
# Created once at app startup, reused across all requests
# ─────────────────────────────────────────────────────────────
_admin_pool: asyncpg.Pool | None = None
_readonly_pool: asyncpg.Pool | None = None


async def create_pools() -> None:
    """
    Create both connection pools.
    Called once at application startup in main.py.
    """
    global _admin_pool, _readonly_pool

    logger.info("Creating database connection pools...")

    # Strip +asyncpg from URL — asyncpg uses postgresql:// directly
    admin_url = settings.postgres_url.replace("postgresql+asyncpg://", "postgresql://")
    readonly_url = settings.postgres_readonly_url.replace("postgresql+asyncpg://", "postgresql://")

    _admin_pool = await asyncpg.create_pool(
        dsn=admin_url,
        min_size=2,         # keep 2 connections alive always
        max_size=10,        # max 10 concurrent connections
        command_timeout=30, # query timeout in seconds
    )

    _readonly_pool = await asyncpg.create_pool(
        dsn=readonly_url,
        min_size=2,
        max_size=20,        # more connections for readonly — AI queries come here
        command_timeout=30,
    )

    logger.info("✓ Database pools created (admin: 2-10, readonly: 2-20)")


async def close_pools() -> None:
    """
    Close both pools gracefully.
    Called at application shutdown in main.py.
    """
    global _admin_pool, _readonly_pool

    if _admin_pool:
        await _admin_pool.close()
        logger.info("Admin pool closed")

    if _readonly_pool:
        await _readonly_pool.close()
        logger.info("Readonly pool closed")


@asynccontextmanager
async def get_readonly_pool() -> AsyncGenerator[asyncpg.Pool, None]:
    """
    Context manager that yields the readonly pool.
    Use this for all AI agent queries.

    Example:
        async with get_readonly_pool() as pool:
            rows = await pool.fetch("SELECT * FROM products")
    """
    if _readonly_pool is None:
        raise RuntimeError("Readonly pool not initialised. Call create_pools() first.")
    yield _readonly_pool


@asynccontextmanager
async def get_admin_pool() -> AsyncGenerator[asyncpg.Pool, None]:
    """
    Context manager that yields the admin pool.
    Use only for internal operations — never for AI queries.

    Example:
        async with get_admin_pool() as pool:
            await pool.execute("REFRESH MATERIALIZED VIEW v_monthly_revenue")
    """
    if _admin_pool is None:
        raise RuntimeError("Admin pool not initialised. Call create_pools() first.")
    yield _admin_pool


async def health_check() -> dict:
    """
    Check both pools are alive.
    Called by the /health endpoint.
    """
    results = {"admin": False, "readonly": False}

    try:
        async with get_admin_pool() as pool:
            await pool.fetchval("SELECT 1")
            results["admin"] = True
    except Exception as e:
        logger.error(f"Admin pool health check failed: {e}")

    try:
        async with get_readonly_pool() as pool:
            await pool.fetchval("SELECT 1")
            results["readonly"] = True
    except Exception as e:
        logger.error(f"Readonly pool health check failed: {e}")

    return results