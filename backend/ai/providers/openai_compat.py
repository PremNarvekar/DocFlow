"""
Base adapter for OpenAI-compatible providers.

xAI, Groq, Cerebras, and OpenRouter all expose an OpenAI-compatible
chat completions endpoint. The only differences are:
  - base_url
  - api_key
  - default model name
  - supported tasks

This base class handles all the common logic. Each provider subclass
just supplies its config constants.

For structured output: these providers support JSON mode or
function-calling. We use the simpler approach: instruct the model
to return JSON matching the schema, then validate with Pydantic.
This is less reliable than Gemini's native response_schema but
works across all OpenAI-compatible endpoints.
"""

from __future__ import annotations

import json
import time
from typing import Any

from pydantic import BaseModel

from ai.base import AIProvider, AIResponse, AITask, ProviderStatus
from ai.errors import AIProviderError, ErrorCategory


class OpenAICompatibleProvider(AIProvider):
    """Shared implementation for providers using the OpenAI chat API format."""

    # Subclasses MUST set these
    _provider_name: str = ""
    _provider_display_name: str = ""
    _base_url: str = ""
    _default_model: str = ""
    _provider_supported_tasks: list[AITask] = []

    def __init__(self, api_key: str | None, model: str | None = None):
        self._api_key = api_key
        self._model_name = model or self._default_model
        self._client = None
        self._status = ProviderStatus.UNAVAILABLE
        self._init_client()

    def _init_client(self) -> None:
        if not self._api_key:
            self._status = ProviderStatus.UNAVAILABLE
            return
        try:
            from openai import OpenAI

            self._client = OpenAI(
                api_key=self._api_key,
                base_url=self._base_url,
            )
            self._status = ProviderStatus.AVAILABLE
        except Exception:
            self._status = ProviderStatus.ERROR

    # -- ABC properties --

    @property
    def name(self) -> str:
        return self._provider_name

    @property
    def display_name(self) -> str:
        return self._provider_display_name

    @property
    def model(self) -> str:
        return self._model_name

    @property
    def supported_tasks(self) -> list[AITask]:
        return self._provider_supported_tasks

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
        request_id = self._make_request_id()
        start = time.time()

        messages = []
        if system_instruction:
            messages.append({"role": "system", "content": system_instruction})
        messages.append({"role": "user", "content": prompt})

        try:
            response = self._client.chat.completions.create(
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
        """Structured output via JSON mode + Pydantic validation.

        We build a system instruction that includes the JSON schema,
        ask for JSON output, then validate the response.
        """
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
            kwargs: dict[str, Any] = {
                "model": self._model_name,
                "messages": messages,
            }

            # Use JSON mode if available (most OpenAI-compatible APIs support it)
            try:
                kwargs["response_format"] = {"type": "json_object"}
            except Exception:
                pass

            response = self._client.chat.completions.create(**kwargs)
            text = response.choices[0].message.content or ""

            # Strip markdown fences if the model wrapped the JSON
            text = self._strip_markdown_fences(text)

            # Validate against schema — raises ValidationError if bad
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
            # Check if it's a Pydantic ValidationError
            if "ValidationError" in type(exc).__name__:
                raise AIProviderError(
                    f"Request {request_id}: model returned invalid structured output",
                    provider=self.name,
                    category=ErrorCategory.INVALID_RESPONSE,
                    original_error=exc,
                )
            self._handle_error(exc, request_id)

    # -- Internal helpers --

    @staticmethod
    def _strip_markdown_fences(text: str) -> str:
        """Remove ```json ... ``` wrappers that models sometimes add."""
        text = text.strip()
        if text.startswith("```"):
            lines = text.split("\n")
            # Remove first line (```json) and last line (```)
            if lines[-1].strip() == "```":
                lines = lines[1:-1]
            else:
                lines = lines[1:]
            text = "\n".join(lines).strip()
        return text

    def _ensure_available(self) -> None:
        if not self.is_available():
            raise AIProviderError(
                f"{self.display_name} is not available",
                provider=self.name,
                category=ErrorCategory.AUTH_ERROR,
            )

    def _handle_error(self, exc: Exception, request_id: str) -> None:
        """Convert OpenAI-style exceptions into AIProviderError."""
        msg = str(exc)
        code = getattr(exc, "status_code", None)

        if code == 429 or "429" in msg or "rate" in msg.lower():
            self._status = ProviderStatus.RATE_LIMITED
            cat = ErrorCategory.RATE_LIMITED
        elif code == 401 or "401" in msg or "auth" in msg.lower():
            self._status = ProviderStatus.AUTH_ERROR
            cat = ErrorCategory.AUTH_ERROR
        elif code == 408 or "timeout" in msg.lower():
            cat = ErrorCategory.TIMEOUT
        elif code and code >= 500:
            cat = ErrorCategory.SERVER_ERROR
        elif "connection" in msg.lower() or "network" in msg.lower():
            cat = ErrorCategory.NETWORK_ERROR
        else:
            cat = ErrorCategory.UNKNOWN

        raise AIProviderError(
            f"Request {request_id} failed: {type(exc).__name__}",
            provider=self.name,
            category=cat,
            status_code=code,
            original_error=exc,
        )
