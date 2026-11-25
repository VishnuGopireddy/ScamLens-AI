"""Text indicator extractor for SMS, WhatsApp, and promotional messages.

Aligns with README §4 Objective 2 & §5 Use Case A & D.
"""

from __future__ import annotations

import re
from typing import List

from scamlens.core.models import EvidenceCategory, EvidenceItem, SeverityLevel

_URGENCY_KEYWORDS = [
    "immediately", "within 24 hours", "account blocked", "account suspended",
    "last warning", "expire today", "urgent action required", "electricity power cut",
    "debit freeze", "freeze", "freeze alert", "starting today", "non-compliant",
    "consequences", "penalty", "deadline", "mandatory compliance"
]

_CREDENTIAL_KEYWORDS = [
    "otp", "pin", "password", "netbanking password", "cvv", "card details",
    "complete your kyc", "pan update", "aadhaar update", "customer id",
    "netbanking ipin", "ipin", "pan-aadhaar", "biometric linking", "centralized cbs"
]

_PRIZE_OFFER_KEYWORDS = [
    "congratulations you won", "lottery", "cashback prize", "claim reward",
    "guaranteed return", "daily work from home salary", "telegram task"
]

_PHONE_REGEX = re.compile(r"(?<!\d)(?:\+91[\s-]?)?[6-9]\d{9}(?!\d)")
_EMAIL_REGEX = re.compile(r"[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+")


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


_HEADER_LINE_PREFIXES = ("from:", "to:", "cc:", "reply-to:", "return-path:", "delivered-to:")


def extract_contact_indicators(text: str, claimed_brand: str = "") -> List[EvidenceItem]:
    """Inspect contact phone numbers and support emails for fraudulent or unverified channels."""
    findings: List[EvidenceItem] = []
    if not text:
        return findings

    # Exclude raw email routing headers (From/To/Cc) so recipient addresses are not flagged as support contacts
    body_lines = [
        line for line in text.splitlines()
        if not line.lstrip().lower().startswith(_HEADER_LINE_PREFIXES)
    ]
    scan_text = "\n".join(body_lines)
    scan_lower = scan_text.lower()

    phones = list(dict.fromkeys(_PHONE_REGEX.findall(scan_text)))
    emails = list(dict.fromkeys(_EMAIL_REGEX.findall(scan_text)))

    # 1. Suspicious phone numbers (standard 10-digit mobile posing as bank support)
    bank_keywords = ["bank", "sbi", "hdfc", "icici", "axis", "kotak", "vigilance", "safety line"]
    text_lower_full = text.lower()
    claims_bank = bool(
        claimed_brand
        or any(re.search(rf"\b{re.escape(b)}\b", text_lower_full) for b in bank_keywords)
    )

    flagged_mobile = False
    for phone in phones:
        clean_num = re.sub(r"[^\d]", "", phone)
        if clean_num.startswith("91") and len(clean_num) == 12:
            clean_num = clean_num[2:]
        # Indian standard 10-digit mobile starts with 6-9
        if len(clean_num) == 10 and clean_num[0] in "6789" and claims_bank:
            flagged_mobile = True
            findings.append(
                EvidenceItem(
                    category=EvidenceCategory.IMPERSONATION,
                    severity=SeverityLevel.MEDIUM,
                    summary="Suspicious mobile number as official helpline",
                    details=(
                        f"Contact number '{phone}' appears to be a personal mobile line, "
                        "which is contrary to official bank toll-free 1800 numbers or shortcodes."
                    ),
                    source="contact_heuristic",
                )
            )
            break

    # redact_pii only masks 10-digit Indian mobile numbers ([REDACTED_PHONE]), not 1800 toll-free numbers
    if not flagged_mobile and claims_bank and "[redacted_phone]" in scan_lower:
        if any(cue in scan_lower for cue in ("helpline", "safety line", "customer care", "contact", "officer", "support")):
            findings.append(
                EvidenceItem(
                    category=EvidenceCategory.IMPERSONATION,
                    severity=SeverityLevel.MEDIUM,
                    summary="Suspicious mobile number as official helpline",
                    details=(
                        "Redacted 10-digit mobile number appeared as an institutional support helpline, "
                        "which is contrary to official bank toll-free 1800 numbers or shortcodes."
                    ),
                    source="contact_heuristic",
                )
            )

    # 2. Suspicious contact email addresses
    for email_addr in emails:
        domain = email_addr.split("@")[-1].lower() if "@" in email_addr else ""
        if claims_bank:
            # Check if domain uses suspicious TLD or brand hyphens
            if any(tld in domain for tld in [".online", ".xyz", ".top", ".site", ".live"]) or "-" in domain:
                findings.append(
                    EvidenceItem(
                        category=EvidenceCategory.IMPERSONATION,
                        severity=SeverityLevel.HIGH,
                        summary="Fraudulent contact email domain",
                        details=f"Official contact email '{email_addr}' uses an unverified or high-risk domain '{domain}'.",
                        source="contact_heuristic",
                    )
                )

    return findings
