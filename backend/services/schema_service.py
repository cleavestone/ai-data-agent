"""
services/schema_service.py

Fetches and caches the live database schema for the AI agent.
The agent calls get_schema() once per session so it knows what
tables, columns, and views are available before writing SQL.

Schema is cached in memory — it changes only when the database
schema changes (a deployment event), so re-reading it per request
would be wasteful.
"""

import logging
from db.connection import get_admin_pool

logger = logging.getLogger(__name__)

_schema_cache: str | None = None


async def get_schema_text() -> str:
    """
    Return the full database schema as a human-readable string.
    Fetches from the database on first call, then returns cached value.
    """
    global _schema_cache
    if _schema_cache:
        return _schema_cache

    _schema_cache = await _fetch_schema()
    logger.info("Schema fetched and cached")
    return _schema_cache


def invalidate_schema_cache() -> None:
    """Force a re-fetch on the next call. Call after schema migrations."""
    global _schema_cache
    _schema_cache = None
    logger.info("Schema cache invalidated")


async def _fetch_schema() -> str:
    """Query the database and build a schema description string."""
    parts: list[str] = []

    async with get_admin_pool() as pool:
        # ── Tables ────────────────────────────────────────────────
        columns = await pool.fetch("""
            SELECT
                c.table_name,
                c.column_name,
                c.data_type,
                c.is_nullable,
                c.column_default,
                pgd.description AS column_comment
            FROM information_schema.columns c
            JOIN information_schema.tables t
                ON t.table_name = c.table_name
                AND t.table_schema = c.table_schema
            LEFT JOIN pg_catalog.pg_statio_all_tables st
                ON st.relname = c.table_name
            LEFT JOIN pg_catalog.pg_description pgd
                ON pgd.objoid = st.relid
                AND pgd.objsubid = c.ordinal_position
            WHERE c.table_schema = 'public'
                AND t.table_type = 'BASE TABLE'
            ORDER BY c.table_name, c.ordinal_position
        """)

        tables: dict[str, list[str]] = {}
        for row in columns:
            tbl = row["table_name"]
            nullable = "" if row["is_nullable"] == "YES" else " NOT NULL"
            comment = f"  -- {row['column_comment']}" if row["column_comment"] else ""
            tables.setdefault(tbl, []).append(
                f"    {row['column_name']} {row['data_type'].upper()}{nullable}{comment}"
            )

        parts.append("=== TABLES ===")
        for tbl_name, col_lines in tables.items():
            parts.append(f"\n{tbl_name} (")
            parts.extend(col_lines)
            parts.append(")")

        # ── Views ─────────────────────────────────────────────────
        views = await pool.fetch("""
            SELECT
                t.table_name,
                obj_description(c.oid) AS view_comment
            FROM information_schema.tables t
            LEFT JOIN pg_catalog.pg_class c ON c.relname = t.table_name
            WHERE t.table_schema = 'public'
                AND t.table_type = 'VIEW'
            ORDER BY t.table_name
        """)

        if views:
            parts.append("\n\n=== VIEWS (use these for common queries) ===")
            for view in views:
                comment = f" — {view['view_comment']}" if view["view_comment"] else ""
                parts.append(f"  {view['table_name']}{comment}")

        # ── Enums / constraints (key ones) ────────────────────────
        parts.append("""

=== KEY CONSTRAINTS ===
customers.tier       : 'bronze' | 'silver' | 'gold' | 'platinum'
orders.status        : 'pending' | 'confirmed' | 'processing' | 'shipped' | 'delivered' | 'cancelled' | 'refunded'
All timestamps       : TIMESTAMPTZ stored in UTC
All prices/amounts   : NUMERIC (USD)
""")

    return "\n".join(parts)
