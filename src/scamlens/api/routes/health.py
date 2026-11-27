"""Health and readiness checks."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict

from scamlens import __version__
from scamlens.core.config import get_settings


def health_check() -> Dict[str, Any]:
    """Return system status, AI configuration, and Gmail readiness info."""
    settings = get_settings()
    project_root = Path(__file__).resolve().parents[4]

    cred_path = Path(settings.gmail_credentials_file)
    if not cred_path.is_absolute():
        cred_path = project_root / cred_path

    token_path = Path(settings.gmail_token_file)
    if not token_path.is_absolute():
        token_path = project_root / token_path

    active_model = settings.custom_ai_model
    if settings.default_ai_provider == "groq":
        active_model = settings.groq_model
    elif settings.default_ai_provider == "gemini":
        active_model = settings.gemini_model
    elif settings.default_ai_provider == "openai":
        active_model = settings.openai_model
    elif settings.default_ai_provider == "vllm" and settings.vllm_model:
        active_model = settings.vllm_model

    return {
        "status": "healthy",
        "service": "scamlens-ai",
        "version": __version__,
        "environment": settings.app_env,
        "mock_intelligence": settings.use_mock_intelligence,
        "enable_pii_redaction": settings.enable_pii_redaction,
        "ai_provider": settings.default_ai_provider,
        "ai_model": active_model,
        "gmail_credentials_configured": cred_path.is_file(),
        "gmail_token_present": token_path.is_file(),
    }
