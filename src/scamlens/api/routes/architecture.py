"""Technical architecture, orchestrator, and 9-tool metadata route handler."""

from __future__ import annotations

from typing import Any, Dict, List

from scamlens.ai.prompts import load_tool_prompts
from scamlens.ai.tools import SCAMLENS_TOOLS
from scamlens.api.routes.health import health_check

_TOOL_IMPL_META: Dict[str, Dict[str, Any]] = {
    "analyze_url_structure": {
        "module": "src/scamlens/extractors/url.py -> analyze_url()",
        "execution": "Local Deterministic (0ms, 0 tokens)",
        "categories": ["URL_DOMAIN", "IMPERSONATION"],
        "checks": [
            "Raw IPv4 hosts in URLs (HIGH)",
            "Disposable / high-abuse TLDs (.xyz, .top, .online, .club, etc.) (MEDIUM)",
            "Brand impersonation with hyphens or excessive subdomains (HIGH)",
            "Unencrypted HTTP protocol (LOW)",
            "Credential harvesting paths (/login, /kyc, /auth, /pan) on risky domains (HIGH)",
        ],
    },
    "check_threat_intelligence": {
        "module": "src/scamlens/intelligence/client.py -> ThreatIntelligenceClient.check_url_reputation()",
        "execution": "External APIs / Mock Fallback (RDAP + VirusTotal v3)",
        "categories": ["EXTERNAL_INTEL"],
        "checks": [
            "Aggregates ICANN RDAP domain registration age + 404 registry check",
            "Aggregates VirusTotal API v3 multi-engine vendor consensus",
            "Enforces Epistemic Humility: 0 detections never proves safety",
        ],
    },
    "verify_brand_official_domain": {
        "module": "src/scamlens/rag/knowledge_base.py -> RegionalKnowledgeBase.verify_domain_against_brand()",
        "execution": "Local RAG Registry (trusted_domains.json)",
        "categories": ["IMPERSONATION"],
        "checks": [
            "Verifies observed domain against official Indian bank & government domains",
            "Supports brand aliases (e.g. 'HDFC Bank' -> 'hdfc', 'State Bank of India' -> 'sbi')",
            "Returns national cybercrime helpline (1930) alongside verification verdict",
        ],
    },
    "decode_qr_payment": {
        "module": "src/scamlens/extractors/qr.py -> analyze_qr_payload()",
        "execution": "Local Deterministic Parser + URL Analyzer",
        "categories": ["PAYMENT_UPI", "QR_CODE", "URL_DOMAIN"],
        "checks": [
            "Extracts UPI payee VPA (pa), payee name (pn), and prefilled amount (am)",
            "Flags malformed upi://pay payloads",
            "Runs analyze_url() when a QR code embeds an HTTP/HTTPS web link",
        ],
    },
    "inspect_domain_whois_age": {
        "module": "src/scamlens/intelligence/client.py -> inspect_domain_whois_rdap()",
        "execution": "ICANN RDAP (https://rdap.org/domain/{apex}) / Simulated Mock",
        "categories": ["EXTERNAL_INTEL"],
        "checks": [
            "Reduces subdomains (e.g. click.grammarly.com) to registrable apex domain before RDAP query",
            "Flags zero-day domains < 30 days old (HIGH) and < 90 days old (MEDIUM)",
            "Flags unregistered/suspended domains returning HTTP 404 (MEDIUM)",
        ],
    },
    "check_virustotal_reputation": {
        "module": "src/scamlens/intelligence/client.py -> check_virustotal_reputation()",
        "execution": "VirusTotal API v3 (/api/v3/urls/{id}) / Simulated Mock",
        "categories": ["EXTERNAL_INTEL"],
        "checks": [
            "Queries 70+ security engines for malicious/suspicious consensus",
            "2+ malicious engines -> CRITICAL; 1 malicious or 2+ suspicious -> MEDIUM",
            "Mock mode inspects hostname/TLD & short path segments while ignoring opaque base64 tokens",
        ],
    },
    "extract_text_indicators": {
        "module": "src/scamlens/extractors/text.py -> extract_text_indicators()",
        "execution": "Local Deterministic NLP Heuristics",
        "categories": ["TEXT_CLAIM"],
        "checks": [
            "Coercive urgency phrases ('within 24 hours', 'debit freeze', 'last warning') (MEDIUM/HIGH)",
            "Credential / KYC harvesting ('otp', 'ipin', 'pan-aadhaar', 'complete your kyc') (HIGH)",
            "Prize, lottery, or easy Telegram/WFH job lures (HIGH)",
        ],
    },
    "inspect_email_authentication": {
        "module": "src/scamlens/extractors/email.py -> extract_email_evidence()",
        "execution": "Local RFC 5322 Header & MIME Forensics",
        "categories": ["IMPERSONATION", "EXTERNAL_INTEL"],
        "checks": [
            "SPF fail/softfail (HIGH), DKIM fail (HIGH), DMARC policy failure (CRITICAL)",
            "Reply-To vs From domain mismatch (HIGH)",
            "Display-name brand spoofing on unverified sender domains (HIGH)",
            "Dangerous executable/macro attachments (.exe, .iso, .xlsm, .docm) (CRITICAL)",
        ],
    },
    "inspect_contact_details": {
        "module": "src/scamlens/extractors/text.py -> extract_contact_indicators()",
        "execution": "Local Pre-Redaction Contact Heuristics",
        "categories": ["IMPERSONATION"],
        "checks": [
            "Runs before PII redaction so personal 10-digit Indian mobile numbers posing as bank helplines are detected",
            "Uses strict digit boundaries so 12-digit UPI ref numbers are not misclassified",
            "Flags support emails on suspicious TLDs (.online, .xyz, .top) or hyphenated lookalike domains",
        ],
    },
}


