"""Investigation engine orchestrator.

Coordinates evidence extraction, threat intelligence, RAG verification,
risk scoring, and actionable recommendations.
"""

from __future__ import annotations

import time
from typing import Any, Dict, List

from scamlens.ai.factory import get_ai_client
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
from scamlens.extractors.privacy import redact_pii
from scamlens.extractors.qr import analyze_qr_payload
from scamlens.extractors.text import extract_text_indicators
from scamlens.extractors.url import analyze_url, extract_urls
from scamlens.extractors.vision import extract_from_image
from scamlens.intelligence.client import ThreatIntelligenceClient
from scamlens.investigator.recommend import generate_recommendations
from scamlens.investigator.scorer import calculate_risk_and_verdict
from scamlens.rag.knowledge_base import RegionalKnowledgeBase


class ScamInvestigator:
    """Core multi-evidence scam investigation orchestrator."""

    def __init__(self):
        self.settings = get_settings()
        self.rag = RegionalKnowledgeBase()
        self.intel = ThreatIntelligenceClient(use_mock=self.settings.use_mock_intelligence)
        self.ai = get_ai_client()

    def investigate(self, submission: InvestigationSubmission) -> InvestigationResult:
        """Run an end-to-end multi-evidence investigation."""
        start_time = time.time()
        findings: List[EvidenceItem] = []
        provenance: List[Dict[str, Any]] = []

        raw_text = submission.text or ""
        cleaned_text = raw_text

        # 1. Privacy & PII sanitization (README §4 Obj 7)
        if self.settings.enable_pii_redaction and raw_text:
            cleaned_text, redact_count = redact_pii(raw_text)
            if redact_count > 0:
                findings.append(
                    EvidenceItem(
                        category=EvidenceCategory.PRIVACY_LEAK,
                        severity=SeverityLevel.LOW,
                        summary=f"Sanitized {redact_count} sensitive fields (OTP/Phone/Secret) from submission",
                        source="privacy_guard",
                    )
                )

        # 2. Post-action harm stage recognition (README §5 Use Case F)
        if submission.incident_stage == IncidentStage.POST_ACTION:
            findings.append(
                EvidenceItem(
                    category=EvidenceCategory.TEXT_CLAIM,
                    severity=SeverityLevel.CRITICAL,
                    summary="Incident in post-action harm stage",
                    details="User reports financial transfer, clicked malicious link, or disclosed credentials.",
                    is_verified=True,
                    source="incident_stage_tracker",
                )
            )

        # 3. Text indicator analysis
        if cleaned_text:
            text_findings = extract_text_indicators(cleaned_text)
            findings.extend(text_findings)

        # 3. URL extraction and analysis
        detected_urls = list(submission.urls)
        if cleaned_text:
            detected_urls.extend(extract_urls(cleaned_text))
        detected_urls = list(dict.fromkeys(detected_urls))

        for url in detected_urls:
            url_findings = analyze_url(url)
            findings.extend(url_findings)

            # Query Threat Intelligence
            intel_findings = self.intel.check_url_reputation(url)
            findings.extend(intel_findings)

            provenance.append({
                "target": url,
                "service": "threat_intelligence",
                "retrieved_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            })

        # 4. QR Code payload analysis
        for qr in submission.qr_payloads:
            qr_findings = analyze_qr_payload(qr)
            findings.extend(qr_findings)

        # 5. Multimodal screenshot & image analysis (README §4 Obj 1)
        for img_path in submission.image_paths:
            img_findings = extract_from_image(img_path, self.ai)
            findings.extend(img_findings)
            provenance.append({
                "target": img_path,
                "service": f"multimodal_vision_{self.settings.default_ai_provider}",
                "retrieved_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            })

        # 6. Determine whether meaningful input was analyzed
        has_content = bool(cleaned_text.strip() or detected_urls or submission.qr_payloads or submission.image_paths)

        # 7. Score risk and determine verdict
        risk_score, confidence, verdict, uncertainties = calculate_risk_and_verdict(findings, has_content)

        # 8. Generate actionable recommendations
        helpline = self.rag.get_national_cybercrime_helpline()
        recommendations = generate_recommendations(verdict, submission.incident_stage, helpline)

        # 9. Compose summary
        summary = (
            f"Investigation assessment: {verdict.value} with estimated risk score {risk_score}/100. "
            f"Evaluated {len(findings)} indicator(s) across submitted evidence."
        )

        return InvestigationResult(
            verdict=verdict,
            risk_score=risk_score,
            confidence=confidence,
            summary=summary,
            evidence_findings=findings,
            uncertainties=uncertainties,
            recommended_actions=recommendations,
            provenance=provenance,
        )
