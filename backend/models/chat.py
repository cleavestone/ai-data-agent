"""
models/chat.py

Pydantic models for the chat API — request and response shapes.
Pydantic validates incoming JSON and serialises outgoing responses automatically.
"""

from typing import Any
from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    question: str = Field(..., min_length=1, max_length=2000)


class ChatResponse(BaseModel):
    success: bool
    answer: str
    visualisation: str          # VisualisationType value — str enum, safe to send as str
    columns: list[str]
    rows: list[dict[str, Any]]
    row_count: int
    cached: bool
    execution_time_ms: float
    sql_executed: str = ""      # the SQL that was run — empty on cache hits or failures


class HealthResponse(BaseModel):
    status: str                 # "healthy" | "degraded" | "unhealthy"
    postgres_admin: bool
    postgres_readonly: bool
    redis: bool
    version: str
