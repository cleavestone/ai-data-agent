"""
agents/tools/run_sql.py

Tool that the AI agent calls to execute a SQL query.
Every query goes through the validator before execution —
the AI cannot bypass this.
"""

import json
import logging
from db.query_runner import run_query

logger = logging.getLogger(__name__)

# ─────────────────────────────────────────────────────────────
# Tool definition
# ─────────────────────────────────────────────────────────────
TOOL_DEFINITION = {
    "type": "function",
    "function": {
        "name": "run_sql",
        "description": (
            "Execute a SQL SELECT query against the database. "
            "Only SELECT statements are allowed. "
            "Always call get_schema first to know what tables exist. "
            "Use the views (v_order_details, v_monthly_revenue, "
            "v_product_performance, v_customer_summary) when possible "
            "as they have pre-built joins."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "sql": {
                    "type": "string",
                    "description": (
                        "A valid PostgreSQL SELECT statement. "
                        "Do not include semicolons. "
                        "Do not use INSERT, UPDATE, DELETE, DROP or any "
                        "data modification statements."
                    ),
                }
            },
            "required": ["sql"],
        },
    },
}


async def execute(sql: str) -> str:
    """
    Validate and run a SQL query.
    Returns results as a JSON string so the AI can read them.
    """
    logger.info(f"AI requested SQL execution: {sql[:100]}...")

    result = await run_query(sql)

    if not result.success:
        # Return error as JSON — AI will read this and try again
        return json.dumps({
            "success": False,
            "error": result.error,
        })

    return json.dumps({
        "success": True,
        "columns": result.columns,
        "rows": result.rows,
        "row_count": result.row_count,
        "execution_time_ms": round(result.execution_time_ms, 1),
    })