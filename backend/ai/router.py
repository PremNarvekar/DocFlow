"""
AI Router — task-aware routing with automatic fallback.

The router is the ONLY component that the pipeline talks to.
It picks the best available provider, calls it, and if it fails,
tries the next one in priority order.

Design:
  1. Receive request (task + prompt + optional schema)
  2. Get priority-ordered list of providers for this task
  3. Try provider #1
  4. If retryable failure → try provider #2
  5. If non-retryable failure → raise immediately
  6. If all fail → raise AIRouterError with all errors

WHY deterministic priority:
  - Predictable behavior — you know which provider handles requests
  - Debuggable — "why did it use Groq?" → "because Gemini returned 429"
  - Cost control — put the cheapest/fastest provider first
  - No surprise bills from accidentally hitting expensive providers

WHY NOT call all providers simultaneously:
  - Wastes money (every call costs)
  - Wastes latency (slowest provider determines response time)
  - Wastes rate limits (burning quota on redundant calls)
  - Unnecessarily complex
"""

from __future__ import annotations

import logging

from pydantic import BaseModel

from ai.base import AIProvider, AIResponse, AITask, ProviderInfo
from ai.errors import AIProviderError, AIRouterError
from ai.registry import ProviderRegistry

logger = logging.getLogger(__name__)

# Maximum number of providers to try before giving up
MAX_FALLBACK_ATTEMPTS = 4


class AIRouter:
    """Routes AI requests to the best available provider with fallback."""

    def __init__(
        self,
        registry: ProviderRegistry,
        priority_order: list[str] | None = None,
    ):
        self._registry = registry
        self._priority = priority_order or []

    def generate(
        self,
        prompt: str,
        system_instruction: str = "",
        task: AITask = AITask.GENERAL_QUERY,
    ) -> AIResponse:
        """Route a text generation request with fallback."""
        providers = self._get_ordered_providers(task)

        if not providers:
            raise AIRouterError(
                f"No available providers for task={task.value}. "
                f"Configure at least one API key."
            )

        errors: list[AIProviderError] = []

        for i, provider in enumerate(providers[:MAX_FALLBACK_ATTEMPTS]):
            try:
                logger.info(
                    "AI request: task=%s provider=%s model=%s",
                    task.value, provider.name, provider.model,
                )
                response = provider.generate(
                    prompt=prompt,
                    system_instruction=system_instruction,
                    task=task,
                )
                if i > 0:
                    response.fallback_used = True
                    response.fallback_from = providers[0].name
                    logger.warning(
                        "Fallback success: %s → %s (after %d failures)",
                        providers[0].name, provider.name, i,
                    )
                logger.info(
                    "AI response: provider=%s latency=%.1fms request_id=%s",
                    response.provider, response.latency_ms, response.request_id,
                )
                return response

            except AIProviderError as exc:
                errors.append(exc)
                logger.warning(
                    "Provider %s failed: %s (category=%s, retryable=%s)",
                    provider.name, exc, exc.category.value, exc.is_retryable,
                )
                if not exc.should_try_other_provider:
                    # Non-retryable across all providers (bad request)
                    raise

        raise AIRouterError(
            f"All {len(errors)} provider(s) failed for task={task.value}",
            errors=errors,
        )

    def parse(
        self,
        prompt: str,
        schema: type[BaseModel],
        system_instruction: str = "",
        task: AITask = AITask.STRUCTURED_EXTRACTION,
    ) -> AIResponse:
        """Route a structured extraction request with fallback."""
        providers = self._get_ordered_providers(task)

        if not providers:
            raise AIRouterError(
                f"No available providers for task={task.value}. "
                f"Configure at least one API key."
            )

        errors: list[AIProviderError] = []

        for i, provider in enumerate(providers[:MAX_FALLBACK_ATTEMPTS]):
            try:
                logger.info(
                    "AI parse: task=%s provider=%s schema=%s",
                    task.value, provider.name, schema.__name__,
                )
                response = provider.parse(
                    prompt=prompt,
                    schema=schema,
                    system_instruction=system_instruction,
                    task=task,
                )
                if i > 0:
                    response.fallback_used = True
                    response.fallback_from = providers[0].name
                    logger.warning(
                        "Fallback success: %s → %s (after %d failures)",
                        providers[0].name, provider.name, i,
                    )
                logger.info(
                    "AI parse response: provider=%s latency=%.1fms",
                    response.provider, response.latency_ms,
                )
                return response

            except AIProviderError as exc:
                errors.append(exc)
                logger.warning(
                    "Provider %s parse failed: %s (category=%s)",
                    provider.name, exc, exc.category.value,
                )
                if not exc.should_try_other_provider:
                    raise

        raise AIRouterError(
            f"All {len(errors)} provider(s) failed for task={task.value}",
            errors=errors,
        )

    def get_provider_status(self) -> list[ProviderInfo]:
        """Get status of all providers — safe for frontend display."""
        return self._registry.get_all_info()

    def _get_ordered_providers(self, task: AITask) -> list[AIProvider]:
        """Return providers ordered by priority, filtered by task + availability."""
        available = self._registry.get_available(task=task)

        if not self._priority:
            return available

        # Order by priority list, then append any not in the list
        ordered = []
        seen = set()
        for name in self._priority:
            provider = self._registry.get(name)
            if provider and provider.is_available() and task in provider.supported_tasks:
                ordered.append(provider)
                seen.add(name)

        for p in available:
            if p.name not in seen:
                ordered.append(p)

        return ordered
