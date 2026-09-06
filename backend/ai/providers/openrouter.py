"""OpenRouter provider — aggregator, good fallback of last resort."""

from ai.base import AITask
from ai.providers.openai_compat import OpenAICompatibleProvider


class OpenRouterProvider(OpenAICompatibleProvider):
    _provider_name = "openrouter"
    _provider_display_name = "OpenRouter"
    _base_url = "https://openrouter.ai/api/v1"
    _default_model = "meta-llama/llama-3.3-70b-instruct"
    _provider_supported_tasks = [
        AITask.DOCUMENT_CLASSIFICATION,
        AITask.STRUCTURED_EXTRACTION,
        AITask.GENERAL_QUERY,
        AITask.SUMMARIZATION,
    ]
