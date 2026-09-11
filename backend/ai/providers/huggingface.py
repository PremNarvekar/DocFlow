"""Hugging Face Inference Provider.

Uses the huggingface_hub InferenceClient to query serverless endpoints.
Provides production telemetry, strict timeouts, correlation IDs, and token extraction.
"""

from __future__ import annotations

import json
import time
from typing import Any

from pydantic import BaseModel

from ai.base import (
    AIProvider,
    AIResponse,
    AITask,
    ProviderStatus,
)
from ai.errors import AIProviderError, ErrorCategory
from utils.logger import get_structured_logger

logger = get_structured_logger("docflow.ai.huggingface")


class HuggingFaceProvider(AIProvider):

    def __init__(
        self,
        api_key: str | None = None,
        model: str | None = None,
    ) -> None:

        self._api_key = api_key
        # Default to Llama-3.1-70B as determined in DOCFLOW_04_HF_MODEL_EVALUATION.md
        self._model = model or "meta-llama/Meta-Llama-3.1-70B-Instruct"
        self._status = (
            ProviderStatus.AVAILABLE
            if api_key
            else ProviderStatus.UNAVAILABLE
        )

        self._client = None
        self._init_client()

    def _init_client(self) -> None:
        if not self._api_key:
            return
        try:
            from huggingface_hub import InferenceClient

            # Enforce 60s timeout at the client level
            self._client = InferenceClient(
                api_key=self._api_key,
                provider="auto",
                timeout=60.0
            )
        except Exception as e:
            logger.error(f"Failed to initialize Hugging Face client", extra={"structured_data": {"error": str(e)}})
            self._status = ProviderStatus.ERROR

    @property
    def name(self) -> str:
        return "huggingface"

    @property
    def display_name(self) -> str:
        return "Hugging Face"

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
        return bool(self._api_key and self._client and self._status in (ProviderStatus.AVAILABLE, ProviderStatus.DEGRADED))

    def get_status(self) -> ProviderStatus:
        return self._status

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

        try:
            messages = []
            if system_instruction:
                messages.append({"role": "system", "content": system_instruction})
            messages.append({"role": "user", "content": prompt})

            response = self._client.chat.completions.create(
                model=self._model,
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

        try:
            # Hugging Face TGI endpoints support json_schema constrained decoding
            response_format = {
                "type": "json_schema",
                "json_schema": {
                    "name": schema.__name__,
                    "schema": schema.model_json_schema(),
                    "strict": True,
                },
            }

            messages = []
            if system_instruction:
                messages.append({"role": "system", "content": system_instruction})
            messages.append({"role": "user", "content": prompt})

            response = self._client.chat.completions.create(
                model=self._model,
                messages=messages,
                response_format=response_format,
            )

            text = response.choices[0].message.content or ""

            # Application-level validation
            schema.model_validate_json(text)

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

    # -- Internal Helpers --

    def _log_request(self, method: str, request_id: str, correlation_id: str | None, task: AITask) -> None:
        logger.info(f"{self.display_name} {method} request started", extra={"structured_data": {
            "provider": self.name,
            "model": self._model,
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
            model=self._model,
            task=task,
            latency_ms=latency,
            request_id=request_id,
            correlation_id=correlation_id,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            total_tokens=total_tokens,
        )

    def _ensure_available(self) -> None:
        if not self.is_available():
            raise AIProviderError(
                "Hugging Face is not available",
                provider=self.name,
                category=ErrorCategory.AUTH_ERROR,
            )

    def _handle_error(
        self,
        exc: Exception,
        request_id: str,
        correlation_id: str | None,
    ) -> None:
        message = str(exc)
        code = getattr(exc, "status_code", None)

        if code == 429 or "429" in message or "rate" in message.lower():
            self._status = ProviderStatus.RATE_LIMITED
            category = ErrorCategory.RATE_LIMITED
        elif code == 401 or code == 403 or "401" in message or "unauthorized" in message.lower():
            self._status = ProviderStatus.AUTH_ERROR
            category = ErrorCategory.AUTH_ERROR
        elif code == 400 or "400" in message:
            category = ErrorCategory.INVALID_REQUEST
        elif code == 408 or "timeout" in message.lower():
            category = ErrorCategory.TIMEOUT
        elif code and code >= 500 or "500" in message or "502" in message or "503" in message:
            category = ErrorCategory.SERVER_ERROR
        else:
            category = ErrorCategory.UNKNOWN

        logger.error(f"{self.display_name} request failed", extra={"structured_data": {
            "provider": self.name,
            "request_id": request_id,
            "correlation_id": correlation_id,
            "error_category": category.value,
            "error_message": message,
            "status_code": code
        }})

        raise AIProviderError(
            f"Request {request_id} failed: {type(exc).__name__}",
            provider=self.name,
            category=category,
            status_code=code,
            original_error=exc,
        )