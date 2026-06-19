"""
db/sql_validator.py

Validates AI-generated SQL before it is executed against the database.
This is a critical security layer — AI models can make mistakes or be
manipulated into generating harmful SQL.

Validation checks (in order):
1. Not empty
2. Is a SELECT statement only
3. No dangerous keywords
4. No multiple statements (SQL injection via semicolons)
5. No system table access
6. LIMIT clause enforced

Usage:
    from db.sql_validator import validate_sql, ValidationError

    try:
        clean_sql = validate_sql(raw_sql)
    except ValidationError as e:
        return {"error": str(e)}
"""

import re
import logging
from dataclasses import dataclass

logger = logging.getLogger(__name__)


class ValidationError(Exception):
    """Raised when SQL fails validation."""
    pass


# ─────────────────────────────────────────────────────────────
# Dangerous keywords that should never appear in AI queries
# ─────────────────────────────────────────────────────────────
FORBIDDEN_KEYWORDS = [
    # Data modification
    "INSERT", "UPDATE", "DELETE", "UPSERT", "MERGE",
    # Schema modification
    "DROP", "CREATE", "ALTER", "TRUNCATE", "RENAME",
    # Permissions
    "GRANT", "REVOKE",
    # Execution
    "EXECUTE", "EXEC",
    # Postgres-specific dangerous operations
    "COPY", "VACUUM", "REINDEX", "CLUSTER",
    # Comment patterns used in injection
    "--", "/*", "*/",
    # Stored procedures
    "CALL",
]

# System schemas the AI should never access
FORBIDDEN_SCHEMAS = [
    "pg_catalog",
    "information_schema",
    "pg_toast",
    "pg_temp",
]

# Maximum rows allowed — overridden by settings
DEFAULT_MAX_ROWS = 1000


@dataclass
class ValidatedSQL:
    """Result of successful SQL validation."""
    sql: str                    # the cleaned, validated SQL
    has_limit: bool             # whether the original had a LIMIT clause
    limit_value: int | None     # the LIMIT value if present


def validate_sql(raw_sql: str, max_rows: int = DEFAULT_MAX_ROWS) -> ValidatedSQL:
    """
    Validate and clean AI-generated SQL.

    Args:
        raw_sql:  The raw SQL string from the AI
        max_rows: Maximum rows to allow (injected if missing)

    Returns:
        ValidatedSQL with cleaned sql ready to execute

    Raises:
        ValidationError: If SQL fails any check
    """
    if not raw_sql or not raw_sql.strip():
        raise ValidationError("SQL query is empty.")

    # ── Clean up ──────────────────────────────────────────────
    # Remove markdown code fences the AI sometimes adds
    sql = raw_sql.strip()
    sql = re.sub(r"^```sql\s*", "", sql, flags=re.IGNORECASE)
    sql = re.sub(r"^```\s*", "", sql)
    sql = re.sub(r"\s*```$", "", sql)
    sql = sql.strip()

    # ── Check 1: Must not be empty after cleaning ─────────────
    if not sql:
        raise ValidationError("SQL query is empty after cleaning.")

    # ── Check 2: Must be a SELECT statement ───────────────────
    first_word = sql.split()[0].upper()
    if first_word not in ("SELECT", "WITH"):
        raise ValidationError(
            f"Only SELECT queries are allowed. Got: '{first_word}'. "
            "The AI agent cannot modify data."
        )

    # ── Check 3: No forbidden keywords ───────────────────────
    sql_upper = sql.upper()
    for keyword in FORBIDDEN_KEYWORDS:
        # Use word boundary to avoid false positives
        # e.g. "CREATED_AT" should not match "CREATE"
        pattern = rf"\b{re.escape(keyword)}\b"
        if re.search(pattern, sql_upper):
            raise ValidationError(
                f"Forbidden keyword detected: '{keyword}'. "
                "Query rejected for security reasons."
            )

    # ── Check 4: No multiple statements ──────────────────────
    # SQL injection often works by appending ; DROP TABLE ...
    # Strip semicolons at end (normal), but reject any in the middle
    sql_no_strings = re.sub(r"'[^']*'", "''", sql)  # blank out string literals
    semicolons = [i for i, c in enumerate(sql_no_strings) if c == ";"]

    if len(semicolons) > 1:
        raise ValidationError(
            "Multiple SQL statements detected. "
            "Only a single SELECT statement is allowed."
        )

    # Remove trailing semicolon — asyncpg handles this better without it
    sql = sql.rstrip(";").strip()

    # ── Check 5: No system schema access ─────────────────────
    for schema in FORBIDDEN_SCHEMAS:
        if schema.lower() in sql.lower():
            raise ValidationError(
                f"Access to system schema '{schema}' is not allowed."
            )

    # ── Check 6: Enforce LIMIT ────────────────────────────────
    limit_match = re.search(r"\bLIMIT\s+(\d+)", sql, re.IGNORECASE)
    has_limit = limit_match is not None
    limit_value = int(limit_match.group(1)) if limit_match else None

    if has_limit and limit_value and limit_value > max_rows:
        # Replace the limit with the max allowed
        sql = re.sub(
            r"\bLIMIT\s+\d+",
            f"LIMIT {max_rows}",
            sql,
            flags=re.IGNORECASE,
        )
        limit_value = max_rows
        logger.warning(f"LIMIT reduced to {max_rows} (requested {limit_value})")

    if not has_limit:
        # Inject a LIMIT to prevent runaway queries
        sql = f"{sql}\nLIMIT {max_rows}"
        limit_value = max_rows
        logger.info(f"LIMIT {max_rows} injected into query")

    logger.info(f"SQL validation passed | has_limit={has_limit} | limit={limit_value}")

    return ValidatedSQL(
        sql=sql,
        has_limit=has_limit,
        limit_value=limit_value,
    )


def format_validation_error(error: ValidationError) -> dict:
    """Format a ValidationError into a user-friendly response."""
    return {
        "error": "invalid_query",
        "message": str(error),
        "hint": "Please rephrase your question. The system only supports read queries.",
    }