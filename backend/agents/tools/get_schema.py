"""
agents/tools/get_schema.py

OpenAI tool that returns the database schema to the AI agent.
The AI calls this first so it knows what tables and columns exist
before writing any SQL.
"""

import json
import logging

from services.schema_service import get_schema_text

logger = logging.getLogger(__name__)

TOOL_DEFINITION = {
    "type": "function",
    "function": {
        "name": "get_schema",
        "description": (
            "Get the database schema: tables, columns, data types, and available views. "
            "Always call this before writing SQL so you know what data is available."
        ),
        "parameters": {
            "type": "object",
            "properties": {},
            "required": [],
        },
    },
}


async def execute() -> str:
    """Return the full database schema as a JSON string."""
    try:
        schema = await get_schema_text()
        return json.dumps({"schema": schema})
    except Exception as e:
        logger.error(f"get_schema tool failed: {e}")
        return json.dumps({"error": str(e)})
