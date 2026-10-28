"""Standard OpenAI-compatible tool specifications and execution dispatcher for ScamLens-AI.

These tools are compatible with OpenAI, Groq, Ollama, vLLM, and Gemini's OpenAI endpoint.
"""

from __future__ import annotations

import json
from typing import Any, Callable, Dict, List

from scamlens.extractors.qr import analyze_qr_payload
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
]

# ------------------------------------------------------------------------------
# 2. Tool Execution Dispatcher
# ------------------------------------------------------------------------------


class ToolDispatcher:
    """Executes OpenAI-format tool calls against local extractors, intel, and RAG."""

    def __init__(self):
        self.rag = RegionalKnowledgeBase()
        self.intel = ThreatIntelligenceClient(use_mock=True)

    def execute_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Dispatch tool call by name and return serializable result dictionary."""
        if tool_name == "analyze_url_structure":
            url = arguments.get("url", "")
            findings = analyze_url(url)
            return {"url": url, "findings": [f.to_dict() for f in findings]}

        if tool_name == "check_threat_intelligence":
            url = arguments.get("url", "")
            findings = self.intel.check_url_reputation(url)
            return {"url": url, "intel_findings": [f.to_dict() for f in findings]}

        if tool_name == "verify_brand_official_domain":
            brand = arguments.get("brand", "")
            domain = arguments.get("domain", "")
            is_official = self.rag.verify_domain_against_brand(brand, domain)
            helpline = self.rag.get_national_cybercrime_helpline()
            return {
                "brand": brand,
                "domain": domain,
                "is_official": is_official,
                "cybercrime_helpline": helpline,
            }

        if tool_name == "decode_qr_payment":
            payload = arguments.get("qr_payload", "")
            findings = analyze_qr_payload(payload)
            return {"payload": payload, "findings": [f.to_dict() for f in findings]}

        return {"error": f"Tool '{tool_name}' not recognized."}

