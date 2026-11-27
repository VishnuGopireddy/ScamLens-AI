"""Standard OpenAI-compatible tool specifications and execution dispatcher for ScamLens-AI.

These tools are compatible with OpenAI, Groq, Ollama, vLLM, and Gemini's OpenAI endpoint.
"""

from __future__ import annotations

import json
from email.utils import parseaddr
from typing import Any, Callable, Dict, List, Optional, Tuple

from scamlens.core.config import get_settings
from scamlens.core.models import EvidenceCategory, EvidenceItem, SeverityLevel
from scamlens.extractors.email import EmailMessage, extract_email_evidence
from scamlens.extractors.qr import analyze_qr_payload
from scamlens.extractors.text import extract_contact_indicators, extract_text_indicators
from scamlens.extractors.url import analyze_url
from scamlens.intelligence.client import ThreatIntelligenceClient
from scamlens.rag.knowledge_base import RegionalKnowledgeBase

# ------------------------------------------------------------------------------
# 1. OpenAI-style Tool Definitions (Standard JSON Schema)
# ------------------------------------------------------------------------------

SCAMLENS_TOOLS: List[Dict[str, Any]] = [
    {
        "type": "function",
        "function": {
            "name": "analyze_url_structure",
            "description": "Inspects a URL for deceptive patterns, suspicious TLDs, IP hosts, and brand impersonation.",
            "parameters": {
                "type": "object",
                "properties": {
                    "url": {
                        "type": "string",
                        "description": "The full suspicious URL (e.g. 'http://sbi-fake-login.xyz/update')",
                    }
                },
                "required": ["url"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "check_threat_intelligence",
            "description": "Checks reputation lists (VirusTotal, Google Safe Browsing) for known malicious records.",
            "parameters": {
                "type": "object",
                "properties": {
                    "url": {
                        "type": "string",
                        "description": "The URL to query against threat databases.",
                    }
                },
                "required": ["url"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "verify_brand_official_domain",
            "description": "Verifies whether a domain matches official records for trusted Indian banks or government services.",
            "parameters": {
                "type": "object",
                "properties": {
                    "brand": {
                        "type": "string",
                        "description": "Brand or bank name (e.g., 'sbi', 'hdfc', 'icici', 'indiapost')",
                    },
                    "domain": {
                        "type": "string",
                        "description": "Domain name observed in the message or link (e.g., 'sbi-update.xyz')",
                    },
                },
                "required": ["brand", "domain"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "decode_qr_payment",
            "description": "Decodes and inspects a QR payload string, identifying UPI payee VPA, name, and requested amount.",
            "parameters": {
                "type": "object",
                "properties": {
                    "qr_payload": {
                        "type": "string",
                        "description": "Decoded QR string starting with 'upi://pay...' or web link",
                    }
                },
                "required": ["qr_payload"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "inspect_domain_whois_age",
            "description": "Inspects domain registration date, age, and registrar via ICANN RDAP. Critical for detecting newly registered domains (<30 days old) impersonating brands.",
            "parameters": {
                "type": "object",
                "properties": {
                    "domain_or_url": {
                        "type": "string",
                        "description": "Domain name or full URL to inspect (e.g., 'sbi-fake.xyz' or 'http://sbi-fake.xyz/login')",
                    }
                },
                "required": ["domain_or_url"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "check_virustotal_reputation",
            "description": "Queries VirusTotal API v3 for multi-engine antivirus and phishing consensus across 70+ security vendors.",
            "parameters": {
                "type": "object",
                "properties": {
                    "url": {
                        "type": "string",
                        "description": "The URL to query against VirusTotal threat engines.",
                    }
                },
                "required": ["url"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "extract_text_indicators",
            "description": "Extracts indicators of artificial urgency, coercive threats, pressure tactics, and credential requests from message text.",
            "parameters": {
                "type": "object",
                "properties": {
                    "text": {
                        "type": "string",
                        "description": "The suspicious message body, SMS, or email text.",
                    }
                },
                "required": ["text"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "inspect_email_authentication",
            "description": "Forensically inspects email headers for SPF, DKIM, DMARC authentication status, sender domain impersonation, and Reply-To mismatch.",
            "parameters": {
                "type": "object",
                "properties": {
                    "from_addr": {
                        "type": "string",
                        "description": "The sender header (e.g., 'HDFC Bank <alert@hdfc-pan-update.online>')",
                    },
                    "reply_to": {
                        "type": "string",
                        "description": "The Reply-To header if present",
                    },
                    "spf": {
                        "type": "string",
                        "description": "SPF status ('pass', 'fail', 'softfail', 'none')",
                    },
                    "dkim": {
                        "type": "string",
                        "description": "DKIM verification status ('pass', 'fail', 'none')",
                    },
                    "dmarc": {
                        "type": "string",
                        "description": "DMARC policy status ('pass', 'fail', 'none')",
                    },
                },
                "required": ["from_addr"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "inspect_contact_details",
            "description": "Inspects contact phone numbers and support emails in the message for fraudulent, unverified, or personal mobile numbers posing as official customer service.",
            "parameters": {
                "type": "object",
                "properties": {
                    "text": {
                        "type": "string",
                        "description": "The message text containing contact details, footer, or signature block.",
                    },
                    "claimed_brand": {
                        "type": "string",
                        "description": "The brand or bank claimed by the sender (e.g. 'HDFC Bank', 'SBI').",
                    },
                },
                "required": ["text"],
            },
        },
    },
]

# ------------------------------------------------------------------------------
# 2. Tool Execution Dispatcher
# ------------------------------------------------------------------------------


class ToolDispatcher:
    """Executes OpenAI-format tool calls against local extractors, intel, and RAG."""

    def __init__(self, use_mock: Optional[bool] = None):
        self.rag = RegionalKnowledgeBase()
        resolved_mock = (
            use_mock if use_mock is not None else get_settings().use_mock_intelligence
        )
        self.intel = ThreatIntelligenceClient(use_mock=resolved_mock)

    def _dispatch_with_evidence(
        self, tool_name: str, arguments: Dict[str, Any]
    ) -> Tuple[Dict[str, Any], List[EvidenceItem]]:
        """Execute a tool and return both its JSON payload and typed EvidenceItems."""
        if tool_name == "analyze_url_structure":
            url = arguments.get("url", "")
            findings = analyze_url(url)
            return {"url": url, "findings": [f.to_dict() for f in findings]}, findings

        if tool_name == "check_threat_intelligence":
            url = arguments.get("url", "")
            findings = self.intel.check_url_reputation(url)
            return {"url": url, "intel_findings": [f.to_dict() for f in findings]}, findings

        if tool_name == "verify_brand_official_domain":
            brand = arguments.get("brand", "")
            domain = arguments.get("domain", "")
            is_official = self.rag.verify_domain_against_brand(brand, domain)
            helpline = self.rag.get_national_cybercrime_helpline()
            findings: List[EvidenceItem] = []
            if is_official is False:
                findings.append(
                    EvidenceItem(
                        category=EvidenceCategory.IMPERSONATION,
                        severity=SeverityLevel.HIGH,
                        summary=f"Domain '{domain}' does not match official records for '{brand}'",
                        details=(
                            f"Observed domain '{domain}' is not listed among official domains for "
                            f"'{brand}' in the verified institutional registry."
                        ),
                        is_verified=True,
                        source="brand_registry",
                    )
                )
            elif is_official is True:
                findings.append(
                    EvidenceItem(
                        category=EvidenceCategory.IMPERSONATION,
                        severity=SeverityLevel.INFO,
                        summary=f"Verified official domain '{domain}' for '{brand}'",
                        is_verified=True,
                        source="brand_registry",
                    )
                )
            return {
                "brand": brand,
                "domain": domain,
                "is_official": is_official,
                "cybercrime_helpline": helpline,
            }, findings

        if tool_name == "decode_qr_payment":
            payload = arguments.get("qr_payload", "")
            findings = analyze_qr_payload(payload)
            return {"payload": payload, "findings": [f.to_dict() for f in findings]}, findings

        if tool_name == "inspect_domain_whois_age":
            target = arguments.get("domain_or_url", "")
            findings = self.intel.inspect_domain_whois_rdap(target)
            return {"domain_or_url": target, "findings": [f.to_dict() for f in findings]}, findings

        if tool_name == "check_virustotal_reputation":
            url = arguments.get("url", "")
            findings = self.intel.check_virustotal_reputation(url)
            return {"url": url, "virustotal_findings": [f.to_dict() for f in findings]}, findings

        if tool_name == "extract_text_indicators":
            text = arguments.get("text", "")
            findings = extract_text_indicators(text)
            return {
                "text": text,
                "findings": [f.to_dict() for f in findings],
                "has_urgency": any(
                    "urgency" in f.summary.lower() or "deadline" in f.summary.lower()
                    for f in findings
                ),
            }, findings

        if tool_name == "inspect_email_authentication":
            from_addr = arguments.get("from_addr", "")
            reply_to = arguments.get("reply_to", "")
            spf = arguments.get("spf", "unknown")
            dkim = arguments.get("dkim", "unknown")
            dmarc = arguments.get("dmarc", "unknown")

            display_name, sender_email = parseaddr(from_addr)
            sender_domain = sender_email.split("@")[-1].lower() if "@" in sender_email else ""
            reply_to_email = parseaddr(reply_to)[1] if reply_to else ""

            msg = EmailMessage(
                id="tool_inspect",
                thread_id="tool_inspect",
                sender=from_addr,
                sender_name=display_name,
                sender_email=sender_email,
                sender_domain=sender_domain,
                reply_to=reply_to,
                reply_to_email=reply_to_email or None,
                spf_status=spf.lower() if spf else "unknown",
                dkim_status=dkim.lower() if dkim else "unknown",
                dmarc_status=dmarc.lower() if dmarc else "unknown",
            )
            findings = extract_email_evidence(msg)
            return {
                "from_addr": from_addr,
                "sender_domain": sender_domain,
                "spf_status": spf,
                "dkim_status": dkim,
                "dmarc_status": dmarc,
                "auth_findings": [f.to_dict() for f in findings],
            }, findings

        if tool_name == "inspect_contact_details":
            text = arguments.get("text", "")
            claimed_brand = arguments.get("claimed_brand", "")
            findings = extract_contact_indicators(text, claimed_brand=claimed_brand)
            return {
                "claimed_brand": claimed_brand,
                "contact_findings": [f.to_dict() for f in findings],
            }, findings

        return {"error": f"Tool '{tool_name}' not recognized."}, []

    def execute_tool_with_evidence(
        self, tool_name: str, arguments: Dict[str, Any]
    ) -> Tuple[Dict[str, Any], List[EvidenceItem]]:
        """Dispatch tool call and return (serializable result dict, EvidenceItem list)."""
        return self._dispatch_with_evidence(tool_name, arguments)

    def execute_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Dispatch tool call by name and return serializable result dictionary."""
        result, _ = self._dispatch_with_evidence(tool_name, arguments)
        return result

