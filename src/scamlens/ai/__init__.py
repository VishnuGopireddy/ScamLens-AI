"""AI & LLM Provider integrations for ScamLens-AI."""

from scamlens.ai.base import BaseLLMClient
from scamlens.ai.factory import get_ai_client
from scamlens.ai.openai_compat import OpenAICompatibleClient
from scamlens.ai.tools import SCAMLENS_TOOLS, ToolDispatcher

__all__ = [
    "BaseLLMClient",
    "OpenAICompatibleClient",
    "SCAMLENS_TOOLS",
    "ToolDispatcher",
    "get_ai_client",
]
