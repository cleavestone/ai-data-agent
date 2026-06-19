"""
agents/base_agent.py

Shared OpenAI client used by all agents.
Centralises model config, retry logic, and error handling
so individual agents stay focused on their job.
"""

import logging
from openai import AsyncOpenAI
from core.config import settings

logger = logging.getLogger(__name__)

# ─────────────────────────────────────────────────────────────
# Single shared client instance
# AsyncOpenAI is thread-safe and designed to be reused
# ─────────────────────────────────────────────────────────────
openai_client = AsyncOpenAI(api_key=settings.openai_api_key)


def get_client() -> AsyncOpenAI:
    """Return the shared OpenAI client."""
    return openai_client


def get_model() -> str:
    """Return the configured model name."""
    return settings.openai_model


def get_max_tokens() -> int:
    """Return the configured max tokens."""
    return settings.openai_max_tokens