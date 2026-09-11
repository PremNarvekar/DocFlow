"""
Google Gemini provider adapter.

Uses the google-genai SDK with native structured output via response_schema.
This is the most mature integration.

Gemini's structured output is the gold standard: you pass a Pydantic model
as response_schema and the API returns JSON that matches it. No parsing hacks.
"""

from __future__ import annotations

import time
import uuid
import os
from typing import Any

from pydantic import BaseModel

from ai.base import AIProvider, AIResponse, AITask, ProviderStatus
from ai.errors import AIProviderError, ErrorCategory

from utils.logger import get_structured_logger

DEFAULT_MODEL = "gemini-2.5-flash"
logger = get_structured_logger("docflow.ai.gemini")

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
            # Initialize with native http_options for timeout
            self._client = genai.Client(
                api_key=self._api_key, 
                http_options={'timeout': 60000}  # 60s timeout
            )
            self._status = ProviderStatus.AVAILABLE
        except Exception as e:
            logger.error("Failed to initialize Gemini client", extra={"structured_data": {"error": str(e)}})
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
        correlation_id: str | None = None,
    ) -> AIResponse:
        self._ensure_available()
        from google.genai import types

        request_id = self._make_request_id()
        start = time.time()
        
        self._log_request("generate", request_id, correlation_id, task)

        try:
            config = types.GenerateContentConfig()
            if system_instruction:
                config.system_instruction = system_instruction

            response = self._client.models.generate_content(
                model=self._model,
                contents=prompt,
                config=config,
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
        """Use Gemini's native structured output (response_schema)."""
        self._ensure_available()
        from google.genai import types

        request_id = self._make_request_id()
        start = time.time()
        
        self._log_request("parse", request_id, correlation_id, task)

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

            return self._build_response(response, task, start, request_id, correlation_id)
        except AIProviderError:
            raise
        except Exception as exc:
            self._handle_error(exc, request_id, correlation_id)

    # -- Internal helpers --

    def _log_request(self, method: str, request_id: str, correlation_id: str | None, task: AITask) -> None:
        logger.info(f"Gemini {method} request started", extra={"structured_data": {
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

        if hasattr(response, "usage_metadata") and response.usage_metadata:
            input_tokens = getattr(response.usage_metadata, "prompt_token_count", None)
            output_tokens = getattr(response.usage_metadata, "candidates_token_count", None)
            total_tokens = getattr(response.usage_metadata, "total_token_count", None)

        logger.info("Gemini request completed", extra={"structured_data": {
            "provider": self.name,
            "request_id": request_id,
            "correlation_id": correlation_id,
            "latency_ms": latency,
            "input_tokens": input_tokens,
            "output_tokens": output_tokens,
        }})

        return AIResponse(
            text=response.text,
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
                "Gemini is not available",
                provider=self.name,
                category=ErrorCategory.AUTH_ERROR,
            )

    def _handle_error(self, exc: Exception, request_id: str, correlation_id: str | None) -> None:
        """Convert provider-specific exceptions into AIProviderError."""
        msg = str(exc)
        code = getattr(exc, "status_code", None) or getattr(exc, "code", None)

        if "429" in msg or "RESOURCE_EXHAUSTED" in msg:
            self._status = ProviderStatus.RATE_LIMITED
            cat = ErrorCategory.RATE_LIMITED
        elif "401" in msg or "UNAUTHENTICATED" in msg or "API_KEY_INVALID" in msg:
            self._status = ProviderStatus.AUTH_ERROR
            cat = ErrorCategory.AUTH_ERROR
        elif "timeout" in msg.lower() or "deadline" in msg.lower():
            cat = ErrorCategory.TIMEOUT
        elif "500" in msg or "503" in msg or "INTERNAL" in msg:
            cat = ErrorCategory.SERVER_ERROR
        else:
            cat = ErrorCategory.UNKNOWN

        logger.error("Gemini request failed", extra={"structured_data": {
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
            status_code=int(code) if code else None,
            original_error=exc,
        )
