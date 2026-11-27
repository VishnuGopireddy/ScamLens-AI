"""Investigation engine orchestrator.

Coordinates evidence extraction, threat intelligence, RAG verification,
Phase 1 parallel tool orchestration, risk scoring, and actionable recommendations.
"""

from __future__ import annotations

import logging
import time
from typing import Any, Callable, Dict, List, Optional
from urllib.parse import urlparse

from scamlens.ai.factory import get_ai_client
from scamlens.ai.prompts import load_tool_prompts
from scamlens.ai.tools import SCAMLENS_TOOLS, ToolDispatcher
from scamlens.core.config import get_settings
from scamlens.core.exceptions import ModelInferenceError
from scamlens.core.models import (
    EvidenceCategory,
    EvidenceItem,
    IncidentStage,
    InvestigationResult,
    InvestigationSubmission,
    SeverityLevel,
)
from scamlens.extractors.email import EmailMessage, extract_email_evidence
from scamlens.extractors.privacy import redact_pii
from scamlens.extractors.qr import analyze_qr_payload
from scamlens.extractors.text import extract_contact_indicators, extract_text_indicators
from scamlens.extractors.url import analyze_url, extract_urls
from scamlens.extractors.vision import extract_from_image
from scamlens.intelligence.client import ThreatIntelligenceClient
from scamlens.investigator.recommend import generate_recommendations
from scamlens.investigator.scorer import calculate_risk_and_verdict
from scamlens.rag.knowledge_base import RegionalKnowledgeBase

logger = logging.getLogger(__name__)

SUPPORTED_STRATEGIES = ("linear", "orchestrator")


def _deduplicate_evidence(items: List[EvidenceItem]) -> List[EvidenceItem]:
    """Preserve order while removing duplicate evidence findings before scoring."""
    seen = set()
    unique: List[EvidenceItem] = []
    for item in items:
        cat = item.category.value if hasattr(item.category, "value") else str(item.category)
        key = (cat, item.source, item.summary)
        if key not in seen:
            seen.add(key)
            unique.append(item)
    return unique


ProgressCallback = Optional[Callable[[Dict[str, Any]], None]]


