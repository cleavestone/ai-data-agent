"""
services/cache_service.py

Handles all Redis caching for query results.

Why cache AI query results?
- An AI + DB round trip costs time (2-5 seconds) and money (OpenAI tokens)
- Many users ask the same or similar questions
- "What was last month's revenue?" asked 100 times should hit the DB once

Cache strategy:
- Key: SHA256 hash of the normalised question
- Value: full AgentResponse serialised as JSON
- TTL: configurable (default 1 hour)

We normalise the question before hashing so that:
"show me revenue last month" and "Show me revenue last month"
and "show me revenue last month " all hit the same cache entry.
"""

import json
import hashlib
import logging
from typing import Any

import redis.asyncio as aioredis

from core.config import settings

logger = logging.getLogger(__name__)

# ─────────────────────────────────────────────────────────────
# Single shared Redis client
# ─────────────────────────────────────────────────────────────
_redis_client: aioredis.Redis | None = None


async def get_redis() -> aioredis.Redis:
    """Return shared Redis client, creating it if needed."""
    global _redis_client

    if _redis_client is None:
        _redis_client = aioredis.from_url(
            settings.redis_url,
            encoding="utf-8",
            decode_responses=True,
        )
        logger.info("Redis client created")

    return _redis_client


async def close_redis() -> None:
    """Close Redis connection — called at app shutdown."""
    global _redis_client
    if _redis_client:
        await _redis_client.aclose()
        logger.info("Redis connection closed")


def _make_cache_key(question: str) -> str:
    """
    Generate a deterministic cache key from a question.
    Normalises the question first so minor variations hit the same key.
    """
    # Normalise — lowercase, strip whitespace, collapse multiple spaces
    normalised = " ".join(question.lower().strip().split())

    # Hash it — keys should be short and safe for Redis
    hash_value = hashlib.sha256(normalised.encode()).hexdigest()[:16]

    return f"agent:query:{hash_value}"


async def get_cached(question: str) -> dict | None:
    """
    Look up a cached response for this question.

    Returns:
        The cached response dict if found, None if cache miss
    """
    try:
        redis = await get_redis()
        key = _make_cache_key(question)
        cached = await redis.get(key)

        if cached:
            logger.info(f"Cache HIT for key: {key}")
            return json.loads(cached)

        logger.info(f"Cache MISS for key: {key}")
        return None

    except Exception as e:
        # Cache failures should never break the app
        # Log and continue — the request will just hit the AI
        logger.warning(f"Cache get failed (non-fatal): {e}")
        return None


async def set_cached(question: str, response: dict, ttl: int | None = None) -> None:
    """
    Cache a response for this question.

    Args:
        question: The original question (will be normalised)
        response: The response dict to cache
        ttl:      Time to live in seconds (defaults to config value)
    """
    try:
        redis = await get_redis()
        key = _make_cache_key(question)
        ttl = ttl or settings.redis_cache_ttl

        await redis.setex(
            name=key,
            time=ttl,
            value=json.dumps(response),
        )
        logger.info(f"Cached response for key: {key} (TTL: {ttl}s)")

    except Exception as e:
        logger.warning(f"Cache set failed (non-fatal): {e}")


async def invalidate(question: str) -> None:
    """Delete a specific cached response."""
    try:
        redis = await get_redis()
        key = _make_cache_key(question)
        await redis.delete(key)
        logger.info(f"Cache invalidated for key: {key}")
    except Exception as e:
        logger.warning(f"Cache invalidate failed (non-fatal): {e}")


async def flush_all_queries() -> int:
    """
    Delete all cached query responses.
    Useful when underlying data changes significantly.

    Returns:
        Number of keys deleted
    """
    try:
        redis = await get_redis()
        keys = await redis.keys("agent:query:*")
        if keys:
            deleted = await redis.delete(*keys)
            logger.info(f"Flushed {deleted} cached queries")
            return deleted
        return 0
    except Exception as e:
        logger.warning(f"Cache flush failed: {e}")
        return 0


async def health_check() -> bool:
    """Check Redis is reachable."""
    try:
        redis = await get_redis()
        await redis.ping()
        return True
    except Exception:
        return False