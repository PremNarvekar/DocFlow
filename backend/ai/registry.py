"""
Provider registry — discovers and manages AI providers.

At startup, the registry reads the config, instantiates providers
for every configured API key, and makes them available to the router.

Missing API keys don't crash — they just mean that provider
is unavailable. The router routes around unavailable providers.
"""

from __future__ import annotations

from ai.base import AIProvider, AITask, ProviderInfo, ProviderStatus

# Import provider classes
from ai.providers.gemini import GeminiProvider
from ai.providers.xai import XAIProvider
from ai.providers.groq import GroqProvider
from ai.providers.cerebras import CerebrasProvider
from ai.providers.mistral import MistralProvider
from ai.providers.openrouter import OpenRouterProvider
from ai.mock import MockProvider


# Maps provider name -> provider class + config key names
_PROVIDER_FACTORIES: dict[str, type] = {
    "gemini": GeminiProvider,
    "xai": XAIProvider,
    "groq": GroqProvider,
    "cerebras": CerebrasProvider,
    "mistral": MistralProvider,
    "openrouter": OpenRouterProvider,
}


class ProviderRegistry:
    """Holds all instantiated providers and answers availability queries.

    The registry is the single source of truth for which providers
    exist and what state they're in.
    """

    def __init__(self) -> None:
        self._providers: dict[str, AIProvider] = {}

    def register(self, provider: AIProvider) -> None:
        """Add a provider instance to the registry."""
        self._providers[provider.name] = provider

    def get(self, name: str) -> AIProvider | None:
        """Get a specific provider by name."""
        return self._providers.get(name)

    def get_available(
        self, task: AITask | None = None
    ) -> list[AIProvider]:
        """Return providers that are available, optionally filtered by task."""
        result = []
        for p in self._providers.values():
            if not p.is_available():
                continue
            if task and task not in p.supported_tasks:
                continue
            result.append(p)
        return result

    def get_all_info(self) -> list[ProviderInfo]:
        """Provider status for all registered providers — safe for frontends."""
        infos = []
        for p in self._providers.values():
            info = p.get_info()
            if not p.is_available():
                info.reason = self._unavailable_reason(p)
            infos.append(info)
        return infos

    @property
    def provider_names(self) -> list[str]:
        return list(self._providers.keys())

    @staticmethod
    def _unavailable_reason(provider: AIProvider) -> str:
        status = provider.get_status()
        if status == ProviderStatus.UNAVAILABLE:
            return "API key not configured"
        elif status == ProviderStatus.AUTH_ERROR:
            return "Authentication failed"
        elif status == ProviderStatus.RATE_LIMITED:
            return "Rate limited"
        elif status == ProviderStatus.ERROR:
            return "Provider initialization failed"
        return "Unknown"


def build_registry(
    api_keys: dict[str, str | None],
    model_overrides: dict[str, str | None],
    mock_mode: bool = False,
    mock_failure: str | None = None,
) -> ProviderRegistry:
    """Build a registry from configuration.

    This is the main entry point called at application startup.
    It creates provider instances for every known provider,
    whether the key exists or not — unavailable providers are
    still registered so we can report their status.
    """
    registry = ProviderRegistry()

    if mock_mode:
        registry.register(MockProvider(failure_mode=mock_failure))
        return registry

    for provider_name, provider_cls in _PROVIDER_FACTORIES.items():
        key = api_keys.get(provider_name)
        model = model_overrides.get(provider_name)
        provider = provider_cls(api_key=key, model=model)
        registry.register(provider)

    return registry
