"""
Mistral provider adapter.

Uses the official mistralai SDK. Mistral has its own API format
that's similar to but not identical to OpenAI's, so it gets
its own adapter rather than extending OpenAICompatibleProvider.
"""

from __future__ import annotations

import json
import time
from typing import Any

from pydantic import BaseModel

from ai.base import AIProvider, AIResponse, AITask, ProviderStatus
from ai.errors import AIProviderError, ErrorCategory

DEFAULT_MODEL = "mistral-small-latest"


class MistralProvider(AIProvider):

    def __init__(self, api_key: str | None, model: str | None = None):
        self._api_key = api_key
        self._model_name = model or DEFAULT_MODEL
        self._client = None
        self._status = ProviderStatus.UNAVAILABLE
        self._init_client()

    def _init_client(self) -> None:
        if not self._api_key:
            self._status = ProviderStatus.UNAVAILABLE
            return
        try:
            from mistralai import Mistral

            self._client = Mistral(api_key=self._api_key)
            self._status = ProviderStatus.AVAILABLE
        except Exception:
            self._status = ProviderStatus.ERROR

    @property
    def name(self) -> str:
        return "mistral"

    @property
    def display_name(self) -> str:
        return "Mistral AI"

    @property
    def model(self) -> str:
        return self._model_name

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

    def generate(
        self,
        prompt: str,
        system_instruction: str = "",
        task: AITask = AITask.GENERAL_QUERY,
    ) -> AIResponse:
        self._ensure_available()
        request_id = self._make_request_id()
        start = time.time()

        messages = []
        if system_instruction:
            messages.append({"role": "system", "content": system_instruction})
        messages.append({"role": "user", "content": prompt})

        try:
            response = self._client.chat.complete(
                model=self._model_name,
                messages=messages,
            )
            text = response.choices[0].message.content or ""
            return AIResponse(
                text=text,
                provider=self.name,
                model=self._model_name,
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
        self._ensure_available()
        request_id = self._make_request_id()
        start = time.time()

        schema_json = json.dumps(schema.model_json_schema(), indent=2)
        full_system = (
            f"{system_instruction}\n\n" if system_instruction else ""
        ) + (
            "You MUST respond with valid JSON only, no other text.\n"
            "The JSON must conform to this schema:\n"
            f"```json\n{schema_json}\n```"
        )

        messages = [
            {"role": "system", "content": full_system},
            {"role": "user", "content": prompt},
        ]

        try:
            response = self._client.chat.complete(
                model=self._model_name,
                messages=messages,
                response_format={"type": "json_object"},
            )
            text = response.choices[0].message.content or ""
            text = self._strip_markdown_fences(text)

            schema.model_validate_json(text)

            return AIResponse(
                text=text,
                provider=self.name,
                model=self._model_name,
                task=task,
                latency_ms=self._time_ms(start),
                request_id=request_id,
            )
        except AIProviderError:
            raise
        except Exception as exc:
            if "ValidationError" in type(exc).__name__:
                raise AIProviderError(
                    f"Request {request_id}: invalid structured output",
                    provider=self.name,
                    category=ErrorCategory.INVALID_RESPONSE,
                    original_error=exc,
                )
            self._handle_error(exc, request_id)

    @staticmethod
    def _strip_markdown_fences(text: str) -> str:
        text = text.strip()
        if text.startswith("```"):
            lines = text.split("\n")
            if lines[-1].strip() == "```":
                lines = lines[1:-1]
            else:
                lines = lines[1:]
            text = "\n".join(lines).strip()
        return text

    def _ensure_available(self) -> None:
        if not self.is_available():
            raise AIProviderError(
                "Mistral AI is not available",
                provider=self.name,
                category=ErrorCategory.AUTH_ERROR,
            )

    def _handle_error(self, exc: Exception, request_id: str) -> None:
        msg = str(exc)
        code = getattr(exc, "status_code", None)

        if code == 429 or "429" in msg:
            self._status = ProviderStatus.RATE_LIMITED
            cat = ErrorCategory.RATE_LIMITED
        elif code == 401 or "401" in msg or "auth" in msg.lower():
            self._status = ProviderStatus.AUTH_ERROR
            cat = ErrorCategory.AUTH_ERROR
        elif "timeout" in msg.lower():
            cat = ErrorCategory.TIMEOUT
        elif code and code >= 500:
            cat = ErrorCategory.SERVER_ERROR
        else:
            cat = ErrorCategory.UNKNOWN

        raise AIProviderError(
            f"Request {request_id} failed: {type(exc).__name__}",
            provider=self.name,
            category=cat,
            status_code=code,
            original_error=exc,
        )
