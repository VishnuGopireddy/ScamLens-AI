"""Prompt template management package for ScamLens-AI."""

from scamlens.ai.prompts.loader import (
    PromptTemplate,
    get_catalog_dir,
    list_available_prompts,
    load_prompt,
    load_tool_prompts,
)

__all__ = [
    "PromptTemplate",
    "load_prompt",
    "load_tool_prompts",
    "list_available_prompts",
    "get_catalog_dir",
]

