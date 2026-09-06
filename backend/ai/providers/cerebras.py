"""Cerebras provider — OpenAI-compatible endpoint with fast inference."""

from ai.base import AITask
from ai.providers.openai_compat import OpenAICompatibleProvider


class CerebrasProvider(OpenAICompatibleProvider):
    _provider_name = "cerebras"
    _provider_display_name = "Cerebras"
    _base_url = "https://api.cerebras.ai/v1"
    _default_model = "llama-3.3-70b"
    _provider_supported_tasks = [
        AITask.DOCUMENT_CLASSIFICATION,
        AITask.STRUCTURED_EXTRACTION,
        AITask.GENERAL_QUERY,
        AITask.SUMMARIZATION,
    ]
