# ScamLens-AI Technical Architecture & Implementation Reference

This document describes the **implemented** architecture, execution pipelines, forensic tools, threat-intelligence integrations, Gmail ingestion/polling, and CLI/Web GUI internals of **ScamLens-AI**.

---

## 1. Module Map

| Layer | File | Primary Responsibility |
| :--- | :--- | :--- |
| **Core Models & Config** | `src/scamlens/core/models.py` | `@dataclass` contracts: `InvestigationSubmission`, `EvidenceItem`, `InvestigationResult`, `IncidentStage`, `SeverityLevel`, `VerdictEnum` |
| | `src/scamlens/core/config.py` | `Settings`, `get_settings()`, `clear_settings_cache()` (`.env` loader) |
| **Orchestrator Engine** | `src/scamlens/investigator/engine.py` | `ScamInvestigator` (Phase 1 `orchestrator` strategy, pre-checks, offline deterministic fallback, deduplication, live progress events) |
| **Scoring & Guidance** | `src/scamlens/investigator/scorer.py` | `calculate_risk_and_verdict()` (deterministic `0–100` scoring & verdict thresholds) |
| | `src/scamlens/investigator/recommend.py` | `generate_recommendations()` (`PRE_ACTION` vs `POST_ACTION` emergency response) |
| **AI & Tool Calling** | `src/scamlens/ai/openai_compat.py` | `OpenAICompatibleClient` (`/chat/completions`, `run_agent_loop()`, parallel tool execution, vision) |
| | `src/scamlens/ai/tools.py` | `SCAMLENS_TOOLS` (9 OpenAI JSON schemas) & `ToolDispatcher` |
| | `src/scamlens/ai/prompts/` | Prompt catalog (`tool_prompts.json`, YAML templates, `loader.py`) |
| **Extractors** | `src/scamlens/extractors/email.py` | `GmailAuthManager`, `GmailReader`, `LocalEmailReader`, `parse_gmail_message`, `parse_raw_email`, `extract_email_evidence` |
| | `src/scamlens/extractors/privacy.py` | `redact_pii()` (OTPs, secrets, cards, Indian mobile numbers) |
| | `src/scamlens/extractors/text.py` | `extract_text_indicators()`, `extract_contact_indicators()` |
| | `src/scamlens/extractors/url.py` | `extract_urls()`, `analyze_url()` |
| | `src/scamlens/extractors/qr.py` | `analyze_qr_payload()` (UPI `upi://pay` & embedded URLs) |
| | `src/scamlens/extractors/vision.py` | `extract_from_image()` (multimodal screenshot inspection) |
| **Threat Intel & RAG** | `src/scamlens/intelligence/client.py` | `ThreatIntelligenceClient` (WhoisXML, ICANN RDAP, VirusTotal v3, simulated mock) |
| | `src/scamlens/rag/knowledge_base.py` | `RegionalKnowledgeBase` (`trusted_domains.json`, helpline `1930`) |
| **API, GUI & CLI** | `src/GUI/server.py` | Zero-dependency `ThreadingHTTPServer` + SSE streaming & cache/Gmail routes |
| | `src/GUI/static/` | `index.html`, `styles.css`, `app.js` (4-tab UI, 60s Gmail polling, live feed) |
| | `src/scamlens/api/routes/` | `investigate.py`, `emails.py`, `health.py`, `architecture.py` |
| | `scripts/scan_gmail.py` | Gmail CLI scanner with `--v` live terminal renderer (`src/scamlens/cli_live.py`) |

---

## 2. Investigation Engine (`ScamInvestigator`)

All investigations enter `ScamInvestigator.investigate()` or `ScamInvestigator.investigate_email()` in `src/scamlens/investigator/engine.py` and execute via the Phase 1 **`orchestrator`** strategy (`SUPPORTED_STRATEGIES = ("orchestrator",)`).