def get_architecture_details() -> Dict[str, Any]:
    """Return live technical architecture, orchestrator details, and 9-tool schemas."""
    tool_catalog = load_tool_prompts()
    prompt_tools = tool_catalog.get("tools", {})
    orchestrator_cfg = tool_catalog.get("orchestrator", {})

    tools_detail: List[Dict[str, Any]] = []
    for schema in SCAMLENS_TOOLS:
        fn = schema.get("function", {})
        name = fn.get("name", "")
        prompt_meta = prompt_tools.get(name, {})
        impl_meta = _TOOL_IMPL_META.get(name, {})
        tools_detail.append(
            {
                "name": name,
                "description": fn.get("description", ""),
                "parameters": fn.get("parameters", {}),
                "module": impl_meta.get("module", "src/scamlens/ai/tools.py"),
                "execution": impl_meta.get("execution", "ToolDispatcher"),
                "categories": impl_meta.get("categories", []),
                "checks": impl_meta.get("checks", []),
                "guidelines": prompt_meta.get("guidelines", []),
                "synthesis_prompt": prompt_meta.get("synthesis_prompt", ""),
                "few_shot_examples": prompt_meta.get("few_shot_examples", []),
            }
        )

    components: List[Dict[str, Any]] = [
        {
            "id": "orchestrator",
            "step": "03",
            "title": "Phase 1 AI Orchestrator",
            "subtitle": "2-Turn Parallel Fan-Out / Fan-In Tool Loop",
            "badge": "CORE ENGINE",
            "module": "src/scamlens/investigator/engine.py + src/scamlens/ai/openai_compat.py",
            "summary": (
                "Coordinates an LLM reasoning loop over all 9 forensic tools using OpenAI-compatible "
                "tool calling (Groq, Ollama, vLLM, Gemini, OpenAI, or custom HTTPS endpoints)."
            ),
            "highlights": [
                "Turn 1 (Fan-Out): Sends PII-sanitized incident briefing + 9 tool JSON schemas; model emits parallel tool_calls.",
                "Concurrent Execution: OpenAICompatibleClient.run_agent_loop() dispatches tools via ThreadPoolExecutor (up to 8 workers).",
                "Typed Evidence Capture: ToolDispatcher.execute_tool_with_evidence() returns JSON ToolMessages for the LLM AND typed EvidenceItems for deterministic scoring.",
                "Turn 2 (Forced Synthesis): Omits tools (tools=None) on the final turn so the model correlates all tool outputs into a structured forensic narrative.",
                "Resilient Fallback: Automatically falls back to the deterministic linear pipeline on ModelInferenceError or offline simulated mock output.",
            ],
            "details": {
                "max_turns": 2,
                "parallel_tools": True,
                "max_workers": 8,
                "url_prompt_cap": "Up to 12 URLs (max 2 per distinct hostname) in _build_orchestrator_prompt()",
                "fallback_triggers": [
                    "Client lacks run_agent_loop()",
                    "ModelInferenceError (endpoint unreachable / HTTP error)",
                    "Empty tool_history with '[Simulated ...]' offline mock response",
                ],
                "phase2_roadmap": (
                    "Planned in claude/agentic-ai-plan.md: LangGraph Supervisor + Specialized Worker Agents "
                    "(Email, URL, Content, Reputation) + Evaluator-Reflector re-investigation cycle."
                ),
            },
        },
        {
            "id": "tools",
            "step": "04",
            "title": "9-Tool Forensic Arsenal",
            "subtitle": "SCAMLENS_TOOLS & ToolDispatcher",
            "badge": "9 TOOLS",
            "module": "src/scamlens/ai/tools.py + src/scamlens/ai/prompts/catalog/tool_prompts.json",
            "summary": (
                "Standard OpenAI JSON-schema function tools dispatched concurrently against local extractors, "
                "ICANN RDAP, VirusTotal v3, and the RegionalKnowledgeBase."
            ),
            "highlights": [
                "Unified dual-return pattern: execute_tool_with_evidence() returns (serializable_json, List[EvidenceItem]).",
                "Zero score hallucination: Tools emit typed EvidenceItems with verified vs heuristic provenance.",
                "Supports parallel execution across URL structure, WHOIS/RDAP age, VirusTotal, brand registry, QR/UPI, text, email headers, and contact channels.",
            ],
            "details": {
                "tool_names": [t["name"] for t in tools_detail],
            },
        },
        {
            "id": "privacy",
            "step": "01",
            "title": "Ingestion & Privacy Guard",
            "subtitle": "Pre-LLM PII Redaction & Stage Tracking",
            "badge": "PRIVACY BY DESIGN",
            "module": "src/scamlens/extractors/privacy.py + src/scamlens/extractors/text.py",
            "summary": (
                "Sanitizes sensitive user secrets before any text reaches an LLM prompt or orchestrator briefing, "
                "while running local contact-channel heuristics prior to masking."
            ),
            "highlights": [
                "Masks OTPs ([REDACTED_OTP]), passwords/PINs ([REDACTED_SECRET]), 13-16 digit card numbers ([REDACTED_CARD_NUMBER]), and 10-digit Indian mobiles ([REDACTED_PHONE]).",
                "Runs extract_contact_indicators() prior to redaction so scammers' mobile helpline numbers are still flagged.",
                "Tracks PRE_ACTION vs POST_ACTION stage; POST_ACTION adds a CRITICAL indicator for urgent harm containment.",
            ],
            "details": {
                "redacted_fields": ["OTP / Verification Code", "Password / PIN", "13-16 Digit Card", "10-Digit Indian Mobile"],
                "digit_boundary_guard": "Uses (?<!\\d)...(?!\\d) so 12-digit UPI references are never corrupted.",
            },
        },
        {
            "id": "extractors",
            "step": "02",
            "title": "Multimodal Extractors",
            "subtitle": "Email MIME, URL, Text, QR/UPI & Vision",
            "badge": "EXTRACTION",
            "module": "src/scamlens/extractors/{email,url,text,qr,vision}.py",
            "summary": (
                "Parses heterogeneous user inputs—Gmail REST payloads, raw RFC 5322 .eml files, URLs, UPI QR payloads, "
                "and uploaded screenshots—into normalized InvestigationSubmission and EvidenceItem objects."
            ),
            "highlights": [
                "Email Forensics: Parses SPF/DKIM/DMARC, Reply-To mismatch, display-name brand spoofing, HTML anchor links, and attachments.",
                "URL Extractor: Strips trailing angle brackets/punctuation (e.g. <https://...>) and checks TLDs, IP hosts, and credential paths.",
                "QR / UPI Decoder: Extracts pa (VPA), pn (payee name), and am (amount) without assuming payment requests are automatically fraud.",
                "Vision Extractor: Base64-encodes screenshots and calls the configured multimodal vision model.",
            ],
            "details": {
                "supported_email_sources": ["Gmail REST API (GmailReader)", "Local .eml / .json / .md (LocalEmailReader)", "Raw MIME paste/upload"],
            },
        },
        {
            "id": "intel_rag",
            "step": "05",
            "title": "Threat Intel & Brand RAG",
            "subtitle": "ICANN RDAP, VirusTotal v3 & Trusted Registry",
            "badge": "VERIFICATION",
            "module": "src/scamlens/intelligence/client.py + src/scamlens/rag/knowledge_base.py",
            "summary": (
                "Grounds investigation claims in external registry telemetry and authoritative Indian institutional records "
                "while maintaining strict epistemic humility."
            ),
            "highlights": [
                "ICANN RDAP: Normalizes subdomains to apex domains and inspects registration age (<30d HIGH, <90d MEDIUM) & 404 status.",
                "VirusTotal API v3: Multi-engine vendor consensus across 70+ scanners (or deterministic offline mock mode).",
                "RegionalKnowledgeBase: Verifies official bank/gov domains, SMS headers, UPI rules, and helpline 1930.",
            ],
            "details": {
                "trusted_registry_path": "src/scamlens/rag/data/trusted_domains.json",
                "national_helpline": "1930 (https://cybercrime.gov.in)",
            },
        },
        {
            "id": "scorer",
            "step": "06",
            "title": "Deterministic Scorer & Recommender",
            "subtitle": "Calibrated 0-100 Risk Scoring & Stage Guidance",
            "badge": "GUARDRAIL",
            "module": "src/scamlens/investigator/scorer.py + recommend.py",
            "summary": (
                "Deduplicates all EvidenceItems from pre-checks and orchestrator tools, computes an objective 0-100 risk score, "
                "and selects stage-appropriate actions."
            ),
            "highlights": [
                "Severity Weights: INFO=0, LOW=10, MEDIUM=25, HIGH=45, CRITICAL=80 (summed & capped at 100).",
                "Verdict Thresholds: CRITICAL or score >= 70 or >= 2 HIGH -> 'Likely scam'; score >= 35 or 1 HIGH -> 'Suspicious'; empty -> 'Insufficient evidence'.",
                "Deduplication Key: (category, source, summary) prevents double-counting when both pre-checks and orchestrator tools inspect the same signal.",
                "Stage-Aware Actions: POST_ACTION prioritizes calling 1930, freezing bank transactions, changing passwords, and preserving UTR/chat evidence.",
            ],
            "details": {
                "weights": {"INFO": 0, "LOW": 10, "MEDIUM": 25, "HIGH": 45, "CRITICAL": 80},
                "verdicts": [
                    "Likely scam",
                    "Suspicious — further verification needed",
                    "Insufficient evidence",
                    "No clear scam indicators found",
                ],
            },
        },
        {
            "id": "gui_sse",
            "step": "07",
            "title": "Live SSE Streaming & Web GUI",
            "subtitle": "Zero-Dependency HTTP + Server-Sent Events",
            "badge": "INTERFACE",
            "module": "src/GUI/server.py + src/GUI/static/{index.html,app.js,styles.css}",
            "summary": (
                "Streams real-time investigation progress events (reading email, parsed email snapshot, per-URL checks, "
                "orchestrator tool completions, scoring, final verdict) over HTTP SSE."
            ),
            "highlights": [
                "Built on stdlib ThreadingHTTPServer with queue-backed SSE streaming and 15s keepalives.",
                "Mirrors core REST handlers in src/scamlens/api/main.py for FastAPI compatibility.",
                "Supports single multimodal investigations, raw .eml / local dataset / live Gmail triage, and live batch inbox scans.",
            ],
            "details": {
                "sse_endpoints": [
                    "POST /api/v1/investigate/stream",
                    "POST /api/v1/investigate/email/stream",
                    "POST /api/v1/emails/scan/stream",
                ],
            },
        },
    ]

    return {
        "runtime": health_check(),
        "orchestrator": {
            "strategy": "orchestrator",
            "fallback_strategy": "linear",
            "max_turns": 2,
            "parallel_tools": True,
            "max_workers": 8,
            "system_prompt": orchestrator_cfg.get("system_prompt", ""),
            "synthesis_prompt": orchestrator_cfg.get("synthesis_prompt", ""),
        },
        "tools": tools_detail,
        "components": components,
    }
