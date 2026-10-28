"""Domain models and data contracts for ScamLens-AI.

Based on requirements in README.md:
- Multimodal submission formats (Text, Screenshot, URL, QR, Context)
- Four defined assessment verdicts
- Calibrated 0-100 risk score
- Evidence items with category, severity, and grounding provenance
- Actionable recommendations (preventative & post-harm)
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional


class VerdictEnum(str, Enum):
    """Assessment categories defined in README §6.A."""

    LIKELY_SCAM = "Likely scam"
    SUSPICIOUS = "Suspicious — further verification needed"
    INSUFFICIENT_EVIDENCE = "Insufficient evidence"
    NO_CLEAR_INDICATORS = "No clear scam indicators found"


class SeverityLevel(str, Enum):
    """Severity or weight of a detected indicator."""

    INFO = "INFO"
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class EvidenceCategory(str, Enum):
    """Types of evidence indicators (README §4 & §6)."""

    TEXT_CLAIM = "TEXT_CLAIM"
    URL_DOMAIN = "URL_DOMAIN"
    QR_CODE = "QR_CODE"
    PAYMENT_UPI = "PAYMENT_UPI"
    IMPERSONATION = "IMPERSONATION"
    EXTERNAL_INTEL = "EXTERNAL_INTEL"
    CONTRADICTION = "CONTRADICTION"
    PRIVACY_LEAK = "PRIVACY_LEAK"


class IncidentStage(str, Enum):
    """User journey stage (README §5.F & §6.D)."""

    PRE_ACTION = "PRE_ACTION"  # User has not clicked / transferred money
    POST_ACTION = "POST_ACTION"  # Harm may have occurred; requires urgent mitigation


@dataclass
class EvidenceItem:
    """An individual verified finding, indicator, or observation."""

    category: EvidenceCategory
    severity: SeverityLevel
    summary: str
    details: str = ""
    is_verified: bool = False
    source: str = "internal_analysis"  # e.g., 'ocr', 'whois', 'virustotal', 'rbi_advisory'
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "category": self.category.value if isinstance(self.category, Enum) else self.category,
            "severity": self.severity.value if isinstance(self.severity, Enum) else self.severity,
            "summary": self.summary,
            "details": self.details,
            "is_verified": self.is_verified,
            "source": self.source,
            "metadata": self.metadata,
        }


@dataclass
class InvestigationSubmission:
    """Unified user submission across multiple multimodal inputs (README §4 Obj 1)."""

    text: Optional[str] = None
    image_paths: List[str] = field(default_factory=list)
    urls: List[str] = field(default_factory=list)
    qr_payloads: List[str] = field(default_factory=list)
    context_description: Optional[str] = None
    incident_stage: IncidentStage = IncidentStage.PRE_ACTION
    user_region: str = "IN"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "text": self.text,
            "image_paths": self.image_paths,
            "urls": self.urls,
            "qr_payloads": self.qr_payloads,
            "context_description": self.context_description,
            "incident_stage": (
                self.incident_stage.value
                if isinstance(self.incident_stage, Enum)
                else self.incident_stage
            ),
            "user_region": self.user_region,
        }


@dataclass
class InvestigationResult:
    """Complete explainable investigation output (README §6)."""

    verdict: VerdictEnum
    risk_score: int  # 0 to 100
    confidence: float  # 0.0 to 1.0 (estimated reliability)
    summary: str
    evidence_findings: List[EvidenceItem] = field(default_factory=list)
    uncertainties: List[str] = field(default_factory=list)
    recommended_actions: List[str] = field(default_factory=list)
    provenance: List[Dict[str, Any]] = field(default_factory=list)
    disclaimer: str = (
        "ScamLens AI provides decision-support analysis based on available evidence, "
        "not a legal or cybersecurity guarantee. Never share passwords, OTPs, or PINs."
    )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "verdict": self.verdict.value if isinstance(self.verdict, Enum) else self.verdict,
            "risk_score": self.risk_score,
            "confidence": self.confidence,
            "summary": self.summary,
            "evidence_findings": [item.to_dict() for item in self.evidence_findings],
            "uncertainties": self.uncertainties,
            "recommended_actions": self.recommended_actions,
            "provenance": self.provenance,
            "disclaimer": self.disclaimer,
        }

