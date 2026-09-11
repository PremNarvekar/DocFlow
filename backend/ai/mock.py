"""
Mock AI provider for testing.

Returns deterministic responses without calling any API.
Supports controlled failure injection for testing fallback logic.

Usage:
  AI_MODE=mock                    → deterministic success
  AI_MODE=mock  MOCK_FAILURE=timeout  → simulated timeout
  AI_MODE=mock  MOCK_FAILURE=429      → simulated rate limit
  AI_MODE=mock  MOCK_FAILURE=auth     → simulated auth error
  AI_MODE=mock  MOCK_FAILURE=500      → simulated server error
"""

from __future__ import annotations

import json
import time

from pydantic import BaseModel

from ai.base import AIProvider, AIResponse, AITask, ProviderStatus
from ai.errors import AIProviderError, ErrorCategory


# Deterministic classification responses keyed by keywords in the prompt
_MOCK_CLASSIFICATIONS = {
    "invoice": "invoice",
    "contract": "contract",
    "agreement": "contract",
    "medical": "medical_report",
    "patient": "medical_report",
    "pathology": "medical_report",
    "financial": "financial_statement",
    "income": "financial_statement",
    "revenue": "financial_statement",
    "balance sheet": "financial_statement",
}


class MockProvider(AIProvider):
    """Deterministic mock for unit tests and local development."""

    def __init__(
        self,
        failure_mode: str | None = None,
        latency_ms: float = 5.0,
    ):
        self._failure_mode = failure_mode
        self._latency_ms = latency_ms
        self._call_count = 0

    @property
    def name(self) -> str:
        return "mock"

    @property
    def display_name(self) -> str:
        return "Mock Provider"

    @property
    def model(self) -> str:
        return "mock-v1"

    @property
    def supported_tasks(self) -> list[AITask]:
        return [
            AITask.DOCUMENT_CLASSIFICATION,
            AITask.STRUCTURED_EXTRACTION,
            AITask.GENERAL_QUERY,
            AITask.SUMMARIZATION,
        ]

    def is_available(self) -> bool:
        return True

    def get_status(self) -> ProviderStatus:
        return ProviderStatus.AVAILABLE

    def generate(
        self,
        prompt: str,
        system_instruction: str = "",
        task: AITask = AITask.GENERAL_QUERY,
        correlation_id: str | None = None,
    ) -> AIResponse:
        self._maybe_fail()
        self._call_count += 1

        request_id = self._make_request_id()

        if task == AITask.DOCUMENT_CLASSIFICATION:
            text = self._mock_classification(prompt)
        else:
            text = f"Mock response for: {prompt[:50]}..."

        return AIResponse(
            text=text,
            provider=self.name,
            model=self.model,
            task=task,
            latency_ms=self._latency_ms,
            request_id=request_id,
            correlation_id=correlation_id,
        )

    def parse(
        self,
        prompt: str,
        schema: type[BaseModel],
        system_instruction: str = "",
        task: AITask = AITask.STRUCTURED_EXTRACTION,
        correlation_id: str | None = None,
    ) -> AIResponse:
        self._call_count += 1
        self._maybe_fail()

        request_id = self._make_request_id()
        
        if task == AITask.DOCUMENT_CLASSIFICATION:
            text = self._mock_classification(prompt)
        else:
            mock_data = self._build_mock_schema_data(schema, prompt)
            text = json.dumps(mock_data)

        # Validate our own mock data — if this fails, the mock is broken
        schema.model_validate_json(text)

        return AIResponse(
            text=text,
            provider=self.name,
            model=self.model,
            task=task,
            latency_ms=self._latency_ms,
            request_id=request_id,
        )

    # -- Internal --

    def _maybe_fail(self) -> None:
        """Inject failure if configured."""
        if not self._failure_mode:
            return

        mode = self._failure_mode.lower()
        if mode == "timeout":
            raise AIProviderError(
                "Simulated timeout",
                provider=self.name,
                category=ErrorCategory.TIMEOUT,
            )
        elif mode == "429" or mode == "rate_limit":
            raise AIProviderError(
                "Simulated rate limit",
                provider=self.name,
                category=ErrorCategory.RATE_LIMITED,
            )
        elif mode == "auth":
            raise AIProviderError(
                "Simulated auth error",
                provider=self.name,
                category=ErrorCategory.AUTH_ERROR,
            )
        elif mode == "500" or mode == "server":
            raise AIProviderError(
                "Simulated server error",
                provider=self.name,
                category=ErrorCategory.SERVER_ERROR,
            )
        elif mode == "invalid_json":
            # This will fail Pydantic validation in the router
            raise AIProviderError(
                "Simulated invalid response",
                provider=self.name,
                category=ErrorCategory.INVALID_RESPONSE,
            )

    def _mock_classification(self, prompt: str) -> str:
        """Deterministic classification based on keywords."""
        prompt_lower = prompt.lower()
        doc_type = "unknown"
        for keyword, dtype in _MOCK_CLASSIFICATIONS.items():
            if keyword in prompt_lower:
                doc_type = dtype
                break
        return json.dumps({"document_type": doc_type})

    def _build_mock_schema_data(
        self, schema: type[BaseModel], prompt: str
    ) -> dict:
        """Build plausible mock data that matches the Pydantic schema.

        Walks the schema fields and generates deterministic values
        by type. Not perfect — but good enough for testing.
        """
        data = {}
        schema_info = schema.model_json_schema()
        properties = schema_info.get("properties", {})
        required = set(schema_info.get("required", []))

        for field_name, field_info in properties.items():
            field_type = field_info.get("type", "string")
            field_format = field_info.get("format", "")

            if field_name not in required and "default" in field_info:
                # Skip optional fields with defaults
                continue

            # Resolve $ref if present
            if "$ref" in field_info:
                ref_name = field_info["$ref"].split("/")[-1]
                defs = schema_info.get("$defs", {})
                if ref_name in defs:
                    field_info = defs[ref_name]

            # If it's an enum, pick the first value
            if "enum" in field_info:
                data[field_name] = field_info["enum"][0]
                continue

            field_type = field_info.get("type", "string")
            field_format = field_info.get("format", "")

            if field_type == "string":
                if field_format == "date":
                    data[field_name] = "2026-01-15"
                else:
                    data[field_name] = f"mock_{field_name}"
            elif field_type == "number" or field_type == "integer":
                data[field_name] = 100.0
            elif field_type == "boolean":
                data[field_name] = True
            elif field_type == "array":
                items = field_info.get("items", {})
                if "$ref" in items:
                    # Nested model — build a simple instance
                    ref_name = items["$ref"].split("/")[-1]
                    defs = schema_info.get("$defs", {})
                    if ref_name in defs:
                        nested = self._build_nested_mock(defs[ref_name], defs)
                        data[field_name] = [nested]
                    else:
                        data[field_name] = ["mock_item"]
                else:
                    data[field_name] = ["mock_item"]
            elif field_type == "object":
                data[field_name] = {}
            else:
                data[field_name] = f"mock_{field_name}"

        return data

    def _build_nested_mock(self, schema_def: dict, all_defs: dict) -> dict:
        """Build mock data for a nested Pydantic model."""
        data = {}
        props = schema_def.get("properties", {})
        required = set(schema_def.get("required", []))

        for name, info in props.items():
            if name not in required and "default" in info:
                continue

            # Resolve $ref if present
            if "$ref" in info:
                ref_name = info["$ref"].split("/")[-1]
                if ref_name in all_defs:
                    info = all_defs[ref_name]

            # If it's an enum, pick the first value
            if "enum" in info:
                data[name] = info["enum"][0]
                continue

            ftype = info.get("type", "string")
            fmt = info.get("format", "")

            if ftype == "string":
                if fmt == "date":
                    data[name] = "2026-01-15"
                else:
                    data[name] = f"mock_{name}"
            elif ftype in ("number", "integer"):
                data[name] = 1.0
            elif ftype == "boolean":
                data[name] = True
            elif ftype == "array":
                data[name] = []
            else:
                data[name] = f"mock_{name}"

        return data

    @property
    def call_count(self) -> int:
        return self._call_count

    def reset(self) -> None:
        self._call_count = 0
