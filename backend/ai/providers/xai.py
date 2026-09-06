"""xAI / Grok provider — OpenAI-compatible endpoint."""

from ai.base import AITask
from ai.providers.openai_compat import OpenAICompatibleProvider


class XAIProvider(OpenAICompatibleProvider):
    _provider_name = "xai"
    _provider_display_name = "xAI Grok"
    _base_url = "https://api.x.ai/v1"
    _default_model = "grok-3-mini"
    _provider_supported_tasks = [
        AITask.DOCUMENT_CLASSIFICATION,
        AITask.STRUCTURED_EXTRACTION,
        AITask.GENERAL_QUERY,
        AITask.SUMMARIZATION,
    ]
