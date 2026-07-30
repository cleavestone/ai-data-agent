"""
services/chat_service.py

Orchestrates the complete flow for a single chat turn:

1. Check Redis cache — return immediately if hit
2. Call the AI agent
3. Format the response (decide visualisation type)
4. Cache the result
5. Return FormattedResponse to the API layer

This is the only service the API layer calls directly.
It coordinates cache_service, the agent, and formatter_service
so the API route stays thin.
"""

import logging
import time

from agents.sql_agent import ask, AgentResponse
from services.cache_service import get_cached, set_cached
from services.formatter_service import format_response, FormattedResponse
from core.tracing import trace

logger = logging.getLogger(__name__)


async def handle_question(question: str) -> FormattedResponse:
    """
    Handle a single user question end to end.

    Args:
        question: Natural language question from the user

    Returns:
        FormattedResponse — always returns, never raises
    """
    start_time = time.monotonic()

    with trace(
        "handle_question",
        run_type="chain",
        inputs={"question": question},
    ) as run:
        # ── Step 1: Check cache ───────────────────────────────
        cached_data = await get_cached(question)

        if cached_data:
            logger.info(f"Returning cached response for: {question[:50]}...")
            result = FormattedResponse(
                answer=cached_data["answer"],
                visualisation=cached_data["visualisation"],
                columns=cached_data["columns"],
                rows=cached_data["rows"],
                row_count=cached_data["row_count"],
                sql_executed=cached_data.get("sql_executed", ""),
                cached=True,
                execution_time_ms=0.0,
            )
            run.end(outputs={"cached": True, "answer": result.answer[:200]})
            return result

        # ── Step 2: Call the agent ────────────────────────────
        logger.info(f"Cache miss — calling agent for: {question[:50]}...")
        agent_response: AgentResponse = await ask(question)

        execution_time_ms = (time.monotonic() - start_time) * 1000

        # ── Step 3: Handle agent failure ──────────────────────
        if not agent_response.success:
            result = FormattedResponse(
                answer=agent_response.answer,
                visualisation="text_only",
                columns=[],
                rows=[],
                row_count=0,
                sql_executed=agent_response.sql_executed,
                cached=False,
                execution_time_ms=execution_time_ms,
            )
            run.end(
                outputs={
                    "cached": False,
                    "success": False,
                    "error": agent_response.error,
                }
            )
            return result

        # ── Step 4: Format the response ───────────────────────
        formatted = format_response(
            answer=agent_response.answer,
            columns=agent_response.columns,
            rows=agent_response.rows,
            row_count=agent_response.row_count,
            sql_executed=agent_response.sql_executed,
            cached=False,
            execution_time_ms=execution_time_ms,
        )

        # ── Step 5: Cache the result ──────────────────────────
        if agent_response.success and agent_response.row_count > 0:
            await set_cached(
                question,
                {
                    "answer": formatted.answer,
                    "visualisation": formatted.visualisation,
                    "columns": formatted.columns,
                    "rows": formatted.rows,
                    "row_count": formatted.row_count,
                    "sql_executed": formatted.sql_executed,
                },
            )

        run.end(
            outputs={
                "cached": False,
                "success": True,
                "visualisation": formatted.visualisation,
                "execution_time_ms": execution_time_ms,
                "row_count": formatted.row_count,
            }
        )

    return formatted
