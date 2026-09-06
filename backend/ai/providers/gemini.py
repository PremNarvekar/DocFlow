"""
Google Gemini provider adapter.

Uses the google-genai SDK with native structured output via response_schema.
This is the most mature integration — it was the original provider.

Gemini's structured output is the gold standard: you pass a Pydantic model
as response_schema and the API returns JSON that matches it. No parsing hacks.
"""

from __future__ import annotations

import json
import time
from typing import Any

from pydantic import BaseModel

from ai.base import AIProvider, AIResponse, AITask, ProviderStatus
from ai.errors import AIProviderError, ErrorCategory

DEFAULT_MODEL = "gemini-2.5-flash"


class GeminiProvider(AIProvider):

    def __init__(self, api_key: str | None, model: str | None = None):
        self._api_key = api_key
        self._model = model or DEFAULT_MODEL
        self._client = None
        self._status = ProviderStatus.UNAVAILABLE
        self._init_client()

    def _init_client(self) -> None:
        if not self._api_key:
            self._status = ProviderStatus.UNAVAILABLE
            return
        try:
            from google import genai

            self._client = genai.Client(api_key=self._api_key)
            self._status = ProviderStatus.AVAILABLE
        except Exception:
            self._status = ProviderStatus.ERROR

    # -- ABC properties --

    @property
    def name(self) -> str:
        return "gemini"

    @property
    def display_name(self) -> str:
        return "Google Gemini"

    @property
    def model(self) -> str:
        return self._model

    @property
    def supported_tasks(self) -> list[AITask]:
        return [
            AITask.DOCUMENT_CLASSIFICATION,
            AITask.STRUCTURED_EXTRACTION,
            AITask.GENERAL_QUERY,
            AITask.SUMMARIZATION,
        ]

    def is_available(self) -> bool:
        return self._client is not None and self._status in (
            ProviderStatus.AVAILABLE,
            ProviderStatus.DEGRADED,
        )

    def get_status(self) -> ProviderStatus:
        return self._status

    # -- Core methods --

    def generate(
        self,
        prompt: str,
        system_instruction: str = "",
        task: AITask = AITask.GENERAL_QUERY,
    ) -> AIResponse:
        self._ensure_available()
        from google.genai import types

        request_id = self._make_request_id()
        start = time.time()
        try:
            config = types.GenerateContentConfig()
            if system_instruction:
                config.system_instruction = system_instruction

            response = self._client.models.generate_content(
                model=self._model,
                contents=prompt,
                config=config,
            )
            return AIResponse(
                text=response.text,
                provider=self.name,
                model=self._model,
                task=task,
                latency_ms=self._time_ms(start),
                request_id=request_id,
            )
        except Exception as exc:
            self._handle_error(exc, request_id)

    def parse(
        self,
        prompt: str,
        schema: type[BaseModel],
        system_instruction: str = "",
        task: AITask = AITask.STRUCTURED_EXTRACTION,
    ) -> AIResponse:
        """Use Gemini's native structured output (response_schema)."""
        self._ensure_available()
        from google.genai import types

        request_id = self._make_request_id()
        start = time.time()
        try:
            config = types.GenerateContentConfig(
                response_mime_type="application/json",
                response_schema=schema,
            )
            if system_instruction:
                config.system_instruction = system_instruction

            response = self._client.models.generate_content(
                model=self._model,
                contents=prompt,
                config=config,
            )
            # Validate the response against the schema before returning
            schema.model_validate_json(response.text)

            return AIResponse(
                text=response.text,
                provider=self.name,
                model=self._model,
                task=task,
                latency_ms=self._time_ms(start),
                request_id=request_id,
            )
        except AIProviderError:
            raise
        except Exception as exc:
            self._handle_error(exc, request_id)

    # -- Internal helpers --

    def _ensure_available(self) -> None:
        if not self.is_available():
            raise AIProviderError(
                "Gemini is not available",
                provider=self.name,
                category=ErrorCategory.AUTH_ERROR,
            )

    def _handle_error(self, exc: Exception, request_id: str) -> None:
        """Convert provider-specific exceptions into AIProviderError."""
        msg = str(exc)
        code = getattr(exc, "status_code", None) or getattr(exc, "code", None)

        if "429" in msg or "RESOURCE_EXHAUSTED" in msg:
            self._status = ProviderStatus.RATE_LIMITED
            cat = ErrorCategory.RATE_LIMITED
        elif "401" in msg or "UNAUTHENTICATED" in msg:
            self._status = ProviderStatus.AUTH_ERROR
            cat = ErrorCategory.AUTH_ERROR
        elif "timeout" in msg.lower() or "deadline" in msg.lower():
            cat = ErrorCategory.TIMEOUT
        elif "500" in msg or "503" in msg or "INTERNAL" in msg:
            cat = ErrorCategory.SERVER_ERROR
        else:
            cat = ErrorCategory.UNKNOWN

        raise AIProviderError(
            f"Request {request_id} failed: {type(exc).__name__}",
            provider=self.name,
            category=cat,
            status_code=int(code) if code else None,
            original_error=exc,
        )
