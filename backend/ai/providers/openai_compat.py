"""
Base class for providers using the OpenAI SDK format (xAI, Groq, Mistral, etc).

This base class handles all the common logic including telemetry, structured logging,
timeout guarantees, and fallback schema validation.
"""

from __future__ import annotations

import json
import time
from typing import Any

from pydantic import BaseModel

from ai.base import AIProvider, AIResponse, AITask, ProviderStatus
from ai.errors import AIProviderError, ErrorCategory
from utils.logger import get_structured_logger

logger = get_structured_logger("docflow.ai.openai_compat")


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
            import httpx

            # Enforce strict 60s timeout to prevent Celery worker hanging
            self._client = OpenAI(
                api_key=self._api_key,
                base_url=self._base_url,
                http_client=httpx.Client(timeout=60.0)
            )
            self._status = ProviderStatus.AVAILABLE
        except Exception as e:
            logger.error(f"Failed to initialize {self.name} client", extra={"structured_data": {"error": str(e)}})
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
        correlation_id: str | None = None,
    ) -> AIResponse:
        self._ensure_available()
        request_id = self._make_request_id()
        start = time.time()

        self._log_request("generate", request_id, correlation_id, task)

        messages = []
        if system_instruction:
            messages.append({"role": "system", "content": system_instruction})
        messages.append({"role": "user", "content": prompt})

        try:
            response = self._client.chat.completions.create(
                model=self._model_name,
                messages=messages,
            )
            return self._build_response(response, task, start, request_id, correlation_id)
        except Exception as exc:
            self._handle_error(exc, request_id, correlation_id)

    def parse(
        self,
        prompt: str,
        schema: type[BaseModel],
        system_instruction: str = "",
        task: AITask = AITask.STRUCTURED_EXTRACTION,
        correlation_id: str | None = None,
    ) -> AIResponse:
        self._ensure_available()
        request_id = self._make_request_id()
        start = time.time()

        self._log_request("parse", request_id, correlation_id, task)

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

            try:
                kwargs["response_format"] = {"type": "json_object"}
            except Exception:
                pass

            response = self._client.chat.completions.create(**kwargs)
            text = response.choices[0].message.content or ""
            text = self._strip_markdown_fences(text)

            schema.model_validate_json(text)

            # We must override the text in the response object manually for tracking purposes if we stripped it
            response.choices[0].message.content = text
            
            return self._build_response(response, task, start, request_id, correlation_id)
        except AIProviderError:
            raise
        except Exception as exc:
            if "ValidationError" in type(exc).__name__:
                logger.error("Structured output validation failed", extra={"structured_data": {
                    "provider": self.name,
                    "request_id": request_id,
                    "correlation_id": correlation_id,
                    "error": str(exc)
                }})
                raise AIProviderError(
                    f"Request {request_id}: model returned invalid structured output",
                    provider=self.name,
                    category=ErrorCategory.INVALID_RESPONSE,
                    original_error=exc,
                )
            self._handle_error(exc, request_id, correlation_id)

    # -- Internal helpers --

    def _log_request(self, method: str, request_id: str, correlation_id: str | None, task: AITask) -> None:
        logger.info(f"{self.display_name} {method} request started", extra={"structured_data": {
            "provider": self.name,
            "model": self._model_name,
            "task": task.value,
            "request_id": request_id,
            "correlation_id": correlation_id,
        }})

    def _build_response(self, response: Any, task: AITask, start_time: float, request_id: str, correlation_id: str | None) -> AIResponse:
        latency = self._time_ms(start_time)
        input_tokens = None
        output_tokens = None
        total_tokens = None

        if hasattr(response, "usage") and response.usage:
            input_tokens = getattr(response.usage, "prompt_tokens", None)
            output_tokens = getattr(response.usage, "completion_tokens", None)
            total_tokens = getattr(response.usage, "total_tokens", None)

        text = ""
        if hasattr(response, "choices") and len(response.choices) > 0:
            text = response.choices[0].message.content or ""

        logger.info(f"{self.display_name} request completed", extra={"structured_data": {
            "provider": self.name,
            "request_id": request_id,
            "correlation_id": correlation_id,
            "latency_ms": latency,
            "input_tokens": input_tokens,
            "output_tokens": output_tokens,
        }})

        return AIResponse(
            text=text,
            provider=self.name,
            model=self._model_name,
            task=task,
            latency_ms=latency,
            request_id=request_id,
            correlation_id=correlation_id,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            total_tokens=total_tokens,
        )

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
                f"{self.display_name} is not available",
                provider=self.name,
                category=ErrorCategory.AUTH_ERROR,
            )

    def _handle_error(self, exc: Exception, request_id: str, correlation_id: str | None) -> None:
        msg = str(exc)
        code = getattr(exc, "status_code", None)

        if code == 429 or "429" in msg or "rate" in msg.lower():
            self._status = ProviderStatus.RATE_LIMITED
            cat = ErrorCategory.RATE_LIMITED
        elif code == 401 or "401" in msg or "auth" in msg.lower():
            self._status = ProviderStatus.AUTH_ERROR
            cat = ErrorCategory.AUTH_ERROR
        elif code == 400 or "400" in msg:
            cat = ErrorCategory.INVALID_REQUEST
        elif code == 408 or "timeout" in msg.lower():
            cat = ErrorCategory.TIMEOUT
        elif code and code >= 500:
            cat = ErrorCategory.SERVER_ERROR
        elif "connection" in msg.lower() or "network" in msg.lower():
            cat = ErrorCategory.NETWORK_ERROR
        else:
            cat = ErrorCategory.UNKNOWN

        logger.error(f"{self.display_name} request failed", extra={"structured_data": {
            "provider": self.name,
            "request_id": request_id,
            "correlation_id": correlation_id,
            "error_category": cat.value,
            "error_message": msg,
            "status_code": code
        }})

        raise AIProviderError(
            f"Request {request_id} failed: {type(exc).__name__}",
            provider=self.name,
            category=cat,
            status_code=code,
            original_error=exc,
        )
