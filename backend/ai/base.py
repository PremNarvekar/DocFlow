"""
AI provider abstraction layer.

Defines the contract that every AI provider must implement,
plus shared data models used by the router and pipeline.

Design choice: abc.ABC with @abstractmethod
- Enforces the contract at class instantiation time
- If a provider forgets to implement generate(), it crashes immediately
- Not at some random runtime moment weeks later

Rejected alternatives:
- Protocol: structural subtyping, but missing methods aren't caught until call time
- Duck typing: no enforcement, no documentation
"""

from __future__ import annotations

import time
import uuid
from abc import ABC, abstractmethod
from enum import Enum
from typing import Any

from pydantic import BaseModel


class AITask(str, Enum):
    """What the pipeline is asking the AI to do.

    The router uses this to find providers that support
    the requested task, so extraction isn't sent to a
    classification-only provider.
    """

    DOCUMENT_CLASSIFICATION = "document_classification"
    STRUCTURED_EXTRACTION = "structured_extraction"
    GENERAL_QUERY = "general_query"
    SUMMARIZATION = "summarization"


class ProviderStatus(str, Enum):
    """Health state of a single provider."""

    AVAILABLE = "available"
    UNAVAILABLE = "unavailable"
    DEGRADED = "degraded"
    RATE_LIMITED = "rate_limited"
    AUTH_ERROR = "auth_error"
    ERROR = "error"


class ProviderInfo(BaseModel):
    """Public metadata for a provider — safe to return to frontends."""

    name: str
    display_name: str
    model: str
    status: ProviderStatus
    supported_tasks: list[AITask]
    reason: str = ""


class AIResponse(BaseModel):
    """Standardized response from any provider.

    Every provider returns this, regardless of their native format.
    The pipeline never sees provider-specific response objects.
    """

    text: str
    provider: str
    model: str
    task: AITask
    latency_ms: float
    request_id: str
    correlation_id: str | None = None
    input_tokens: int | None = None
    output_tokens: int | None = None
    total_tokens: int | None = None
    fallback_used: bool = False
    fallback_from: str | None = None


class AIProvider(ABC):
    """Contract that every AI provider adapter must implement.

    Subclasses translate this interface into provider-specific SDK calls.
    The rest of DocFlow only ever talks to this interface.
    """

    @property
    @abstractmethod
    def name(self) -> str:
        """Short identifier, e.g. 'gemini', 'groq'. Used in logs and config."""
        ...

    @property
    @abstractmethod
    def display_name(self) -> str:
        """Human-readable name, e.g. 'Google Gemini'. Used in UI."""
        ...

    @property
    @abstractmethod
    def model(self) -> str:
        """Current model identifier, e.g. 'gemini-2.5-flash'."""
        ...

    @property
    @abstractmethod
    def supported_tasks(self) -> list[AITask]:
        """Which AITask values this provider can handle."""
        ...

    @abstractmethod
    def is_available(self) -> bool:
        """True if the provider has a valid API key and is ready to serve."""
        ...

    @abstractmethod
    def get_status(self) -> ProviderStatus:
        """Current health. Used by router to skip broken providers."""
        ...

    @abstractmethod
    def generate(
        self,
        prompt: str,
        system_instruction: str = "",
        task: AITask = AITask.GENERAL_QUERY,
        correlation_id: str | None = None,
    ) -> AIResponse:
        """Send a text prompt, get a text response."""
        ...

    @abstractmethod
    def parse(
        self,
        prompt: str,
        schema: type[BaseModel],
        system_instruction: str = "",
        task: AITask = AITask.STRUCTURED_EXTRACTION,
        correlation_id: str | None = None,
    ) -> AIResponse:
        """Send a text prompt, get a response that conforms to a Pydantic schema.

        The response.text must be valid JSON that can be passed to
        schema.model_validate_json(response.text).

        Providers that support native structured output should use it.
        Others should instruct the model to return JSON and validate after.
        """
        ...

    def get_info(self) -> ProviderInfo:
        """Build a ProviderInfo snapshot — safe for frontend display."""
        return ProviderInfo(
            name=self.name,
            display_name=self.display_name,
            model=self.model,
            status=self.get_status(),
            supported_tasks=self.supported_tasks,
        )

    @staticmethod
    def _make_request_id() -> str:
        return uuid.uuid4().hex[:12]

    @staticmethod
    def _time_ms(start: float) -> float:
        return round((time.time() - start) * 1000, 1)
