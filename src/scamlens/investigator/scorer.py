"""Calibrated risk scorer and verdict decider.

Aligns with README §6.A (Verdict categories) & §6.B (Risk score).
"""

from __future__ import annotations

from typing import List, Tuple

from scamlens.core.models import EvidenceItem, SeverityLevel, VerdictEnum

# Weight mapping for severity levels
_SEVERITY_WEIGHTS = {
    SeverityLevel.INFO: 0,
    SeverityLevel.LOW: 10,
    SeverityLevel.MEDIUM: 25,
    SeverityLevel.HIGH: 45,
    SeverityLevel.CRITICAL: 80,
}


def calculate_risk_and_verdict(
    evidence_items: List[EvidenceItem],
    has_meaningful_content: bool,
) -> Tuple[int, float, VerdictEnum, List[str]]:
    """Compute 0-100 risk score, confidence rating, verdict, and uncertainties.

    Returns:
        Tuple of (risk_score, confidence, verdict, uncertainties)
    """
    uncertainties: List[str] = []

    if not has_meaningful_content:
        return 0, 0.2, VerdictEnum.INSUFFICIENT_EVIDENCE, [
            "Input is empty or insufficient to perform an investigation."
        ]

    if not evidence_items:
        uncertainties.append(
            "No explicit threat indicators matched our heuristics, but newly formed scams may evade standard checks."
        )
        return 10, 0.6, VerdictEnum.NO_CLEAR_INDICATORS, uncertainties

    raw_score = sum(_SEVERITY_WEIGHTS.get(item.severity, 0) for item in evidence_items)
    # Cap risk score at 100
    risk_score = min(100, raw_score)

    has_critical = any(item.severity == SeverityLevel.CRITICAL for item in evidence_items)
    high_count = sum(1 for item in evidence_items if item.severity == SeverityLevel.HIGH)

    # Determine verdict based on objective thresholds
    if has_critical or risk_score >= 70 or high_count >= 2:
        verdict = VerdictEnum.LIKELY_SCAM
        confidence = 0.85
    elif risk_score >= 35 or high_count == 1:
        verdict = VerdictEnum.SUSPICIOUS
        confidence = 0.70
        uncertainties.append("Some suspicious indicators exist, but conclusive proof requires further channel verification.")
    else:
        verdict = VerdictEnum.NO_CLEAR_INDICATORS
        confidence = 0.65
        uncertainties.append("Absence of known scam signatures does not guarantee complete authenticity.")

    return risk_score, confidence, verdict, uncertainties

