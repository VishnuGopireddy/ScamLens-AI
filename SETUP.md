# ScamLens-AI Repository Setup & Local Development Guide

This document contains step-by-step instructions for setting up the local development environment, configuring environment variables, running investigations via CLI, launching the API server, and executing tests.

---

## 1. Prerequisites
- **Python 3.10+**
- (Recommended) [`uv`](https://docs.astral.sh/uv/) or standard `python3 -m venv` / `pip`

---

## 2. Environment Configuration
Copy the template configuration file:
```bash
cp .env.example .env
```

Key configuration options in `.env`:
- `DEFAULT_AI_PROVIDER`: Select your AI engine (`custom`, `groq`, `ollama`, `vllm`, `gemini`, `openai`). **Default: `custom`**.
- **Custom / Private Endpoint Configuration (Default)**:
  - `CUSTOM_AI_BASE_URL`: OpenAI-compatible API base URL (e.g. `https://103.42.50.41:1034/v1`).
  - `CUSTOM_AI_API_KEY`: Bearer token / API password for the custom endpoint.
  - `CUSTOM_AI_MODEL`: Model name deployed on the endpoint (e.g. `Qwen/Qwen3-8B`).
  - `CUSTOM_AI_CA_CERT`: Path to CA certificate for private/self-signed SSL (e.g. `assets/vm04-ca.crt`).
    > **Note**: Place your certificate files inside the `assets/` folder. All `*.crt` and `*.pem` files are ignored by `.gitignore` to prevent committing private credentials.
- `GROQ_API_KEY`: (Optional) Groq API key if using cloud Llama models instead.
- `USE_MOCK_INTELLIGENCE`: Set to `true` (default) for offline testing, or `false` when connecting live VirusTotal / Safe Browsing keys.
- `ENABLE_PII_REDACTION`: Set to `true` (default) to automatically sanitize OTPs, passwords, and sensitive cards.

---

## 3. Installation

### Option A: Using `uv` (Fastest)
```bash
uv pip install -e ".[dev,ai,gmail,agentic]"
# Or install using requirements.txt
uv pip install -r requirements.txt
```

### Option B: Using standard Python venv
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev,ai,gmail,agentic]"
# Or install using requirements.txt
pip install -r requirements.txt
```

### Option C: Automated Setup Script
Run the automated dev bootstrap script:
```bash
./scripts/setup_dev.sh
```

---

## 4. Test API Key & AI Call First

Before running full scam investigations or starting services, verify that your AI provider API key is recognized and responding properly.

### Method 1: Using the Verification Script (Recommended)
Run the built-in diagnostic test:
```bash
python3 scripts/test_api.py
```
This script will:
- Check your active provider (`groq`, `ollama`, `gemini`, etc.) and model name.
- Verify whether an API key is loaded from `.env`.
- Send a lightweight live ping and measure response latency.
- Test structured JSON formatting.

### Method 2: Quick Python One-Liner
```bash
python3 -c "from scamlens.ai import get_ai_client; client = get_ai_client(); print(client.generate_text('Reply with OK if online.'))"
```

### Method 3: Direct cURL Test (Custom Endpoint)
```bash
curl --cacert "assets/vm04-ca.crt" \
  https://103.42.50.41:1034/v1/chat/completions \
  -H "Authorization: Bearer $CUSTOM_AI_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "Qwen/Qwen3-8B",
    "messages": [{"role": "user", "content": "Reply with OK"}],
    "max_tokens": 50
  }'
```

### Method 4: Alternative Direct cURL Test (e.g. Groq)
```bash
curl -X POST https://api.groq.com/openai/v1/chat/completions \
  -H "Authorization: Bearer $GROQ_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "llama-3.3-70b-versatile",
    "messages": [{"role": "user", "content": "Reply with OK"}]
  }'
```

---

## 5. Running Investigations (CLI)

The CLI allows investigating suspicious messages, URLs, or QR codes directly from the terminal without starting a server:

```bash
# Analyze a phishing SMS and link
python3 src/scamlens/cli.py \
  --text "Dear customer, your bank account is blocked. Immediately update KYC at http://sbi-verification.xyz" \
  --url "http://sbi-verification.xyz"

