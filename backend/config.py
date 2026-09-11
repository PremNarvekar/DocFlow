"""
Application configuration.

Loads all provider API keys from the environment.
Missing keys do NOT crash the app - they just mean that
provider is unavailable. The router handles the rest.
"""

import os
from pathlib import Path

from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent
load_dotenv(dotenv_path=BASE_DIR / ".env")

GEMINI_API_KEY: str | None = os.getenv("GEMINI_API_KEY")
XAI_API_KEY: str | None = os.getenv("XAI_API_KEY")
GROQ_API_KEY: str | None = os.getenv("GROQ_API_KEY")
CEREBRAS_API_KEY: str | None = os.getenv("CEREBRAS_API_KEY")
MISTRAL_API_KEY: str | None = os.getenv("MISTRAL_API_KEY")
OPENROUTER_API_KEY: str | None = os.getenv("OPENROUTER_API_KEY")
HF_TOKEN: str | None = os.getenv("HF_TOKEN")

GEMINI_MODEL: str | None = os.getenv("GEMINI_MODEL")
XAI_MODEL: str | None = os.getenv("XAI_MODEL")
GROQ_MODEL: str | None = os.getenv("GROQ_MODEL")
CEREBRAS_MODEL: str | None = os.getenv("CEREBRAS_MODEL")
MISTRAL_MODEL: str | None = os.getenv("MISTRAL_MODEL")
OPENROUTER_MODEL: str | None = os.getenv("OPENROUTER_MODEL")
HF_MODEL: str | None = os.getenv("HF_MODEL")

AI_PROVIDER_PRIORITY: str = os.getenv(
    "AI_PROVIDER_PRIORITY",
    "gemini,xai,groq,cerebras,mistral,openrouter",
)

AI_MODE: str = os.getenv("AI_MODE", "live")

PROVIDER_API_KEYS: dict[str, str | None] = {
    "gemini": GEMINI_API_KEY,
    "xai": XAI_API_KEY,
    "groq": GROQ_API_KEY,
    "cerebras": CEREBRAS_API_KEY,
    "mistral": MISTRAL_API_KEY,
    "openrouter": OPENROUTER_API_KEY,
    "huggingface": HF_TOKEN
}

PROVIDER_MODELS: dict[str, str | None] = {
    "gemini": GEMINI_MODEL,
    "xai": XAI_MODEL,
    "groq": GROQ_MODEL,
    "cerebras": CEREBRAS_MODEL,
    "mistral": MISTRAL_MODEL,
    "openrouter": OPENROUTER_MODEL,
    "huggingface": HF_MODEL,
}

DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///./docflow.db")