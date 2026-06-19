"""
db/query_runner.py

Executes validated SQL against the readonly pool and returns
structured results the rest of the app can work with.

This is the only place in the entire application where SQL
is actually executed. All queries flow through here.

Usage:
    from db.query_runner import run_query

    result = await run_query("SELECT * FROM customers LIMIT 10")
    print(result.rows)
    print(result.columns)
    print(result.row_count)
"""

import time
import logging
from dataclasses import dataclass, field

import asyncpg

from db.connection import get_readonly_pool
from db.sql_validator import validate_sql, ValidationError, format_validation_error
from core.config import settings

logger = logging.getLogger(__name__)


@dataclass
class QueryResult:
    """
    Structured result from a database query.
    This is what flows up to the service layer and eventually
    to the AI agent for formatting.
    """
    success: bool
    columns: list[str] = field(default_factory=list)
    rows: list[dict] = field(default_factory=list)
    row_count: int = 0
    execution_time_ms: float = 0.0
    sql: str = ""                   # the actual SQL that ran (after validation)
    error: dict | None = None       # populated only on failure


async def run_query(raw_sql: str) -> QueryResult:
    """
    Validate and execute a SQL query against the readonly pool.

    Args:
        raw_sql: SQL string from the AI agent

    Returns:
        QueryResult — always returns, never raises
        Check result.success to know if it worked
    """
    start_time = time.monotonic()

    # ── Step 1: Validate ──────────────────────────────────────
    try:
        validated = validate_sql(raw_sql, max_rows=settings.max_rows_per_query)
    except ValidationError as e:
        logger.warning(f"SQL validation failed: {e}")
        return QueryResult(
            success=False,
            error=format_validation_error(e),
            sql=raw_sql,
        )

    # ── Step 2: Execute ───────────────────────────────────────
    try:
        async with get_readonly_pool() as pool:
            records = await pool.fetch(validated.sql)

        execution_time_ms = (time.monotonic() - start_time) * 1000

        # ── Step 3: Convert to plain dicts ────────────────────
        # asyncpg returns Record objects — convert to plain dicts
        # so the rest of the app does not depend on asyncpg types
        if records:
            columns = list(records[0].keys())
            rows = [dict(record) for record in records]
        else:
            columns = []
            rows = []

        # ── Step 4: Serialise non-JSON-safe types ─────────────
        rows = _serialise_rows(rows)

        logger.info(
            f"Query executed | rows={len(rows)} | "
            f"time={execution_time_ms:.1f}ms"
        )

        return QueryResult(
            success=True,
            columns=columns,
            rows=rows,
            row_count=len(rows),
            execution_time_ms=execution_time_ms,
            sql=validated.sql,
        )

    except asyncpg.PostgresError as e:
        execution_time_ms = (time.monotonic() - start_time) * 1000
        logger.error(f"Database error: {e}")
        return QueryResult(
            success=False,
            sql=validated.sql,
            execution_time_ms=execution_time_ms,
            error={
                "error": "database_error",
                "message": "The query could not be executed.",
                "detail": str(e),
            },
        )

    except Exception as e:
        execution_time_ms = (time.monotonic() - start_time) * 1000
        logger.error(f"Unexpected error running query: {e}")
        return QueryResult(
            success=False,
            sql=validated.sql,
            execution_time_ms=execution_time_ms,
            error={
                "error": "unexpected_error",
                "message": "An unexpected error occurred.",
            },
        )


def _serialise_rows(rows: list[dict]) -> list[dict]:
    """
    Convert non-JSON-serialisable types to Python primitives.
    asyncpg returns Decimal, datetime, UUID etc — these need
    converting before we can send them as JSON.
    """
    import uuid
    from datetime import datetime, date
    from decimal import Decimal

    serialised = []
    for row in rows:
        clean = {}
        for key, value in row.items():
            if isinstance(value, Decimal):
                clean[key] = float(value)
            elif isinstance(value, (datetime, date)):
                clean[key] = value.isoformat()
            elif isinstance(value, uuid.UUID):
                clean[key] = str(value)
            elif isinstance(value, memoryview):
                clean[key] = bytes(value).hex()
            else:
                clean[key] = value
        serialised.append(clean)

    return serialised