# Analyze a payment QR code
python3 src/scamlens/cli.py \
  --qr "upi://pay?pa=scammer@upi&pn=LuckyPrize&am=10000"

# Output results in structured JSON format
python3 src/scamlens/cli.py --text "Urgent electricity bill power cut" --json
```

---

## 6. Email Analysis & Forensics (Local Datasets & Gmail REST API)

ScamLens-AI provides dual support for email investigation:
1. **Local Offline Datasets** (`LocalEmailReader`): Test pipelines, algorithms, and agentic workflows completely offline without Google Cloud credentials or OAuth.
2. **Live Gmail REST API** (`GmailReader`): Securely fetch and triage live inbox messages using OAuth 2.0 read-only permissions (`https://www.googleapis.com/auth/gmail.readonly`).

---

### A. Offline Development & Local Proof-of-Concept (Recommended for PoC)

For rapid local testing and development, ScamLens-AI includes a 20-email benchmark dataset covering authentic Indian financial and government communications (5 HAM, 15 SPAM):
- **Raw RFC 5322 MIME messages**: `data/raw_emails/1.eml` through `data/raw_emails/20.eml` (ignored by git).
- **Gmail REST API JSON format**: `data/spam-indian-bank-emails.json` (exact schema returned by `users.messages.get`).
- **Raw Markdown dataset**: `data/spam-indian-bank-emails.md` (raw MIME code blocks without manual field categorization).

#### 1. Programmatic Usage with `LocalEmailReader`
`LocalEmailReader` provides the exact same API interface as `GmailReader` (`fetch_messages()`, `get_message()`, `list_message_summaries()`):

```python
from scamlens.extractors.email import LocalEmailReader, extract_email_evidence
from scamlens.investigator.engine import ScamInvestigator

# Option 1: Load individual numbered .eml files (data/raw_emails/1.eml ... 20.eml)
reader = LocalEmailReader("data/raw_emails")

# Option 2: Load Gmail REST API JSON format
# reader = LocalEmailReader("data/spam-indian-bank-emails.json")

# Option 3: Load directly from Markdown dataset
# reader = LocalEmailReader("data/spam-indian-bank-emails.md")

# Fetch all parsed EmailMessage objects (sorted numerically 1..20)
messages = reader.fetch_messages()

# Inspect automatically separated fields
for msg in messages[:3]:
    print(f"[{msg.id}] {msg.subject}")
    print(f"  Sender:      {msg.sender_name} <{msg.sender_email}> (domain: {msg.sender_domain})")
    print(f"  To / CC:     {msg.recipient} | CC: {msg.cc}")
    print(f"  Auth:        SPF={msg.spf_status}, DKIM={msg.dkim_status}, DMARC={msg.dmarc_status}")
    print(f"  Attachments: {[a.filename for a in msg.attachments]}")
    print(f"  URLs Found:  {msg.extracted_urls}")
    print(f"  Content:     {msg.body_cleaned[:120]}...\n")

# Run evidence extraction or full scam investigation
investigator = ScamInvestigator()
result = investigator.investigate_email(messages[0])
print(f"Verdict: {result.verdict.value} | Risk Score: {result.risk_score}/100")
```

#### 2. Regenerating or Customizing Dummy Datasets
The data preparation and generation scripts are maintained under `src/data_generate_dummy/`:
```bash
# Generate/regenerate data/raw_emails/1.eml ... 20.eml, .json, and .md
python3 src/data_generate_dummy/generate_raw_datasets.py
```

---

