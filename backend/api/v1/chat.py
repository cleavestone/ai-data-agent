"""
api/v1/chat.py

The main chat endpoint.
Receives a natural language question, returns a structured response
with AI answer + data + visualisation type.

POST /api/v1/chat
"""

import logging
from fastapi import APIRouter, HTTPException
from models.chat import ChatRequest, ChatResponse
from services.chat_service import handle_question

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """
    Process a natural language question about the business data.

    The API layer does only three things:
    1. Validate the incoming request (Pydantic does this automatically)
    2. Call the service layer
    3. Return the response

    All business logic lives in the service layer — not here.
    """
    logger.info(f"Chat request received: {request.question[:50]}...")

    try:
        result = await handle_question(request.question)

        return ChatResponse(
            success=True,
            answer=result.answer,
            visualisation=result.visualisation,
            columns=result.columns,
            rows=result.rows,
            row_count=result.row_count,
            cached=result.cached,
            execution_time_ms=result.execution_time_ms,
            sql_executed=result.sql_executed,
        )

    except Exception as e:
        logger.error(f"Unexpected error in chat endpoint: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail="An unexpected error occurred. Please try again.",
        )