### 2.1 Shared Entry: Pre-Checks (`_run_common_pre_checks`)
Every investigation runs these deterministic steps in order before launching the orchestrator:
1. **Email Header Forensics** (for `investigate_email`): `extract_email_evidence(email_msg)` inspects `SPF`, `DKIM`, `DMARC`, `Reply-To` mismatch, display-name brand spoofing, and dangerous attachments.
2. **Pre-Redaction Contact Check**: `extract_contact_indicators(raw_text)` runs *before* PII masking so 10-digit Indian mobile numbers posing as bank helplines are still detectable.
3. **Privacy Guard**: When `settings.enable_pii_redaction` is `True`, `redact_pii(raw_text)` replaces OTPs (`[REDACTED_OTP]`), passwords/PINs (`[REDACTED_SECRET]`), 13–16 digit card numbers (`[REDACTED_CARD_NUMBER]`), and Indian mobile numbers (`[REDACTED_PHONE]`), logging a `LOW` `PRIVACY_LEAK` item if redactions occurred.
4. **Post-Action Stage Check**: If `incident_stage == IncidentStage.POST_ACTION`, adds a `CRITICAL` verified item from `incident_stage_tracker`.
5. **URL Extraction**: Combines explicit `submission.urls` with `extract_urls(cleaned_text)` and deduplicates while preserving order.
6. **Multimodal Vision**: For each `submission.image_paths` entry, calls `extract_from_image(img_path, self.ai)` using `vision_model`.

### 2.2 Phase 1 `orchestrator` (`_investigate_orchestrator`)
A **2-turn parallel Fan-Out / Fan-In** agentic loop (`max_turns=2`, `parallel_tools=True`) implemented in `OpenAICompatibleClient.run_agent_loop()`:

```text
Pre-Checks (Email Forensics, Contact Check, Privacy Guard, URL Extract, Vision)
   │
   ▼  _build_orchestrator_prompt(): headers + context + PII-redacted text + <=12 distinct-host URLs + QR
   │
┌──────────────────────────────────────────────────────────────────────────────┐
│ Turn 1 (Fan-Out): POST /chat/completions with 9 SCAMLENS_TOOLS schemas       │
│   └─► Model emits tool_calls[]                                               │
│                                                                              │
│ Concurrent Execution: ThreadPoolExecutor (max 8 workers)                     │
│   └─► ToolDispatcher._dispatch_with_evidence() via as_completed()            │
│       Returns BOTH:                                                          │
│       1. JSON payload -> role="tool" message for LLM Turn 2                  │
│       2. Typed EvidenceItem[] -> accumulated in deterministic order          │
│                                                                              │
│ Turn 2 (Fan-In): POST /chat/completions with tools=None                      │
│   └─► Forces text-only narrative synthesis across all tool outputs           │
└──────────────────────────────────────────────────────────────────────────────┘
   │
   ├─► Automatic Offline Fallback (_run_deterministic_fallback):
   │   if AI client lacks run_agent_loop, raises ModelInferenceError, or returns
   │   "[Simulated ...]" with 0 tool calls -> runs deterministic text/URL/QR checks
   │
   └─► _finalize_result(findings + tool EvidenceItems, llm_narrative)
```

**Important Prompt & Guardrail Details:**
- `_build_orchestrator_prompt()` caps extracted URLs at **12** and allows at most **2 URLs per distinct hostname** so marketing emails with dozens of tracking links do not bloat the LLM context.
- **No LLM Score Guessing:** The LLM only produces tool selections (Turn 1) and the explanatory narrative (Turn 2). Numeric scoring and verdicts are always computed deterministically afterward.

### 2.3 Shared Exit: Deduplication, Scoring & Recommendations (`_finalize_result`)
1. `_deduplicate_evidence(findings)` removes exact duplicates on `(category, source, summary)` while preserving order (preventing double-counting when both pre-checks and an orchestrator tool flag the same SPF failure or contact indicator).
2. `calculate_risk_and_verdict(unique_findings, has_content)` (`src/scamlens/investigator/scorer.py`):
   - Empty input (`not has_content`): score `0`, confidence `0.20`, `Insufficient evidence`.
   - Zero findings: score `10`, confidence `0.60`, `No clear scam indicators found`.
   - Weights: `INFO=0`, `LOW=10`, `MEDIUM=25`, `HIGH=45`, `CRITICAL=80` (summed and capped at `100`).
   - Verdict thresholds:
     - `has_critical` or `risk_score >= 70` or `high_count >= 2` → **`Likely scam`** (confidence `0.85`)
     - `risk_score >= 35` or `high_count == 1` → **`Suspicious`** (confidence `0.70`)
     - Otherwise → **`No clear scam indicators found`** (confidence `0.65`)
3. `generate_recommendations()` returns `POST_ACTION` emergency containment (`1930` helpline, `cybercrime.gov.in`, credential rotation, evidence preservation) or `PRE_ACTION` preventative steps.

---

## 3. State & Memory Model

