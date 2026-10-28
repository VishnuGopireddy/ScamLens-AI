"""Text indicator extractor for SMS, WhatsApp, and promotional messages.

Aligns with README §4 Objective 2 & §5 Use Case A & D.
"""

from __future__ import annotations

import re
from typing import List

from scamlens.core.models import EvidenceCategory, EvidenceItem, SeverityLevel

_URGENCY_KEYWORDS = [
    "immediately", "within 24 hours", "account blocked", "account suspended",
    "last warning", "expire today", "urgent action required", "electricity power cut"
]

_CREDENTIAL_KEYWORDS = [
    "otp", "pin", "password", "netbanking password", "cvv", "card details",
    "complete your kyc", "pan update", "aadhaar update"
]

_PRIZE_OFFER_KEYWORDS = [
    "congratulations you won", "lottery", "cashback prize", "claim reward",
    "guaranteed return", "daily work from home salary", "telegram task"
]


def extract_text_indicators(text: str) -> List[EvidenceItem]:
    """Scan message text for scam patterns, deceptive urgency, and credential harvesting."""
    findings: List[EvidenceItem] = []
    if not text:
        return findings

    text_lower = text.lower()

    # 1. Artificial Urgency
    matched_urgency = [w for w in _URGENCY_KEYWORDS if w in text_lower]
    if matched_urgency:
        findings.append(
            EvidenceItem(
                category=EvidenceCategory.TEXT_CLAIM,
                severity=SeverityLevel.HIGH if len(matched_urgency) > 1 else SeverityLevel.MEDIUM,
                summary="Artificial urgency detected",
                details=f"Message uses coercive urgency phrases: {', '.join(matched_urgency)}",
                source="text_heuristic",
            )
        )

    # 2. Credential or KYC demands
    matched_credentials = [w for w in _CREDENTIAL_KEYWORDS if w in text_lower]
    if matched_credentials:
        findings.append(
            EvidenceItem(
                category=EvidenceCategory.TEXT_CLAIM,
                severity=SeverityLevel.HIGH,
                summary="Sensitive credential or KYC request",
                details=f"Message solicits verification or credentials: {', '.join(matched_credentials)}",
                source="text_heuristic",
            )
        )

    # 3. Prize / Unrealistic Job / Task Scam
    matched_offers = [w for w in _PRIZE_OFFER_KEYWORDS if w in text_lower]
    if matched_offers:
        findings.append(
            EvidenceItem(
                category=EvidenceCategory.TEXT_CLAIM,
                severity=SeverityLevel.HIGH,
                summary="Unsolicited prize, reward, or easy job claim",
                details=f"Message contains typical fraudulent offer phrases: {', '.join(matched_offers)}",
                source="text_heuristic",
            )
        )

    return findings