### B. Live Google Cloud Gmail REST API Setup
To connect to live Gmail accounts:
1. Open the [Google Cloud Console](https://console.cloud.google.com).
2. Create a project (or select an existing one).
3. Navigate to **APIs & Services > Library**, search for **Gmail API**, and click **Enable**.
4. Configure the **OAuth consent screen**:
   - User Type: **External**.
   - Under **Test users**, add your email (e.g. `your-email@gmail.com`) and click **Save**, OR click **Publish App** to allow access.
5. Create **OAuth 2.0 Credentials**:
   - Go to **APIs & Services > Credentials**.
   - Click **Create Credentials > OAuth client ID**.
   - Application type: **Desktop app** *(Recommended for scripts and notebooks; permits localhost login without redirect URI restrictions)*.
   - Click **Create**, download the JSON client secret, and save it in the project root as `credentials.json`:
     ```bash
     cp ~/Downloads/client_secret_*.json credentials.json
     ```

> **Security Note**: Both `credentials.json` and `token.json` are listed in `.gitignore` to prevent committing secrets to version control.

### B. Environment Configuration (Optional)
In `.env`, you can customize the credential paths if needed:
```bash
GMAIL_CREDENTIALS_FILE=credentials.json
GMAIL_TOKEN_FILE=token.json
GMAIL_SCOPES=https://www.googleapis.com/auth/gmail.readonly
```

### C. Interactive Demo in Jupyter Notebook
Launch the dedicated Gmail parsing notebook to authenticate and print all extracted email fields:
```bash
# Open in VS Code, Cursor, or Jupyter Lab
notebooks/gmail_auth_and_read.ipynb
```
The notebook automatically:
- Connects using `credentials.json` (and caches your login in `token.json`).
- Queries emails by folder or category (`is:unread`, `label:INBOX`, `category:primary`, `category:updates`, etc.).
- Decodes MIME payloads and extracts:
  - **Sender** (Display Name & Email Address)
  - **Domain of the Sender**
  - **Subject**
  - **Time of the Email**
  - **Recipient(s)**
  - **Reply-To**
  - **Has Attachment** (Boolean flag, filenames, MIME types, and sizes)
  - **Email Content** (Decoded text content)
  - **Embedded Links** (All URLs extracted from text and HTML)
  - **Security Headers** (SPF, DKIM, DMARC validation)

### D. Scanning Emails via CLI
Run the CLI scanner to triage emails directly from your terminal:
```bash
# Scan the 5 latest unread emails
python3 scripts/scan_gmail.py --query "is:unread" --max-results 5

# Scan using the Phase 1 AI Orchestrator strategy
python3 scripts/scan_gmail.py --query "is:unread" --max-results 5 --strategy orchestrator

# Scan latest emails in the Inbox
python3 scripts/scan_gmail.py --query "label:INBOX" --max-results 10

# Scan a specific email by Gmail message ID with structured JSON output
python3 scripts/scan_gmail.py --msg-id <MESSAGE_ID> --json
```

### E. Programmatic Usage in Python
```python
from scamlens.extractors.email import GmailReader
from scamlens.investigator.engine import ScamInvestigator

# 1. Initialize reader and fetch messages
reader = GmailReader()
messages = reader.fetch_messages(query="label:INBOX", max_results=5)

# 2. Inspect parsed fields
for msg in messages:
    print(f"Subject:        {msg.subject}")
    print(f"Sender:         {msg.sender_email} (domain: {msg.sender_domain})")
    print(f"Time:           {msg.date}")
    print(f"Has Attachment: {msg.has_attachment}")
    print(f"Content:        {msg.body_cleaned[:200]}...")

    # Optional: Run ScamLens multi-evidence investigation
    # investigator = ScamInvestigator()
    # result = investigator.investigate_email(msg)
```

### F. Troubleshooting Common Errors
- **`Error 400: redirect_uri_mismatch`**: Your OAuth client ID in Google Cloud Console was created as a "Web application" instead of a "Desktop app". In GCP Console > Credentials, create a new OAuth client ID with Application type = **Desktop app**.
- **`Error 403: access_denied`**: The GCP project is in "Testing" status and your email is not in the Test Users list. In GCP Console > OAuth consent screen, either add your email under **Test users** and click Save, or click **Publish App**.
- **`google-api-python-client is not installed`**: Install with `pip install -r requirements.txt` or `pip install -e ".[gmail]"`.

---

## 7. Agentic AI & Phase 1 Orchestrator

ScamLens-AI implements a **Phase 1 2-Turn Parallel Tool Orchestrator** (`strategy="orchestrator"`) in `src/scamlens/investigator/engine.py` and `src/scamlens/ai/openai_compat.py`:
- **Turn 1 (Parallel Fan-Out)**: The LLM selects tools from the 9-tool `SCAMLENS_TOOLS` catalog (`src/scamlens/ai/tools.py`), and `ThreadPoolExecutor` runs them concurrently.
- **Turn 2 (Forced Synthesis & Deterministic Scoring)**: The LLM synthesizes correlated findings while `src/scamlens/investigator/scorer.py` computes the deterministic 0–100 risk score and verdict from typed `EvidenceItem`s.
- **Resilient Fallback**: Automatically falls back to `strategy="linear"` if the LLM endpoint is unreachable or running in simulated offline mode.

### A. Installing Agentic Dependencies
Install the dedicated `agentic` extras group for LangGraph notebook workflows and Phase 2 development:
```bash
uv pip install -e ".[agentic]"
# Or using pip:
pip install langgraph>=1.2.0 langchain-core>=0.3.0
```

### B. Architectural Blueprints (Phase 2 Roadmap)
Refer to [claude/agentic-ai-plan.md](claude/agentic-ai-plan.md) for the Phase 2 LangGraph specification:
- **Plan A (Hierarchical Multi-Agent Orchestrator)**: A supervisor agent routes investigation tasks to specialized domain subagents (Email Forensics, Threat Intel, Content Triage, Evidence Synthesizer).
- **Plan B (Cyclic ReAct State Machine)**: A stateful ReAct cycle with iterative tool invocation and dynamic termination safeguards.
- **Plan C (Unified Hybrid Engine)**: Dynamically selects Plan B for low-latency single email triage and Plan A for complex, multi-evidence incidents.

---

## 8. Launching the Interactive Web GUI (Live SSE)

ScamLens-AI includes a zero-dependency Web GUI under `src/GUI/` powered by Python's built-in `ThreadingHTTPServer` and Server-Sent Events (SSE):

```bash
# Start the Web GUI server (default http://127.0.0.1:8080)
python3 scripts/run_gui.py --host 127.0.0.1 --port 8080

# Alternatives:
PYTHONPATH=src python3 -m GUI --port 8080
python3 src/scamlens/cli.py --gui --port 8080
```

Open `http://127.0.0.1:8080` in your browser to access:
1. **Multimodal Investigator**: Submit message text, URLs, QR/UPI payloads, screenshots (drag-and-drop), `PRE_ACTION`/`POST_ACTION` stage, and one-click benchmark presets.
2. **Email & Gmail Forensics**: Inspect local datasets (`data/raw_emails`), fetch/scan live Gmail messages (requires `credentials.json` + cached `token.json`), or paste/upload `.eml` files with a live status feed (`reading_email` → `email_parsed` → `analyzing_url` → `scoring` → `completed`).
3. **Trusted Registry & Samples**: Browse verified Indian bank domains, SMS headers, helplines (`1930`), UPI rules, and sample scenarios.
4. **Technical Details (Top-Right Tab)**: Interactive architecture diagram, Phase 1 Orchestrator flow & live system prompt inspector, and 9-tool JSON schema explorer.

---

## 9. Starting the FastAPI REST Service

Launch the FastAPI development server (when `fastapi` and `uvicorn` are installed):
```bash
uvicorn scamlens.api.main:app --host 0.0.0.0 --port 8000 --reload
```
- Interactive OpenAPI Docs (Swagger UI): `http://localhost:8000/docs`
- Health check: `GET http://localhost:8000/health` (and `/api/v1/health`)
- Investigation endpoints: `POST /api/v1/investigate`, `POST /api/v1/investigate/email`
- Metadata & Email endpoints: `GET /api/v1/samples`, `GET /api/v1/registry`, `GET /api/v1/architecture`, `GET /api/v1/emails/local`, `GET /api/v1/emails/gmail/status`, `GET /api/v1/emails/gmail`

*(For SSE streaming endpoints `/api/v1/investigate/stream`, `/api/v1/investigate/email/stream`, and `/api/v1/emails/scan/stream`, launch the built-in GUI server in Section 8.)*

---

## 10. Running Tests & Evaluation Benchmark

```bash
# Run unit test suite (50 unit tests covering extractors, orchestrator, GUI/SSE, models, readers)
PYTHONPATH=src python3 -m unittest discover tests -v

# Run reproducible evaluation benchmark (README §9 & §10)
PYTHONPATH=src python3 benchmark/runner.py
```

