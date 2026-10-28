"""Custom exceptions for ScamLens-AI."""


class ScamLensError(Exception):
    """Base exception for all ScamLens errors."""


class ConfigurationError(ScamLensError):
    """Raised when application configuration or environment is invalid."""


class ExtractorError(ScamLensError):
    """Raised when evidence extraction fails from text, image, QR, or URL."""


class IntelligenceError(ScamLensError):
    """Raised when external verification / threat intelligence query fails."""


class ModelInferenceError(ScamLensError):
    """Raised when an AI reasoning or multimodal model invocation fails."""


class ValidationError(ScamLensError):
    """Raised when submission input fails validation or exceeds safety thresholds."""