ScamLens-AI has **no persistent cross-investigation agent memory** (no vector store, conversation memory, or LangGraph checkpointer):
- **Per-Investigation Scope:** Each `investigate()` / `investigate_email()` call creates a fresh local `findings` list and discards it on return.
- **Per-Orchestrator Run Scope:** Tools in `ToolDispatcher` are stateless and run concurrently; they cannot read each other's outputs mid-batch. Only the Turn 2 LLM call receives all `role="tool"` JSON messages together in its local `messages` list.
- **Read-Only Knowledge Base:** `RegionalKnowledgeBase` loads `src/scamlens/rag/data/trusted_domains.json` read-only.
- **Process / UI Caches:**
  - `src/scamlens/core/config.py`: `_cached_settings` singleton (resettable via `clear_settings_cache()`).
  - `src/scamlens/api/routes/emails.py`: `_GMAIL_PROFILE_CACHE` mapping `token.json` mtime/size to the authenticated Gmail email address (resettable via `clear_email_caches()`).
  - `src/GUI/static/app.js`: `state.polledGmailIds` (`Set`) and `state.emails` in browser memory.
  - `POST /api/v1/cache/clear` (and the UI **Clear Cache** button) clears all three caches and reloads `.env`.

---

## 4. The 9-Tool Forensic Arsenal (`SCAMLENS_TOOLS`)

Defined in `src/scamlens/ai/tools.py` and executed by `ToolDispatcher`:

| Tool Name | Underlying Implementation | Key Signals Produced |
| :--- | :--- | :--- |
| `analyze_url_structure` | `extractors/url.py -> analyze_url()` | Raw IP host, suspicious TLD, brand-hyphen impersonation, HTTP, credential paths |
| `check_threat_intelligence` | `intelligence/client.py -> check_url_reputation()` | Combined WhoisXML/RDAP age + VirusTotal v3 check |
| `inspect_domain_whois_age` | `intelligence/client.py -> inspect_domain_whois_rdap()` | Domain registration age (`<30d` HIGH, `<90d` MEDIUM, established INFO) |
| `check_virustotal_reputation` | `intelligence/client.py -> check_virustotal_reputation()` | Multi-engine VT consensus (`>=2` malicious CRITICAL, `1` malicious/`>=2` suspicious MEDIUM) |
| `verify_brand_official_domain` | `rag/knowledge_base.py -> verify_domain_against_brand()` | Cross-checks brand aliases (`sbi`, `hdfc`, `icici`, `indiapost`, etc.) vs `trusted_domains.json` |
| `decode_qr_payment` | `extractors/qr.py -> analyze_qr_payload()` | Parses `upi://pay` (`pa`, `pn`, `am`) or inspects embedded HTTP(S) URLs |
| `extract_text_indicators` | `extractors/text.py -> extract_text_indicators()` | Artificial urgency, KYC/OTP/PIN demands, prize/task scam phrases |
| `inspect_email_authentication` | `extractors/email.py -> extract_email_evidence()` | SPF/DKIM/DMARC failures, `Reply-To` mismatch, display-name spoofing, risky attachments |
| `inspect_contact_details` | `extractors/text.py -> extract_contact_indicators()` | Personal 10-digit Indian mobile numbers posing as official helplines; suspicious support emails |

---

## 5. Email Ingestion, Header Auth & 60s Gmail Polling

### 5.1 Parsing & SPF/DKIM/DMARC Analysis (`src/scamlens/extractors/email.py`)
1. **Gmail REST API / Raw `.eml` Parsing:** `parse_gmail_message()` and `parse_raw_email()` extract `Authentication-Results` and `Received-SPF` headers, decode `text/plain` and `text/html` MIME bodies, collect `<a href>` and regex URLs, and record attachment metadata.
2. **Auth Status Extraction (`_extract_auth_status`):** Matches `\b(spf|dkim|dmarc)\s*=\s*([a-zA-Z0-9_-]+)` in `Authentication-Results`, falling back to the leading status token in `Received-SPF` for SPF.
3. **Forensic Rules (`extract_email_evidence`):**
   - `spf_status in ("fail", "softfail")` → `HIGH` (`email_headers_spf`)
   - `dkim_status == "fail"` → `HIGH` (`email_headers_dkim`)
   - `dmarc_status == "fail"` → `CRITICAL` (`email_headers_dmarc`)
   - `reply_to_email` domain != `sender_domain` → `HIGH` (`email_headers_reply_to`)
   - Brand keyword in `sender_name` with non-official `sender_domain` → `HIGH` (`email_sender_impersonation`)
   - Dangerous extensions (`.exe`, `.scr`, `.bat`, `.vbs`, `.js`, `.iso`, `.wsf`, `.hta`, `.xlsm`, `.docm`) → `CRITICAL` (`email_attachment_analysis`)

