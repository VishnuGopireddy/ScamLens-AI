"""Vision and screenshot extractor.

Aligns with README §4 Objective 1 & §7 Scope:
Extracts text, sender badges, and visual evidence from message screenshots.
"""

from __future__ import annotations

from pathlib import Path
from typing import List, Optional

from scamlens.ai.base import BaseLLMClient
from scamlens.ai.factory import get_ai_client
from scamlens.core.models import EvidenceCategory, EvidenceItem, SeverityLevel


def extract_from_image(
    image_path: str,
    ai_client: Optional[BaseLLMClient] = None,
) -> List[EvidenceItem]:
    """Extract textual and visual indicators from a screenshot image using multimodal vision."""
    findings: List[EvidenceItem] = []
    if not image_path:
        return findings

    path = Path(image_path)
    if not path.is_file():
        findings.append(
            EvidenceItem(
                category=EvidenceCategory.TEXT_CLAIM,
                severity=SeverityLevel.LOW,
                summary="Screenshot file not found",
                details=f"Could not locate image file at: {image_path}",
                source="vision_extractor",
            )
        )
        return findings

    client = ai_client or get_ai_client()
    try:
        vision_prompt = (
            "Analyze this screenshot of a message, email, or offer. "
            "Extract: 1) Any claimed brand/organization, 2) Links/URLs or phone numbers, "
            "3) Signs of artificial urgency or suspicious requests for OTP, PIN, KYC, or money. "
            "Provide a concise bulleted summary."
        )
        analysis = client.analyze_image(str(path), prompt=vision_prompt)
        findings.append(
            EvidenceItem(
                category=EvidenceCategory.TEXT_CLAIM,
                severity=SeverityLevel.INFO,
                summary="Multimodal screenshot visual analysis completed",
                details=analysis[:300] + ("..." if len(analysis) > 300 else ""),
                source="vision_multimodal_groq",
                metadata={"full_analysis": analysis},
            )
        )
    except Exception as exc:
        findings.append(
            EvidenceItem(
                category=EvidenceCategory.TEXT_CLAIM,
                severity=SeverityLevel.INFO,
                summary="Screenshot registered (offline / heuristic fallback)",
                details=f"Image path: {image_path}. (Vision inference status: {exc})",
                source="vision_extractor",
            )
        )

    return findings

