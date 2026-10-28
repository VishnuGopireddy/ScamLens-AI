"""Actionable recommendation generator.

Aligns with README §4 Objective 5 & §5 Use Case F (Harm mitigation).
Distinguishes preventative actions from emergency post-harm steps.
"""

from __future__ import annotations

from typing import List

from scamlens.core.models import IncidentStage, VerdictEnum


def generate_recommendations(
    verdict: VerdictEnum,
    stage: IncidentStage,
    national_helpline: str = "1930",
) -> List[str]:
    """Generate prioritized, actionable advice for the user based on stage and verdict."""
    recommendations: List[str] = []

    # Post-harm emergency response (README §4 Obj 5 & §5 Use Case F)
    if stage == IncidentStage.POST_ACTION:
        recommendations.append(
            f"URGENT: Immediately contact your bank or call the national cybercrime helpline ({national_helpline}) to freeze transactions."
        )
        recommendations.append(
            "Immediately change your banking, email, and social media passwords from a clean device."
        )
        recommendations.append(
            "File an official complaint on https://cybercrime.gov.in with all transaction UTR numbers and screenshots."
        )
        recommendations.append(
            "Preserve all evidence: keep original SMS/WhatsApp chat logs, transaction receipts, and phone numbers without deleting them."
        )
        return recommendations

    # Preventative guidance based on verdict
    if verdict == VerdictEnum.LIKELY_SCAM:
        recommendations.append("Do NOT click any links, download attachments, or scan QR codes provided in the message.")
        recommendations.append("Never share OTPs, UPI PINs, netbanking passwords, or personal documents (PAN/Aadhaar).")
        recommendations.append("Block the sender and report the contact on your messaging platform.")
        recommendations.append("If this claims to be your bank or service provider, contact them only through their verified official app or website.")

    elif verdict == VerdictEnum.SUSPICIOUS:
        recommendations.append("Pause before taking any action. Legitimate organizations do not demand urgent compliance under threat of account closure.")
        recommendations.append("Verify the claim independently by opening your official bank application or dialing their verified customer support.")
        recommendations.append("Avoid providing sensitive information or payment until verified.")

    elif verdict == VerdictEnum.INSUFFICIENT_EVIDENCE:
        recommendations.append("Please provide additional context, such as full message text, screenshot, or link URL for a more conclusive check.")
        recommendations.append("Always exercise caution if the sender asks for personal or financial information.")

    else:  # NO_CLEAR_INDICATORS
        recommendations.append("No immediate fraud signatures were matched, but remain vigilant.")
        recommendations.append("Remember: Scanning a QR code or entering your UPI PIN is only for sending money, never for receiving money.")
        recommendations.append("Ensure the URL domain in your browser address bar matches the official organization before logging in.")

    return recommendations