### 5.2 All-Inbox Fetching & 1-Minute Auto-Polling
- **Query Scope:** GUI endpoints (`GET /api/v1/emails/gmail` and `POST /api/v1/emails/scan/stream`) default to `query="-in:trash -in:drafts"` and `include_spam_trash=True`, scanning **Primary, Promotions, Social, Updates, Archived/All Mail, and Spam** (both **read and unread**), excluding Trash and Drafts.
- **Connected Account Display:** `GmailReader.get_profile_email()` calls `users().getProfile(userId="me")` and exposes `connected_email` to the GUI topbar pill and auth banner.
- **Incremental 60s Poller (`src/GUI/static/app.js`):**
  - When Gmail OAuth is ready and **Auto-poll Gmail every 1 min** is checked, `syncGmailAutoPollState()` ticks every second and runs `pollGmailForNewEmails()` every 60s.
  - Passes `known_ids` (`state.polledGmailIds`) to `POST /api/v1/emails/scan/stream`; the server skips already-seen IDs before calling `get_message()` or running the investigator/LLM.
  - Overlapping polls are prevented via `state.isScanning`.
  - Clicking **Clear Cache** sets `state.forceRescanOnFetch = true` so the next **Fetch Inbox** click runs a full live scan with the selected strategy.

---

## 6. External Threat Intelligence (`ThreatIntelligenceClient`)

Defined in `src/scamlens/intelligence/client.py`:
- **Mode Switch:** Controlled by `USE_MOCK_INTELLIGENCE` (`settings.use_mock_intelligence`).
  - `true`: uses deterministic offline mocks (`icann_rdap_mock`, `virustotal_mock`).
  - `false`: runs live API queries.
- **Domain Age (`inspect_domain_whois_rdap`):**
  1. Reduces subdomains (e.g. `click.grammarly.com` → `grammarly.com`) via `_to_registrable_domain()`.
  2. If `WHOISXML_API_KEY` is set, queries WhoisXML `WhoisService` (`source="whoisxml"`), extracting `createdDate` / `registryData.createdDate` / `estimatedDomainAge` and `registrarName`.
  3. If WhoisXML is unset or fails, falls back to ICANN RDAP (`https://rdap.org/domain/{apex}`, `source="icann_rdap"`).
  4. On network failure, returns an unverified `icann_rdap_offline` notice.
- **URL Reputation (`check_virustotal_reputation`):**
  1. When `VIRUSTOTAL_API_KEY` is set and `use_mock=False`, queries `GET https://www.virustotal.com/api/v3/urls/{url_id}` (`source="virustotal_v3"`).
  2. Non-200/404 responses (e.g. HTTP `429`) or network errors return `source="virustotal_v3_offline"` (`is_verified=False`) rather than falling back to simulated mock results.

---

## 7. Web GUI, SSE Streaming & Verbose CLI

### 7.1 Web GUI & SSE (`src/GUI/server.py`, `src/GUI/static/`)
- Served via Python's built-in `ThreadingHTTPServer` (`scripts/run_gui.py`, default `127.0.0.1:8080`).
- Streaming routes (`/api/v1/investigate/stream`, `/api/v1/investigate/email/stream`, `/api/v1/emails/scan/stream`) run investigations in a worker thread, pushing `on_progress` events over SSE (`text/event-stream`) with 15-second `: keepalive` comments during slow LLM calls.
- The frontend (`app.js`) renders color-coded live stage feeds (purple `.llm-event` for LLM turns/calls, indented green `.tool-event` for parallel tool execution), formatted markdown summaries (`formatReportSummaryHtml()`), severity-filtered evidence cards, and a collapsible provenance trace.

### 7.2 Gmail CLI & Live Process Renderer (`scripts/scan_gmail.py`, `src/scamlens/cli_live.py`)
- Supports `-v` / `--v` / `--verbose` and `--json` (`--v --json` routes live UI to `stderr` so `stdout` stays valid JSON).
- `LiveProgressDisplay` uses `rich.live.Live` (`transient=True`, `redirect_stdout=False`, `redirect_stderr=False`) with separated `_print_lock` / `_state_lock` locking to render an animated spinner on TTYs and line-by-line streamed events in non-TTY pipes.
- `OpenAICompatibleClient.run_agent_loop()` emits `orchestrator_turn` and `llm_call_done` events (carrying `latency_ms`, `usage` tokens, `finish_reason`, and tool decisions) plus real-time `orchestrator_tool_done` events via `concurrent.futures.as_completed()`, highlighted as `[LLM CALL #N]` in CLI output.
