"""
agents/tools/get_schema.py

Tool that returns database schema information to the AI agent.
The AI calls this first to understand what tables and columns
exist before generating SQL.

Critical design decision:
We never give the AI raw data — only schema metadata.
This keeps prompts small, costs low, and avoids leaking
sensitive data into the AI context.
"""

import logging
from db.connection import get_readonly_pool

logger = logging.getLogger(__name__)

# ─────────────────────────────────────────────────────────────
# Tool definition — this is what we register with OpenAI
# so the model knows the tool exists and how to call it
# ─────────────────────────────────────────────────────────────
TOOL_DEFINITION = {
    "type": "function",
    "function": {
        "name": "get_schema",
        "description": (
            "Get the database schema — table names, column names, data types, "
            "and available views. Always call this first before writing any SQL "
            "so you know what tables and columns exist."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "table_name": {
                    "type": "string",
                    "description": (
                        "Optional. Get schema for a specific table or view only. "
                        "If omitted, returns schema for all tables and views."
                    ),
                }
            },
            "required": [],
        },
    },
}


async def execute(table_name: str | None = None) -> str:
    """
    Fetch schema metadata from the database and format it
    as a compact, readable string for the AI prompt.

    Returns something like:
        TABLE: customers
          id          | uuid    | PRIMARY KEY
          name        | varchar | NOT NULL
          email       | varchar | NOT NULL UNIQUE
          country     | varchar | NOT NULL
          tier        | varchar | bronze/silver/gold/platinum
          created_at  | timestamptz

        VIEW: v_order_details
          order_id    | uuid
          customer_name | varchar
          ...
    """
    async with get_readonly_pool() as pool:

        # ── Fetch tables ──────────────────────────────────────
        table_filter = "AND t.table_name = $1" if table_name else ""
        params = [table_name] if table_name else []

        tables = await pool.fetch(
            f"""
            SELECT
                t.table_name,
                t.table_type,
                c.column_name,
                c.data_type,
                c.is_nullable,
                c.column_default,
                col_description(
                    (quote_ident(t.table_schema) || '.' || quote_ident(t.table_name))::regclass::oid,
                    c.ordinal_position
                ) AS column_comment
            FROM information_schema.tables t
            JOIN information_schema.columns c
                ON c.table_name = t.table_name
                AND c.table_schema = t.table_schema
            WHERE t.table_schema = 'public'
            {table_filter}
            ORDER BY t.table_type DESC, t.table_name, c.ordinal_position
            """,
            *params,
        )

        # ── Fetch table comments ──────────────────────────────
        table_comments = await pool.fetch(
            """
            SELECT
                relname AS table_name,
                obj_description(oid, 'pg_class') AS comment
            FROM pg_class
            WHERE relnamespace = 'public'::regnamespace
            AND relkind IN ('r', 'v')
            """
        )
        comment_map = {r["table_name"]: r["comment"] for r in table_comments}

        # ── Format output ─────────────────────────────────────
        if not tables:
            return "No tables found."

        # Group columns by table
        schema_map: dict[str, dict] = {}
        for row in tables:
            tname = row["table_name"]
            if tname not in schema_map:
                schema_map[tname] = {
                    "type": "VIEW" if row["table_type"] == "VIEW" else "TABLE",
                    "comment": comment_map.get(tname, ""),
                    "columns": [],
                }
            schema_map[tname]["columns"].append(row)

        # Build readable string
        lines = []
        for tname, info in schema_map.items():
            lines.append(f"\n{info['type']}: {tname}")
            if info["comment"]:
                lines.append(f"  -- {info['comment']}")

            for col in info["columns"]:
                nullable = "" if col["is_nullable"] == "NO" else " nullable"
                comment = f"  -- {col['column_comment']}" if col["column_comment"] else ""
                lines.append(
                    f"  {col['column_name']:<25} {col['data_type']}{nullable}{comment}"
                )

        return "\n".join(lines)