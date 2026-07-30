"""
agents/sql_agent.py

The main AI agent. Receives a natural language question,
orchestrates tool calls to get schema and run SQL,
then returns a structured response.

Flow:
1. Receive user question
2. Send to OpenAI with tools available (get_schema, run_sql)
3. OpenAI calls get_schema → we return schema
4. OpenAI calls run_sql → we validate + execute → return data
5. OpenAI formats final answer
6. We return structured AgentResponse

This is an agentic loop — we keep processing tool calls
until the AI returns a final text response.
"""

import json
import logging
from dataclasses import dataclass, field
from typing import Any

from agents.base_agent import get_client, get_model, get_max_tokens
from agents.tools import get_schema, run_sql
from core.tracing import trace

logger = logging.getLogger(__name__)

# Register all available tools
TOOLS = [
    get_schema.TOOL_DEFINITION,
    run_sql.TOOL_DEFINITION,
]

# Map tool names to their execute functions
TOOL_EXECUTORS = {
    "get_schema": get_schema.execute,
    "run_sql": run_sql.execute,
}

# ─────────────────────────────────────────────────────────────
# System prompt — this is how we teach the AI to behave
# ─────────────────────────────────────────────────────────────
SYSTEM_PROMPT = """You are an expert data analyst AI assistant with access to a business database.

Your job is to help users answer questions about their business data by:
1. Understanding their natural language question
2. Calling get_schema to understand the available tables and columns
3. Writing precise SQL to answer the question
4. Calling run_sql to execute the query
5. Interpreting the results and presenting them clearly

DATABASE CONTEXT:
- The database contains: customers, products, orders, order_items, categories
- There are pre-built views for common queries:
  * v_order_details      — orders with customer and product details
  * v_monthly_revenue    — revenue, cost, profit by month
  * v_product_performance — sales and profit per product
  * v_customer_summary   — customer profiles with lifetime value
- All timestamps are in UTC (TIMESTAMPTZ)
- Prices are in USD (NUMERIC)
- Customer tiers: bronze, silver, gold, platinum

SQL RULES:
- Only write SELECT statements — never INSERT, UPDATE, DELETE, DROP
- Prefer views over raw table joins when they cover the question
- Always use meaningful column aliases for calculated fields
- Round decimal numbers to 2 places for display
- For date ranges, use: WHERE ordered_at >= NOW() - INTERVAL '30 days'
- Limit results to what is useful — don't return thousands of rows

RESPONSE FORMAT:
- Be concise and direct
- Present numbers with context (e.g. "$12,450 in revenue")
- When data has multiple rows, describe patterns and highlights
- If a question is ambiguous, make a reasonable assumption and state it
- Never expose raw SQL to the user in your response
- Never mention internal tool names or database implementation details
"""


@dataclass
class AgentResponse:
    """
    Structured response from the agent.
    Contains both the AI's text answer and the raw query result
    so the frontend can render tables and charts.
    """

    success: bool
    answer: str  # AI-generated text response
    columns: list[str] = field(default_factory=list)
    rows: list[dict] = field(default_factory=list)
    row_count: int = 0
    sql_executed: str = ""  # for debugging/logging
    error: str | None = None


async def ask(question: str) -> AgentResponse:
    """
    Process a natural language question through the full agent loop.

    Args:
        question: Natural language question from the user

    Returns:
        AgentResponse with text answer + raw data
    """
    logger.info(f"Agent received question: {question}")

    client = get_client()
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": question},
    ]

    sql_executed = ""
    query_columns: list[str] = []
    query_rows: list[dict] = []
    row_count = 0
    result: AgentResponse | None = None

    # ─────────────────────────────────────────────────────────
    # Agentic loop
    # We keep iterating until the AI returns a final
    # text response with no more tool calls
    # Max iterations prevents infinite loops
    # ─────────────────────────────────────────────────────────
    max_iterations = 6
    iteration = 0

    with trace(
        "sql_agent",
        run_type="chain",
        inputs={"question": question},
    ) as run:
        while iteration < max_iterations:
            iteration += 1
            logger.info(f"Agent loop iteration {iteration}")

            # Call OpenAI
            response = await client.chat.completions.create(
                model=get_model(),
                max_tokens=get_max_tokens(),
                messages=messages,
                tools=TOOLS,
                tool_choice="auto",  # AI decides when to use tools
            )

            message = response.choices[0].message

            # Add AI response to message history
            messages.append(message)

            # ── No tool calls — AI is done ────────────────────
            if not message.tool_calls:
                logger.info(f"Agent completed in {iteration} iterations")
                result = AgentResponse(
                    success=True,
                    answer=message.content or "I could not generate a response.",
                    columns=query_columns,
                    rows=query_rows,
                    row_count=row_count,
                    sql_executed=sql_executed,
                )
                break

            # ── Process each tool call ────────────────────────
            for tool_call in message.tool_calls:
                tool_name = tool_call.function.name
                tool_args = json.loads(tool_call.function.arguments)

                logger.info(f"Tool call: {tool_name}({tool_args})")

                # Execute the tool
                executor = TOOL_EXECUTORS.get(tool_name)
                if not executor:
                    tool_result = json.dumps({"error": f"Unknown tool: {tool_name}"})
                else:
                    tool_result = await executor(**tool_args)

                # Capture SQL and results for the AgentResponse
                if tool_name == "run_sql":
                    sql_executed = tool_args.get("sql", "")
                    try:
                        result_data = json.loads(tool_result)
                        if result_data.get("success"):
                            query_columns = result_data.get("columns", [])
                            query_rows = result_data.get("rows", [])
                            row_count = result_data.get("row_count", 0)
                    except json.JSONDecodeError:
                        pass

                # Add tool result to message history
                messages.append(
                    {
                        "role": "tool",
                        "tool_call_id": tool_call.id,
                        "content": tool_result,
                    }
                )

        # ── Handle max iterations ────────────────────────────
        if result is None:
            logger.error(f"Agent hit max iterations ({max_iterations})")
            result = AgentResponse(
                success=False,
                answer="I was unable to complete the analysis. Please try rephrasing your question.",
                error="max_iterations_exceeded",
            )

        # Attach metadata to the LangSmith trace
        run.end(
            outputs={
                "answer": result.answer,
                "success": result.success,
                "sql_executed": result.sql_executed,
                "row_count": result.row_count,
            }
        )
        run.add_metadata(
            {
                "iterations": iteration,
                "model": get_model(),
            }
        )
        if result.sql_executed:
            run.add_metadata({"sql": result.sql_executed[:800]})

    return result
