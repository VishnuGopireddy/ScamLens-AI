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
- `DEFAULT_AI_PROVIDER`: Select your AI engine (`groq`, `ollama`, `vllm`, `gemini`, `openai`). Default: `groq`.
- `GROQ_API_KEY`: Enter your Groq API key for cloud inference with open-source Llama models. (If left empty, ScamLens automatically runs in safe offline mock mode).
- `USE_MOCK_INTELLIGENCE`: Set to `true` (default) for offline testing, or `false` when connecting live VirusTotal / Safe Browsing keys.
- `ENABLE_PII_REDACTION`: Set to `true` (default) to automatically sanitize OTPs, passwords, and sensitive cards.

---

## 3. Installation

### Option A: Using `uv` (Fastest)
```bash
uv pip install -e ".[dev,ai]"
```

### Option B: Using standard Python venv
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev,ai]"
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

### Method 3: Direct cURL Test (e.g. Groq)
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

## 6. Starting the REST API Service

Launch the FastAPI development server:
```bash
uvicorn scamlens.api.main:app --host 0.0.0.0 --port 8000 --reload
```
- Interactive OpenAPI Docs (Swagger UI): `http://localhost:8000/docs`
- Health check: `http://localhost:8000/health`
- Investigation endpoint: `POST http://localhost:8000/api/v1/investigate`

---

## 7. Running Tests & Evaluation Benchmark

```bash
# Run unit test suite
python3 -m unittest discover tests

# Run reproducible evaluation benchmark (README §9 & §10)
python3 benchmark/runner.py
```

