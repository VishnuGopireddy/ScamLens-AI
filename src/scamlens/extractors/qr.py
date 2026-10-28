"""QR code payload decoder and analysis extractor.

Aligns with README §4 Objective 1 & §5 Use Case C:
"A payment QR code must not be classified as fraudulent solely because it requests payment;
the recipient, claim and surrounding evidence matter."
"""

from __future__ import annotations

from typing import List
from urllib.parse import parse_qs, urlparse

from scamlens.core.models import EvidenceCategory, EvidenceItem, SeverityLevel
from scamlens.extractors.url import analyze_url


def analyze_qr_payload(payload: str) -> List[EvidenceItem]:
    """Inspect decoded QR string content (UPI payment URI, Web URL, or generic text)."""
    findings: List[EvidenceItem] = []
    if not payload:
        return findings

    payload_clean = payload.strip()

    # 1. UPI Payment URI check (upi://pay?pa=...&pn=...&am=...)
    if payload_clean.lower().startswith("upi://pay"):
        try:
            parsed = urlparse(payload_clean)
            params = parse_qs(parsed.query)
            payee_vpa = params.get("pa", ["unknown"])[0]
            payee_name = params.get("pn", ["unknown"])[0]
            amount = params.get("am", [None])[0]

            details = f"Payee VPA: {payee_vpa}, Name: {payee_name}"
            if amount:
                details += f", Pre-filled Amount: INR {amount}"

            findings.append(
                EvidenceItem(
                    category=EvidenceCategory.PAYMENT_UPI,
                    severity=SeverityLevel.INFO,
                    summary="UPI Payment QR Code detected",
                    details=details,
                    is_verified=True,
                    source="upi_qr_decoder",
                    metadata={"vpa": payee_vpa, "name": payee_name, "amount": amount},
                )
            )
        except Exception:
            findings.append(
                EvidenceItem(
                    category=EvidenceCategory.QR_CODE,
                    severity=SeverityLevel.MEDIUM,
                    summary="Malformed UPI payment payload",
                    details=f"QR contains invalid UPI parameters: {payload_clean[:50]}...",
                    source="upi_qr_decoder",
                )
            )
        return findings

    # 2. Web URL in QR code
    if payload_clean.lower().startswith(("http://", "https://")):
        findings.append(
            EvidenceItem(
                category=EvidenceCategory.QR_CODE,
                severity=SeverityLevel.INFO,
                summary="URL embedded in QR Code",
                details=f"Target URL: {payload_clean}",
                is_verified=True,
                source="qr_decoder",
            )
        )
        # Deep inspect the URL
        url_findings = analyze_url(payload_clean)
        findings.extend(url_findings)
        return findings

    # 3. Plain text / unrecognized QR format
    findings.append(
        EvidenceItem(
            category=EvidenceCategory.QR_CODE,
            severity=SeverityLevel.INFO,
            summary="Text / Data payload in QR Code",
            details=f"Payload preview: {payload_clean[:60]}",
            source="qr_decoder",
        )
    )
    return findings

