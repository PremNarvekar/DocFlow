"""Groq provider — OpenAI-compatible endpoint with ultra-fast inference."""

from ai.base import AITask
from ai.providers.openai_compat import OpenAICompatibleProvider


class GroqProvider(OpenAICompatibleProvider):
    _provider_name = "groq"
    _provider_display_name = "Groq"
    _base_url = "https://api.groq.com/openai/v1"
    _default_model = "llama-3.3-70b-versatile"
    _provider_supported_tasks = [
        AITask.DOCUMENT_CLASSIFICATION,
        AITask.STRUCTURED_EXTRACTION,
        AITask.GENERAL_QUERY,
        AITask.SUMMARIZATION,
    ]
