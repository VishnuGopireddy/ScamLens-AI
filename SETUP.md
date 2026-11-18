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
uv pip install -e ".[dev,ai,gmail]"
# Or install using requirements.txt
uv pip install -r requirements.txt
```

### Option B: Using standard Python venv
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev,ai,gmail]"
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

## 6. Accessing & Reading Emails (Gmail REST API)

ScamLens-AI provides an official Google Gmail REST API connector using OAuth 2.0 with least-privilege read-only permissions (`https://www.googleapis.com/auth/gmail.readonly`).

### A. Google Cloud Console Setup
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

## 7. Starting the REST API Service

Launch the FastAPI development server:
```bash
uvicorn scamlens.api.main:app --host 0.0.0.0 --port 8000 --reload
```
- Interactive OpenAPI Docs (Swagger UI): `http://localhost:8000/docs`
- Health check: `http://localhost:8000/health`
- Investigation endpoint: `POST http://localhost:8000/api/v1/investigate`

---

## 8. Running Tests & Evaluation Benchmark

```bash
# Run unit test suite
python3 -m unittest discover tests

# Run reproducible evaluation benchmark (README §9 & §10)
python3 benchmark/runner.py
```

