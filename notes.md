# ScamLens-AI Project Notes

## Datasets & Benchmark Data

- **Hinglish Scam Text Dataset**:
  - Source: [`bolewara/hinglish-scam-text-dataset`](https://huggingface.co/datasets/bolewara/hinglish-scam-text-dataset/blob/main/data.json)
  - Local sample file: `data/sample_data.json` (~472 KB, labeled SMS messages with `0 = legitimate`, `1 = scam`)
  - Target coverage: Benign transactional alerts, fake KYC bank suspensions, prize/lottery scams, electricity disconnection threats, and task/job fraud.

---

## Prompt Engineering Strategy & Implemented Catalog

### 1. Storage & Management Architecture
- **Directory**: `src/scamlens/ai/prompts/`
- **Catalog**: `src/scamlens/ai/prompts/catalog/`
- **Format**: Structured YAML files parsed into typed `PromptTemplate` dataclasses via `loader.py`.
- **Packaging**: Packaged directly within the `scamlens` Python distribution.
- **Model Parameters**: Bound directly within each prompt YAML (`temperature`, `max_tokens`, `response_format`).
- **Decoupled Engine**: Compatible with Groq (Llama-3.3), Ollama, vLLM, OpenAI, and Gemini.

### 2. Implemented Catalog Files

```
src/scamlens/ai/prompts/
├── __init__.py                                 # Exposes load_prompt & PromptTemplate
├── loader.py                                   # Typed loader, validator & renderer
└── catalog/                                    # Active YAML prompt templates
    ├── text_triage_v1.yaml                     # SMS/WhatsApp screening (Few-shot)
    ├── vision_screenshot_v1.yaml               # Multimodal screenshot inspection
    ├── investigation_agent_v1.yaml             # Agentic loop & tool selection
    ├── evidence_synthesis_v1.yaml              # Forensic CoT & calibrated scoring
    └── action_guidance_v1.yaml                 # Pre-action vs Post-harm guidance
```

### 3. Active Prompts Summary

| # | Prompt File | Purpose | Primary Technique |
|---|---|---|---|
| 1 | `text_triage_v1.yaml` | Rapid screening of SMS / WhatsApp / Hinglish text; extracts claimed brands, links, and urgency. | **Few-Shot In-Context Learning** |
| 2 | `vision_screenshot_v1.yaml` | OCR & visual analysis of message screenshots, sender badges, spoofed UI layouts. | **Multimodal Vision & Role-Based Prompting** |
| 3 | `investigation_agent_v1.yaml` | Agentic loop orchestration; guides tool selection (RAG domain check, URL parser, threat intel). | **ReAct / Tool-Calling Schema** |
| 4 | `evidence_synthesis_v1.yaml` | Correlates extracted indicators, weighs conflicting evidence, assigns risk score (0-100), and records uncertainties. | **Chain-of-Thought (CoT) & Strict JSON Schema** |
| 5 | `action_guidance_v1.yaml` | Contextual response generator: preventative checks for pre-action vs emergency steps for post-harm. | **Guardrail & Conditional Routing** |

---

## Prompt Techniques & Rationale

### A. Few-Shot In-Context Learning
- **Why**: General LLMs frequently misunderstand Indian fraud patterns (e.g. reverse UPI requests where victims are told to enter a PIN to *receive* money, or Hinglish colloquial urgency: *"bijli cut ho jayegi"*).
- **Implementation**: 3 calibrated pairs in `text_triage_v1.yaml`:
  1. *Benign Transaction*: Official SBI credit alert with verified domain and helpline.
  2. *Electricity Phishing*: Threat of immediate power cut tonight directing to a personal mobile number.
  3. *Prize / Cashback Phishing*: Unsolicited Google Pay scratch card directing to a disposable `.xyz` link.

### B. Chain-of-Thought (CoT) Forensic Deduction
- **Why**: Scam detection requires deductive reasoning across multiple pieces of evidence, not shallow keyword matching.
- **Implementation**: In `evidence_synthesis_v1.yaml`, the model must populate a `"thought_process"` object evaluating:
  1. *claim_analysis*: What is requested or threatened?
  2. *domain_and_channel_check*: Does the domain match official registry records?
  3. *pressure_tactics*: Are there artificial deadlines, fear tactics, or unsolicited rewards?
  4. *contradiction_or_gaps*: What remains unverified or ambiguous?

### C. Epistemic Guardrails & Explicit Uncertainty (README §6, §11)
- Prompt rules strictly enforce:
  - *Absence of warning != Safety*: Unlisted domains must not be classified as legitimate solely because they aren't on blocklists.
  - *Abstention on ambiguous inputs*: Return `Insufficient evidence` if context is inadequate.
  - *Zero secret solicitation*: The AI must never prompt users to enter real OTPs or passwords.

### D. Structured Schema Enforcement
- All analytical outputs enforce JSON mode (`response_format: {"type": "json_object"}`) matching `InvestigationResult` data contracts.

---

## Developer Usage

```python
from scamlens.ai import get_ai_client, load_prompt

# 1. Load template from catalog
prompt = load_prompt("text_triage_v1")

# 2. Render OpenAI-format messages
messages = prompt.render_messages(text="Dear user, electricity cut tonight. Call 9876543210.")

# 3. Execute with configured parameters
client = get_ai_client()
response = client.chat_completion(
    messages=messages,
    temperature=prompt.model_parameters.get("temperature", 0.0),
)
```

---

## Testing & Verification
- Unit test suite: `tests/test_prompts.py`
- Test coverage: Loading all catalog prompts, validating variable requirements, verifying few-shot message generation, and error handling.
- Status: **19/19 passing** across all test suites (`python3 -m unittest discover tests`).
