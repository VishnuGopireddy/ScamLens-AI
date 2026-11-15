"""Configuration manager for ScamLens-AI."""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Optional


def _load_dotenv_simple(env_path: Path) -> None:
    """Lightweight .env file parser that sets os.environ if key is not already set."""
    if not env_path.is_file():
        return
    try:
        try:
            from dotenv import load_dotenv

            load_dotenv(env_path, override=False)
            return
        except ImportError:
            pass

        with open(env_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#") or "=" not in line:
                    continue
                key, val = line.split("=", 1)
                key = key.strip()
                val = val.strip()
                if (val.startswith('"') and val.endswith('"')) or (
                    val.startswith("'") and val.endswith("'")
                ):
                    val = val[1:-1]
                elif "#" in val:
                    val = val.split("#", 1)[0].strip()
                if key and key not in os.environ:
                    os.environ[key] = val
    except (OSError, ValueError):
        pass


# Automatically load from project root .env if found
_PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent
_ENV_FILE = _PROJECT_ROOT / ".env"
_load_dotenv_simple(_ENV_FILE)


@dataclass
class Settings:
    """Application settings loaded from environment variables."""

    app_env: str = os.getenv("APP_ENV", "development")
    debug: bool = os.getenv("DEBUG", "true").lower() in ("1", "true", "yes")
    log_level: str = os.getenv("LOG_LEVEL", "INFO")
    api_host: str = os.getenv("API_HOST", "0.0.0.0")
    api_port: int = int(os.getenv("API_PORT", "8000"))
    secret_key: str = os.getenv("SECRET_KEY", "scamlens-dev-insecure-secret-key-32-bytes-min")

    # Multimodal AI
    default_ai_provider: str = os.getenv("DEFAULT_AI_PROVIDER", "custom")
    groq_api_key: Optional[str] = os.getenv("GROQ_API_KEY")
    groq_model: str = os.getenv("GROQ_MODEL", "openai/gpt-oss-20b")
    groq_vision_model: str = os.getenv("GROQ_VISION_MODEL", "qwen/qwen3.8-27b")
    gemini_api_key: Optional[str] = os.getenv("GEMINI_API_KEY")
    gemini_model: str = os.getenv("GEMINI_MODEL", "gemini-1.5-flash-latest")
    openai_api_key: Optional[str] = os.getenv("OPENAI_API_KEY")
    openai_model: str = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
    anthropic_api_key: Optional[str] = os.getenv("ANTHROPIC_API_KEY")
    anthropic_model: str = os.getenv("ANTHROPIC_MODEL", "claude-3-5-sonnet-20241022")

    # Custom / Self-Hosted OpenAI-Compatible Endpoint (vLLM, Ollama, Private GPU)
    custom_ai_base_url: Optional[str] = os.getenv("CUSTOM_AI_BASE_URL")
    custom_ai_api_key: Optional[str] = os.getenv("CUSTOM_AI_API_KEY")
    custom_ai_model: str = os.getenv("CUSTOM_AI_MODEL", "Qwen/Qwen3-8B")
    custom_ai_vision_model: str = os.getenv("CUSTOM_AI_VISION_MODEL", "Qwen/Qwen3-8B")
    custom_ai_ca_cert: Optional[str] = os.getenv("CUSTOM_AI_CA_CERT")
    custom_ai_insecure_skip_verify: bool = (
        os.getenv("CUSTOM_AI_INSECURE_SKIP_VERIFY", "false").lower() in ("1", "true", "yes")
    )

    # vLLM-specific overrides
    vllm_base_url: Optional[str] = os.getenv("VLLM_BASE_URL")
    vllm_api_key: Optional[str] = os.getenv("VLLM_API_KEY")
    vllm_model: Optional[str] = os.getenv("VLLM_MODEL")
    vllm_ca_cert: Optional[str] = os.getenv("VLLM_CA_CERT")

    # Threat Intelligence
    use_mock_intelligence: bool = (
        os.getenv("USE_MOCK_INTELLIGENCE", "true").lower() in ("1", "true", "yes")
    )
    google_safe_browsing_api_key: Optional[str] = os.getenv("GOOGLE_SAFE_BROWSING_API_KEY")
    virustotal_api_key: Optional[str] = os.getenv("VIRUSTOTAL_API_KEY")
    whoisxml_api_key: Optional[str] = os.getenv("WHOISXML_API_KEY")

    # Privacy & Safety
    enable_pii_redaction: bool = (
        os.getenv("ENABLE_PII_REDACTION", "true").lower() in ("1", "true", "yes")
    )
    max_image_upload_mb: int = int(os.getenv("MAX_IMAGE_UPLOAD_MB", "10"))
    max_text_input_chars: int = int(os.getenv("MAX_TEXT_INPUT_CHARS", "10000"))

    # Regional & Domain defaults
    default_region: str = os.getenv("DEFAULT_REGION", "IN")
    enable_regional_advisories: bool = (
        os.getenv("ENABLE_REGIONAL_ADVISORIES", "true").lower() in ("1", "true", "yes")
    )
    data_dir: Path = Path(os.getenv("DATA_DIR", str(_PROJECT_ROOT / "data")))


_cached_settings: Optional[Settings] = None


def get_settings() -> Settings:
    """Return application settings instance (singleton pattern)."""
    global _cached_settings
    if _cached_settings is None:
        _cached_settings = Settings()
    return _cached_settings

