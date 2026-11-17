"""YAML Prompt Template Loader and Validator.

Loads structured prompt templates from the catalog, validates required input
variables, and renders OpenAI-compatible messages with optional few-shot examples.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional
import yaml


@dataclass
class PromptTemplate:
    """Represents a structured prompt template loaded from YAML."""

    name: str
    version: str = "1.0.0"
    description: str = ""
    system_prompt: str = ""
    user_template: str = ""
    model_parameters: Dict[str, Any] = field(default_factory=dict)
    input_variables: List[str] = field(default_factory=list)
    few_shot_examples: List[Dict[str, str]] = field(default_factory=list)

    def render_user_prompt(self, **kwargs) -> str:
        """Render the user template with provided variables."""
        missing = [v for v in self.input_variables if v not in kwargs]
        if missing:
            raise ValueError(f"Missing required prompt variable(s) for '{self.name}': {missing}")

        # Safe substitution of declared input_variables to avoid breaking on literal braces in JSON schemas
        rendered = self.user_template
        for var in self.input_variables:
            val = str(kwargs.get(var, ""))
            rendered = rendered.replace(f"{{{var}}}", val)
        return rendered.strip()

    def render_messages(self, **kwargs) -> List[Dict[str, str]]:
        """Render complete OpenAI-compatible messages payload:

        - system message
        - optional few-shot (user / assistant pairs)
        - target user message
        """
        user_content = self.render_user_prompt(**kwargs)
        messages: List[Dict[str, str]] = []

        if self.system_prompt.strip():
            messages.append({"role": "system", "content": self.system_prompt.strip()})

        for ex in self.few_shot_examples:
            inp = ex.get("input", "")
            out = ex.get("output", "")
            if inp:
                messages.append({"role": "user", "content": inp.strip()})
            if out:
                messages.append({"role": "assistant", "content": out.strip()})

        messages.append({"role": "user", "content": user_content})
        return messages


_CATALOG_DIR = Path(__file__).resolve().parent / "catalog"


def get_catalog_dir() -> Path:
    """Return the absolute path to the prompt catalog directory."""
    return _CATALOG_DIR


def list_available_prompts() -> List[str]:
    """Return sorted list of available prompt template names in the catalog."""
    if not _CATALOG_DIR.is_dir():
        return []
    return sorted([p.stem for p in _CATALOG_DIR.glob("*.yaml")])


def load_prompt(name: str) -> PromptTemplate:
    """Load a PromptTemplate from the catalog directory by stem name or filename."""
    filename = f"{name}.yaml" if not name.endswith(".yaml") else name
    file_path = _CATALOG_DIR / filename

    if not file_path.is_file():
        available = list_available_prompts()
        raise FileNotFoundError(
            f"Prompt template '{name}' not found at {file_path}. Available prompts: {available}"
        )

    with open(file_path, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f) or {}

    return PromptTemplate(
        name=data.get("name", Path(name).stem),
        version=str(data.get("version", "1.0.0")),
        description=data.get("description", ""),
        system_prompt=data.get("system_prompt", ""),
        user_template=data.get("user_template", ""),
        model_parameters=data.get("model_parameters", {}),
        input_variables=data.get("input_variables", []),
        few_shot_examples=data.get("few_shot_examples", []),
    )

