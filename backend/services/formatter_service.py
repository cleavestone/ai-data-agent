"""
services/formatter_service.py

Decides how query results should be visualised.
The AI returns raw rows and columns — this service
determines whether the frontend should render:

  - A TABLE       → multiple rows, mixed column types
  - A BAR CHART   → categorical data (group by country, category etc)
  - A LINE CHART  → time series data (by month, by week etc)
  - A STAT CARD   → single number result
  - TEXT ONLY     → no structured data to display

This keeps visualisation logic out of the agent and out of the API.
The frontend receives a clear instruction: "render this as a bar_chart"
along with the data, and just executes it.
"""

import logging
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)


class VisualisationType(str, Enum):
    TABLE = "table"
    BAR_CHART = "bar_chart"
    LINE_CHART = "line_chart"
    STAT_CARD = "stat_card"
    TEXT_ONLY = "text_only"


# Column name patterns that suggest time series data
TIME_COLUMN_PATTERNS = [
    "month", "week", "day", "date", "year",
    "period", "time", "created_at", "ordered_at",
]

# Column name patterns that suggest categorical grouping
CATEGORY_COLUMN_PATTERNS = [
    "country", "city", "category", "tier", "status",
    "type", "region", "segment", "name", "product",
]

# Column name patterns that suggest numeric metrics
METRIC_COLUMN_PATTERNS = [
    "revenue", "profit", "total", "count", "amount",
    "sales", "orders", "margin", "value", "sum",
    "avg", "average", "units", "quantity",
]


@dataclass
class FormattedResponse:
    """
    The complete response sent to the frontend.
    Contains the AI answer, the data, and how to display it.
    """
    answer: str                         # AI natural language answer
    visualisation: VisualisationType    # how to render the data
    columns: list[str]                  # column names
    rows: list[dict]                    # the actual data rows
    row_count: int
    sql_executed: str                   # for debug panel
    cached: bool = False                # was this a cache hit?
    execution_time_ms: float = 0.0


def decide_visualisation(
    columns: list[str],
    rows: list[dict],
) -> VisualisationType:
    """
    Analyse the shape of the data and decide the best visualisation.

    Decision logic:
    1. No data → TEXT_ONLY
    2. Single value → STAT_CARD
    3. Has a time column + numeric column → LINE_CHART
    4. Has a category column + numeric column + few rows → BAR_CHART
    5. Everything else → TABLE
    """
    if not rows or not columns:
        return VisualisationType.TEXT_ONLY

    # ── Single value ─────────────────────────────────────────
    if len(rows) == 1 and len(columns) == 1:
        return VisualisationType.STAT_CARD

    columns_lower = [c.lower() for c in columns]

    # Check what kinds of columns we have
    has_time_column = any(
        any(pattern in col for pattern in TIME_COLUMN_PATTERNS)
        for col in columns_lower
    )
    has_category_column = any(
        any(pattern in col for pattern in CATEGORY_COLUMN_PATTERNS)
        for col in columns_lower
    )
    has_metric_column = any(
        any(pattern in col for pattern in METRIC_COLUMN_PATTERNS)
        for col in columns_lower
    )

    # Check if numeric values exist in the data
    has_numeric_values = any(
        isinstance(v, (int, float))
        for row in rows[:5]  # sample first 5 rows
        for v in row.values()
    )

    # ── Time series → line chart ──────────────────────────────
    if has_time_column and (has_metric_column or has_numeric_values):
        return VisualisationType.LINE_CHART

    # ── Categorical + metric + reasonable row count → bar chart
    if (
        has_category_column
        and (has_metric_column or has_numeric_values)
        and len(rows) <= 20      # bar charts get cluttered with too many bars
        and len(columns) <= 4    # too many columns → table is clearer
    ):
        return VisualisationType.BAR_CHART

    # ── Default → table ───────────────────────────────────────
    return VisualisationType.TABLE


def format_response(
    answer: str,
    columns: list[str],
    rows: list[dict],
    row_count: int,
    sql_executed: str,
    cached: bool = False,
    execution_time_ms: float = 0.0,
) -> FormattedResponse:
    """
    Build the complete formatted response for the API layer.
    """
    visualisation = decide_visualisation(columns, rows)

    logger.info(
        f"Response formatted | rows={row_count} | "
        f"visualisation={visualisation} | cached={cached}"
    )

    return FormattedResponse(
        answer=answer,
        visualisation=visualisation,
        columns=columns,
        rows=rows,
        row_count=row_count,
        sql_executed=sql_executed,
        cached=cached,
        execution_time_ms=execution_time_ms,
    )