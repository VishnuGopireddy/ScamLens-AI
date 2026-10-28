"""Threat intelligence verification client.

Aligns with README §4 Objective 3 & §6.E:
Maintains provenance, avoids declaring sites safe solely due to lack of records,
and provides simulated offline mocks for development and testing.
"""

from __future__ import annotations

from typing import Any, Dict, List

from scamlens.core.config import get_settings
from scamlens.core.models import EvidenceCategory, EvidenceItem, SeverityLevel


class ThreatIntelligenceClient:
    """Interface for external threat intelligence checks (VirusTotal, Safe Browsing, WHOIS)."""

    def __init__(self, use_mock: bool = True):
        self.use_mock = use_mock
        self.settings = get_settings()

    def check_url_reputation(self, url: str) -> List[EvidenceItem]:
        """Query reputation databases for known malicious URLs."""
        findings: List[EvidenceItem] = []
        if not url:
            return findings

        # In mock or offline mode, run deterministic checks
        if self.use_mock or self.settings.use_mock_intelligence:
            url_lower = url.lower()
            if any(term in url_lower for term in ["phish", "scam", "malware", "free-cash", "apk-download"]):
                findings.append(
                    EvidenceItem(
                        category=EvidenceCategory.EXTERNAL_INTEL,
                        severity=SeverityLevel.CRITICAL,
                        summary="Threat Intelligence: Malicious URL match (Simulated)",
                        details=f"URL '{url}' matches known malicious indicators in threat database.",
                        is_verified=True,
                        source="threat_intel_mock",
                    )
                )
            else:
                # Crucial requirement from README §6.A & §8:
                # Absence of known malicious record DOES NOT guarantee legitimacy
                findings.append(
                    EvidenceItem(
                        category=EvidenceCategory.EXTERNAL_INTEL,
                        severity=SeverityLevel.INFO,
                        summary="No threat records in public lists",
                        details="No malicious detections recorded in queried databases. This does not confirm the site is safe.",
                        is_verified=False,
                        source="threat_intel_mock",
                    )
                )
        return findings

