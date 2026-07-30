"""
core/tracing.py

LangSmith tracing setup.
Gates on LANGSMITH_API_KEY - if not configured, tracing is silently disabled.

Usage in other modules:
    from core.tracing import maybe_trace
    with maybe_trace("my_span", "chain", inputs={...}) as run:
        ...
"""

import logging
import os
from typing import Any

logger = logging.getLogger(__name__)


# ─────────────────────────────────────────────────────────────
# LangSmith availability check
# We soft-import so the app can still function if the
# package is somehow missing (e.g. in a minimal install).
# ─────────────────────────────────────────────────────────────
_HAS_LANGSMITH = False
_traceable = None
_wrap_openai = None
_ls = None
_Client = None
_configure = None

try:
    from langsmith import Client as _Client
    from langsmith import configure as _configure
    from langsmith import traceable as _traceable
    from langsmith import tracing_context
    from langsmith.wrappers import wrap_openai as _wrap_openai

    import langsmith as _ls

    _HAS_LANGSMITH = True
except ImportError:
    pass


def is_tracing_enabled() -> bool:
    """Check whether LangSmith tracing is currently active."""
    return _HAS_LANGSMITH and os.getenv("LANGSMITH_TRACING") == "true"


def setup_tracing(
    api_key: str | None,
    project_name: str = "ai-data-agent",
) -> object | None:
    """
    Initialise LangSmith and enable tracing.

    Call once at application startup. If *api_key* is falsy,
    tracing remains disabled and this function returns None.

    Returns the LangSmith Client instance if enabled, else None.
    """
    if not _HAS_LANGSMITH:
        logger.info("LangSmith tracing disabled — package not installed")
        return None

    if not api_key:
        logger.info("LangSmith tracing disabled — no API key")
        return None

    client = _Client(api_key=api_key)

    # Tag traces with the running environment
    env = os.getenv("APP_ENV", "development")

    _configure(
        client=client,
        enabled=True,
        project_name=project_name,
        metadata={"environment": env},
    )

    logger.info(f"LangSmith tracing enabled | project={project_name} | env={env}")
    return client


# ─────────────────────────────────────────────────────────────
# Safe re-exports — these always exist, but are no-ops when
# LangSmith is not available.
# ─────────────────────────────────────────────────────────────


class _DummyRun:
    """No-op context manager returned when LangSmith is disabled."""

    def end(self, outputs: dict[str, Any] | None = None) -> None:
        pass

    def add_metadata(self, metadata: dict[str, Any]) -> None:
        pass

    def add_tags(self, tags: list[str]) -> None:
        pass

    def __enter__(self):
        return self

    def __exit__(self, *args):
        pass


def trace(
    name: str,
    run_type: str = "chain",
    inputs: dict[str, Any] | None = None,
    **kwargs,
) -> _DummyRun:
    """
    Context manager that creates a LangSmith trace span.
    Falls back to a no-op when LangSmith is disabled.

    Usage:
        with trace("my_span", run_type="chain", inputs={"key": "val"}) as run:
            ...
            run.end(outputs={"result": "..."})
    """
    if _HAS_LANGSMITH:
        return _ls.trace(name, run_type=run_type, inputs=inputs, **kwargs)
    return _DummyRun()


def traceable(
    *args,
    **kwargs,
):
    """
    Decorator that auto-traces a function call.
    Falls back to a pass-through when LangSmith is disabled.
    """
    if _HAS_LANGSMITH:
        return _traceable(*args, **kwargs)
    # No-op decorator: supports both @traceable and @traceable(kwargs=...)
    if args and callable(args[0]):
        return args[0]
    return lambda f: f


def wrap_openai(client):
    """
    Wrap an OpenAI client to auto-capture LLM calls.
    Falls back to the raw client when LangSmith is disabled.
    """
    if _HAS_LANGSMITH:
        return _wrap_openai(client)
    return client
