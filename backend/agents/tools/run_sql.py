"""
agents/tools/run_sql.py

OpenAI tool that executes AI-generated SQL against the database.
All SQL passes through the validator before execution, so only
safe SELECT queries reach the database.
"""

import json
import logging

from db.query_runner import run_query
from core.tracing import traceable

logger = logging.getLogger(__name__)

TOOL_DEFINITION = {
    "type": "function",
    "function": {
        "name": "run_sql",
        "description": (
            "Execute a SQL SELECT query against the database and return the results. "
            "Only SELECT statements are allowed — no data modification."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "sql": {
                    "type": "string",
                    "description": "A valid SQL SELECT statement to execute.",
                }
            },
            "required": ["sql"],
        },
    },
}


async def execute(sql: str) -> str:
    """Validate and run a SQL query, returning results as a JSON string."""
    logger.info(f"run_sql tool called with: {sql[:100]}...")
    result = await run_query(sql)

    if not result.success:
        return json.dumps(
            {
                "success": False,
                "error": result.error,
            }
        )

    return json.dumps(
        {
            "success": True,
            "columns": result.columns,
            "rows": result.rows,
            "row_count": result.row_count,
            "execution_time_ms": round(result.execution_time_ms, 1),
        }
    )
