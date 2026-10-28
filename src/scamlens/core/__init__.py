"""Core configuration, domain models, and utilities for ScamLens-AI."""

from scamlens.core.config import get_settings
from scamlens.core.models import (
    EvidenceCategory,
    EvidenceItem,
    IncidentStage,
    InvestigationResult,
    InvestigationSubmission,
    SeverityLevel,
    VerdictEnum,
)

__all__ = [
    "get_settings",
    "EvidenceCategory",
    "EvidenceItem",
    "IncidentStage",
    "InvestigationResult",
    "InvestigationSubmission",
    "SeverityLevel",
    "VerdictEnum",
]

