"""Health and readiness checks."""

from typing import Any, Dict
from scamlens import __version__
from scamlens.core.config import get_settings


def health_check() -> Dict[str, Any]:
    """Return system status and version info."""
    settings = get_settings()
    return {
        "status": "healthy",
        "service": "scamlens-ai",
        "version": __version__,
        "environment": settings.app_env,
        "mock_intelligence": settings.use_mock_intelligence,
    }

