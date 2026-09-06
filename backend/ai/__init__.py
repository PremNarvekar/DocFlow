"""
DocFlow AI package — public API.

Usage:
    from ai import get_router
    router = get_router()
    response = router.generate("What is this document?")
    response = router.parse("Extract invoice data...", InvoiceData)

The router is a singleton — built once on first access from config.
"""

from __future__ import annotations

import os

from ai.base import AIProvider, AIResponse, AITask, ProviderInfo, ProviderStatus
from ai.errors import AIProviderError, AIRouterError, ErrorCategory
from ai.router import AIRouter
from ai.registry import ProviderRegistry, build_registry

__all__ = [
    "get_router",
    "AIRouter",
    "AIProvider",
    "AIResponse",
    "AITask",
    "ProviderInfo",
    "ProviderStatus",
    "AIProviderError",
    "AIRouterError",
    "ErrorCategory",
]

_router: AIRouter | None = None


def get_router() -> AIRouter:
    """Get the application-wide AI router singleton.

    Built lazily on first call using values from config.py.
    """
    global _router
    if _router is None:
        _router = _build_router()
    return _router


def _build_router() -> AIRouter:
    """Construct the router from application configuration."""
    import config

    mock_mode = config.AI_MODE.lower() == "mock"
    mock_failure = os.getenv("MOCK_FAILURE")

    registry = build_registry(
        api_keys=config.PROVIDER_API_KEYS,
        model_overrides=config.PROVIDER_MODELS,
        mock_mode=mock_mode,
        mock_failure=mock_failure,
    )

    priority = [
        name.strip()
        for name in config.AI_PROVIDER_PRIORITY.split(",")
        if name.strip()
    ]

    return AIRouter(registry=registry, priority_order=priority)


def reset_router() -> None:
    """Reset the singleton (for testing)."""
    global _router
    _router = None
