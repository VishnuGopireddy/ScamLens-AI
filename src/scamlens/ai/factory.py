"""Factory for obtaining configured LLM / multimodal provider clients.

Supports OpenAI-compatible calling style across:
- Groq (https://api.groq.com/openai/v1)
- Ollama (http://localhost:11434/v1)
- vLLM (http://localhost:8000/v1)
- Gemini (https://generativelanguage.googleapis.com/v1beta/openai)
- OpenAI (https://api.openai.com/v1)
"""

from __future__ import annotations

from typing import Optional

from scamlens.ai.base import BaseLLMClient
from scamlens.ai.openai_compat import OpenAICompatibleClient
from scamlens.core.config import get_settings


def get_ai_client(
    provider: Optional[str] = None,
    base_url: Optional[str] = None,
    api_key: Optional[str] = None,
    model: Optional[str] = None,
) -> BaseLLMClient:
    """Return an instance of the configured LLM client.

    All providers share the exact same OpenAI-compatible tool calling format.
    """
    settings = get_settings()
    selected_provider = (provider or settings.default_ai_provider).lower()

    return OpenAICompatibleClient(
        provider=selected_provider,
        base_url=base_url,
        api_key=api_key,
        model=model,
    )