class ScamInvestigator:
    """Core multi-evidence scam investigation orchestrator."""

    def __init__(self):
        self.settings = get_settings()
        self.rag = RegionalKnowledgeBase()
        self.intel = ThreatIntelligenceClient(use_mock=self.settings.use_mock_intelligence)
        self.ai = get_ai_client()
        self.tool_dispatcher = ToolDispatcher(use_mock=self.settings.use_mock_intelligence)

    def _emit(
        self,
        on_progress: ProgressCallback,
        stage: str,
        message: str,
        detail: Optional[str] = None,
        data: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Emit a structured live progress event if a callback is supplied."""
        if on_progress is None:
            return
        payload: Dict[str, Any] = {
            "stage": stage,
            "message": message,
            "timestamp": time.strftime("%H:%M:%S"),
        }
        if detail:
            payload["detail"] = detail
        if data is not None:
            payload["data"] = data
        try:
            on_progress(payload)
        except Exception as exc:
            logger.debug("Progress callback error ignored: %s", exc)

    def investigate_email(
        self,
        email_msg: EmailMessage,
        incident_stage: IncidentStage = IncidentStage.PRE_ACTION,
        strategy: str = "linear",
        on_progress: ProgressCallback = None,
    ) -> InvestigationResult:
        """Run an end-to-end multi-evidence investigation on a parsed email."""
        self._validate_strategy(strategy)
        self._emit(
            on_progress,
            "email_forensics",
            f"Inspecting email headers & authentication: '{email_msg.subject}'",
            detail=(
                f"From: {email_msg.sender or email_msg.sender_email} | "
                f"SPF={email_msg.spf_status.upper()}, DKIM={email_msg.dkim_status.upper()}, "
                f"DMARC={email_msg.dmarc_status.upper()} | "
                f"{len(email_msg.extracted_urls)} URL(s), {len(email_msg.attachments)} attachment(s)"
            ),
            data={
                "email_id": email_msg.id,
                "subject": email_msg.subject,
                "sender": email_msg.sender,
                "spf": email_msg.spf_status,
                "dkim": email_msg.dkim_status,
                "dmarc": email_msg.dmarc_status,
                "urls": email_msg.extracted_urls,
            },
        )
        submission = email_msg.to_submission(incident_stage=incident_stage)
        email_evidence = extract_email_evidence(email_msg)
        self._emit(
            on_progress,
            "email_forensics_done",
            f"Email header forensics found {len(email_evidence)} indicator(s)",
            detail="; ".join(item.summary for item in email_evidence) if email_evidence else "No header spoofing or dangerous attachments flagged.",
        )
        if strategy == "orchestrator":
            return self._investigate_orchestrator(
                submission,
                extra_evidence=email_evidence,
                email_msg=email_msg,
                on_progress=on_progress,
            )
        return self._investigate_linear(
            submission,
            extra_evidence=email_evidence,
            on_progress=on_progress,
        )

    def investigate(
        self,
        submission: InvestigationSubmission,
        extra_evidence: Optional[List[EvidenceItem]] = None,
        strategy: str = "linear",
        on_progress: ProgressCallback = None,
    ) -> InvestigationResult:
        """Run an end-to-end multi-evidence investigation using the selected strategy."""
        self._validate_strategy(strategy)
        if strategy == "orchestrator":
            return self._investigate_orchestrator(
                submission, extra_evidence=extra_evidence, on_progress=on_progress
            )
        return self._investigate_linear(
            submission, extra_evidence=extra_evidence, on_progress=on_progress
        )

    def _validate_strategy(self, strategy: str) -> None:
        if strategy not in SUPPORTED_STRATEGIES:
            raise ValueError(
                f"Unsupported investigation strategy '{strategy}'. "
                f"Choose from: {', '.join(SUPPORTED_STRATEGIES)}."
            )

    def _run_common_pre_checks(
        self,
        submission: InvestigationSubmission,
        extra_evidence: Optional[List[EvidenceItem]] = None,
        on_progress: ProgressCallback = None,
    ) -> tuple[str, List[str], List[EvidenceItem], List[Dict[str, Any]]]:
        """Run PII redaction, contact heuristics, post-action checks, URL extraction, and vision."""
        findings: List[EvidenceItem] = []
        provenance: List[Dict[str, Any]] = []

        if extra_evidence:
            findings.extend(extra_evidence)

        raw_text = submission.text or ""
        cleaned_text = raw_text

        # Inspect contact channels locally prior to PII masking so mobile helpline numbers stay visible
        if raw_text:
            self._emit(
                on_progress,
                "contact_check",
                "Checking contact channels, phone numbers & support emails...",
            )
            contact_findings = extract_contact_indicators(raw_text)
            findings.extend(contact_findings)
            self._emit(
                on_progress,
                "contact_check_done",
                f"Contact channel check found {len(contact_findings)} indicator(s)",
                detail="; ".join(f.summary for f in contact_findings)
                if contact_findings
                else "No fraudulent mobile helplines or spoofed support emails detected.",
            )

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
            self._emit(
                on_progress,
                "privacy_guard",
                (
                    f"Privacy Guard sanitized {redact_count} sensitive field(s) (OTP/Phone/Card/Secret)"
                    if redact_count > 0
                    else "Privacy Guard verified input (no raw OTP/card secrets detected)"
                ),
            )

        # 2. Post-action harm stage recognition (README §5 Use Case F)
        if submission.incident_stage == IncidentStage.POST_ACTION:
            self._emit(
                on_progress,
                "incident_stage",
                "Post-Action harm stage active — prioritizing emergency containment guidance",
            )
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

        # 3. URL extraction
        detected_urls = list(submission.urls)
        if cleaned_text:
            detected_urls.extend(extract_urls(cleaned_text))
        detected_urls = list(dict.fromkeys(detected_urls))
        if detected_urls:
            self._emit(
                on_progress,
                "urls_extracted",
                f"Extracted {len(detected_urls)} unique URL(s) to inspect",
                detail=", ".join(detected_urls[:5]) + ("..." if len(detected_urls) > 5 else ""),
                data={"urls": detected_urls},
            )

        # 4. Multimodal screenshot & image analysis (README §4 Obj 1)
        for idx, img_path in enumerate(submission.image_paths, 1):
            vision_model = getattr(self.ai, "vision_model", getattr(self.ai, "model", "default"))
            self._emit(
                on_progress,
                "analyzing_image",
                f"[LLM VISION] {self.settings.default_ai_provider}/{vision_model} — Analyzing screenshot {idx}/{len(submission.image_paths)}...",
                detail=str(img_path),
                data={
                    "provider": self.settings.default_ai_provider,
                    "model": vision_model,
                    "llm_call": True,
                },
            )
            t_vis0 = time.perf_counter()
            img_findings = extract_from_image(img_path, self.ai)
            vis_ms = round((time.perf_counter() - t_vis0) * 1000.0, 2)
            findings.extend(img_findings)
            self._emit(
                on_progress,
                "image_analyzed",
                f"[LLM VISION] {self.settings.default_ai_provider}/{vision_model} — Screenshot {idx}/{len(submission.image_paths)} analyzed ({len(img_findings)} indicator(s))",
                detail="; ".join(f.summary for f in img_findings) if img_findings else None,
                data={
                    "provider": self.settings.default_ai_provider,
                    "model": vision_model,
                    "latency_ms": vis_ms,
                    "llm_call": True,
                },
            )
            provenance.append({
                "target": img_path,
                "service": f"multimodal_vision_{self.settings.default_ai_provider}",
                "retrieved_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            })

        return cleaned_text, detected_urls, findings, provenance

    def _finalize_result(
        self,
        findings: List[EvidenceItem],
        has_content: bool,
        submission: InvestigationSubmission,
        provenance: List[Dict[str, Any]],
        llm_narrative: Optional[str] = None,
        on_progress: ProgressCallback = None,
    ) -> InvestigationResult:
        """Deduplicate evidence, compute deterministic calibrated score, and build result."""
        unique_findings = _deduplicate_evidence(findings)
        self._emit(
            on_progress,
            "scoring",
            f"Correlating {len(unique_findings)} unique evidence item(s) & computing calibrated risk score...",
        )
        risk_score, confidence, verdict, uncertainties = calculate_risk_and_verdict(
            unique_findings, has_content
        )

        helpline = self.rag.get_national_cybercrime_helpline()
        recommendations = generate_recommendations(verdict, submission.incident_stage, helpline)

        base_summary = (
            f"Investigation assessment: {verdict.value} with estimated risk score {risk_score}/100. "
            f"Evaluated {len(unique_findings)} indicator(s) across submitted evidence."
        )
        summary = f"{base_summary}\n\n{llm_narrative.strip()}" if llm_narrative and llm_narrative.strip() else base_summary

        result = InvestigationResult(
            verdict=verdict,
            risk_score=risk_score,
            confidence=confidence,
            summary=summary,
            evidence_findings=unique_findings,
            uncertainties=uncertainties,
            recommended_actions=recommendations,
            provenance=provenance,
        )
        self._emit(
            on_progress,
            "completed",
            f"Investigation complete — {verdict.value} (Risk Score: {risk_score}/100)",
            data={"verdict": verdict.value, "risk_score": risk_score, "confidence": confidence},
        )
        return result

    def _investigate_linear(
        self,
        submission: InvestigationSubmission,
        extra_evidence: Optional[List[EvidenceItem]] = None,
        on_progress: ProgressCallback = None,
    ) -> InvestigationResult:
        """Deterministic 1-pass linear investigation pipeline."""
        cleaned_text, detected_urls, findings, provenance = self._run_common_pre_checks(
            submission, extra_evidence=extra_evidence, on_progress=on_progress
        )

        if cleaned_text:
            self._emit(
                on_progress,
                "text_analysis",
                "Scanning message text for artificial urgency, KYC/OTP lures & prize scams...",
            )
            text_findings = extract_text_indicators(cleaned_text)
            findings.extend(text_findings)
            self._emit(
                on_progress,
                "text_analysis_done",
                f"Text analysis found {len(text_findings)} indicator(s)",
                detail="; ".join(f.summary for f in text_findings) if text_findings else "No urgency or credential-lure keywords matched.",
            )

        for idx, url in enumerate(detected_urls, 1):
            self._emit(
                on_progress,
                "analyzing_url",
                f"Analyzing URL ({idx}/{len(detected_urls)}): {url}",
                detail="Checking lexical structure, brand impersonation, ICANN RDAP age & VirusTotal reputation...",
                data={"url": url, "index": idx, "total": len(detected_urls)},
            )
            url_findings = analyze_url(url)
            intel_findings = self.intel.check_url_reputation(url)
            findings.extend(url_findings)
            findings.extend(intel_findings)
            provenance.append({
                "target": url,
                "service": "threat_intelligence",
                "retrieved_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            })
            all_url_items = url_findings + intel_findings
            self._emit(
                on_progress,
                "url_analyzed",
                f"URL checked ({idx}/{len(detected_urls)}): {len(all_url_items)} signal(s) for {url}",
                detail="; ".join(f.summary for f in all_url_items) if all_url_items else "No explicit URL/intel flags.",
            )

        for idx, qr in enumerate(submission.qr_payloads, 1):
            self._emit(
                on_progress,
                "analyzing_qr",
                f"Decoding QR / UPI payload ({idx}/{len(submission.qr_payloads)})...",
                detail=qr[:120],
            )
            qr_findings = analyze_qr_payload(qr)
            findings.extend(qr_findings)
            self._emit(
                on_progress,
                "qr_analyzed",
                f"QR / UPI payload ({idx}/{len(submission.qr_payloads)}) checked: {len(qr_findings)} indicator(s)",
                detail="; ".join(f.summary for f in qr_findings) if qr_findings else None,
            )

        has_content = bool(
            cleaned_text.strip() or detected_urls or submission.qr_payloads or submission.image_paths
        )
        return self._finalize_result(
            findings, has_content, submission, provenance, on_progress=on_progress
        )

    def _build_orchestrator_prompt(
        self,
        cleaned_text: str,
        submission: InvestigationSubmission,
        detected_urls: List[str],
        email_msg: Optional[EmailMessage] = None,
    ) -> str:
        """Assemble a PII-sanitized incident briefing for the Phase 1 Orchestrator."""
        sections: List[str] = [
            "Investigate all vectors of this incident simultaneously using the available forensic tools."
        ]
        if email_msg is not None:
            sections.append(
                "EMAIL HEADERS:\n"
                f"From: {email_msg.sender}\n"
                f"Reply-To: {email_msg.reply_to or 'None'}\n"
                f"SPF: {email_msg.spf_status} | DKIM: {email_msg.dkim_status} | DMARC: {email_msg.dmarc_status}"
            )
        if submission.context_description:
            sections.append(f"USER CONTEXT:\n{submission.context_description}")
        if cleaned_text:
            sections.append(f"SANITIZED CONTENT:\n{cleaned_text}")
        if detected_urls:
            # Prioritize distinct hostnames so marketing emails with dozens of identical-host tracking URLs stay concise
            seen_hosts: Dict[str, int] = {}
            prioritized_urls: List[str] = []
            for u in detected_urls:
                host = (urlparse(u).hostname or u).lower()
                count = seen_hosts.get(host, 0)
                if count < 2:
                    prioritized_urls.append(u)
                    seen_hosts[host] = count + 1
                if len(prioritized_urls) >= 12:
                    break
            sections.append("EXTRACTED URLS:\n" + "\n".join(f"- {u}" for u in prioritized_urls))
        if submission.qr_payloads:
            sections.append("QR PAYLOADS:\n" + "\n".join(f"- {q}" for q in submission.qr_payloads))
        return "\n\n".join(sections)

    def _investigate_orchestrator(
        self,
        submission: InvestigationSubmission,
        extra_evidence: Optional[List[EvidenceItem]] = None,
        email_msg: Optional[EmailMessage] = None,
        on_progress: ProgressCallback = None,
    ) -> InvestigationResult:
        """Phase 1: 2-Turn Parallel Fan-Out / Fan-In Tool Orchestrator with linear fallback."""
        cleaned_text, detected_urls, findings, provenance = self._run_common_pre_checks(
            submission, extra_evidence=extra_evidence, on_progress=on_progress
        )
        has_content = bool(
            cleaned_text.strip() or detected_urls or submission.qr_payloads or submission.image_paths
        )

        if not has_content:
            return self._finalize_result(
                findings, has_content, submission, provenance, on_progress=on_progress
            )

        if not hasattr(self.ai, "run_agent_loop"):
            self._emit(
                on_progress,
                "orchestrator_fallback",
                "Configured AI client does not support tool calling; falling back to linear pipeline.",
            )
            provenance.append({
                "strategy": "orchestrator_fallback_to_linear",
                "reason": "Configured AI client does not support tool calling loop.",
            })
            return self._investigate_linear(
                submission, extra_evidence=extra_evidence, on_progress=on_progress
            )

        try:
            self._emit(
                on_progress,
                "orchestrator_start",
                f"Launching Phase 1 AI Orchestrator ({self.settings.default_ai_provider} / {getattr(self.ai, 'model', 'default')})...",
            )
            orchestrator_prompt = load_tool_prompts()["orchestrator"]["system_prompt"]
            incident_prompt = self._build_orchestrator_prompt(
                cleaned_text, submission, detected_urls, email_msg=email_msg
            )
            agent_out = self.ai.run_agent_loop(
                initial_prompt=incident_prompt,
                system_prompt=orchestrator_prompt,
                tools=SCAMLENS_TOOLS,
                dispatcher=self.tool_dispatcher,
                max_turns=2,
                parallel_tools=True,
                on_event=(
                    lambda ev: self._emit(
                        on_progress,
                        ev["stage"],
                        ev["message"],
                        detail=ev.get("detail"),
                        data=ev.get("data"),
                    )
                )
                if on_progress
                else None,
            )
        except ModelInferenceError as exc:
            logger.warning("Phase 1 orchestrator LLM unreachable (%s); falling back to linear pipeline.", exc)
            self._emit(
                on_progress,
                "orchestrator_fallback",
                "AI endpoint unreachable; automatically falling back to deterministic linear pipeline.",
                detail=str(exc),
            )
            fallback = self._investigate_linear(
                submission, extra_evidence=extra_evidence, on_progress=on_progress
            )
            fallback.provenance.append({
                "strategy": "orchestrator_fallback_to_linear",
                "reason": str(exc),
            })
            return fallback

        tool_history = agent_out.get("tool_history", [])
        final_response = agent_out.get("final_response", "") or ""

        # If provider returned offline simulated mock without executing tools, degrade to deterministic checks
        if not tool_history and "[Simulated " in final_response:
            self._emit(
                on_progress,
                "orchestrator_fallback",
                "AI provider running in simulated offline mode; running deterministic linear checks instead.",
            )
            fallback = self._investigate_linear(
                submission, extra_evidence=extra_evidence, on_progress=on_progress
            )
            fallback.provenance.append({
                "strategy": "orchestrator_fallback_to_linear",
                "reason": "AI provider returned simulated offline response with no tool calls.",
            })
            return fallback

        findings.extend(agent_out.get("evidence_items", []))
        for entry in tool_history:
            provenance.append({
                "strategy": "orchestrator_phase1",
                "tool": entry.get("tool"),
                "arguments": entry.get("arguments"),
                "execution_time_ms": entry.get("execution_time_ms"),
                "retrieved_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            })

        return self._finalize_result(
            findings,
            has_content,
            submission,
            provenance,
            llm_narrative=final_response,
            on_progress=on_progress,
        )
