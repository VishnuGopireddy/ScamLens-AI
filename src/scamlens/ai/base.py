"""Abstract Base Class for LLM / Multimodal Providers."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional


class BaseLLMClient(ABC):
    """Interface contract for LLM providers (Groq, Gemini, OpenAI)."""

    @abstractmethod
    def generate_text(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.2,
    ) -> str:
        """Generate response text from LLM."""

    @abstractmethod
    def generate_json(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.1,
    ) -> Dict[str, Any]:
        """Generate structured JSON response."""

    @abstractmethod
    def analyze_image(
        self,
        image_path: str,
        prompt: str,
        system_prompt: Optional[str] = None,
    ) -> str:
        """Perform multimodal analysis on an image/screenshot."""

