"""
AI provider error hierarchy.

Errors are split into retryable (worth trying another provider or retrying)
and non-retryable (the request itself is bad — no point retrying).

WHY this separation matters:
- A 429 from Grok means "try Gemini" — retryable
- A schema error means "fix the code" — never retry
- A 401 means "key is bad" — don't retry THIS provider, but try another
"""

from enum import Enum


class ErrorCategory(str, Enum):
    """Classifies the root cause so the router can decide what to do."""

    RATE_LIMITED = "rate_limited"
    TIMEOUT = "timeout"
    SERVER_ERROR = "server_error"
    NETWORK_ERROR = "network_error"
    AUTH_ERROR = "auth_error"
    INVALID_REQUEST = "invalid_request"
    INVALID_RESPONSE = "invalid_response"
    MODEL_ERROR = "model_error"
    UNKNOWN = "unknown"


# Which categories are worth trying a different provider for
RETRYABLE_CATEGORIES = {
    ErrorCategory.RATE_LIMITED,
    ErrorCategory.TIMEOUT,
    ErrorCategory.SERVER_ERROR,
    ErrorCategory.NETWORK_ERROR,
}

# Which categories mean "this specific provider is broken, try others"
PROVIDER_BROKEN_CATEGORIES = {
    ErrorCategory.AUTH_ERROR,
}

# Which categories mean "the request is bad, don't retry anywhere"
NON_RETRYABLE_CATEGORIES = {
    ErrorCategory.INVALID_REQUEST,
    ErrorCategory.INVALID_RESPONSE,
    ErrorCategory.MODEL_ERROR,
}


class AIProviderError(Exception):
    """Base error for all AI provider failures."""

    def __init__(
        self,
        message: str,
        provider: str = "unknown",
        category: ErrorCategory = ErrorCategory.UNKNOWN,
        status_code: int | None = None,
        original_error: Exception | None = None,
    ):
        self.provider = provider
        self.category = category
        self.status_code = status_code
        self.original_error = original_error
        # Never include raw API details in the message — they may contain secrets
        super().__init__(f"[{provider}] {message}")

    @property
    def is_retryable(self) -> bool:
        return self.category in RETRYABLE_CATEGORIES

    @property
    def should_try_other_provider(self) -> bool:
        return self.category in (RETRYABLE_CATEGORIES | PROVIDER_BROKEN_CATEGORIES)


class AIRouterError(Exception):
    """All providers failed for a given request."""

    def __init__(self, message: str, errors: list[AIProviderError] | None = None):
        self.errors = errors or []
        super().__init__(message)
