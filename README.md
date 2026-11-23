# ScamLens-AI
### Multimodal Agentic AI for Scam Detection, Investigation and Response


**Project type:** Open-source AI project  
**Domain:** Cybersecurity, consumer protection and fraud awareness  
**Core capabilities:** Multimodal AI, evidence-based investigation, retrieval-augmented generation (RAG), agentic reasoning and evaluation  
**Initial target audience:** Consumers in India, with a design that can eventually support other regions and languages.

---

## 1. Project Overview

ScamLens AI is an AI-powered assistant designed to help people investigate suspicious messages, websites, QR codes, payment requests and promotional offers.

People encounter potential scams through SMS, WhatsApp, social media, email, online advertisements and other digital channels. These messages may impersonate banks, government departments, delivery services, employers, online marketplaces or trusted brands. They may attempt to steal personal information, obtain account credentials, induce fraudulent payments or persuade people to click malicious links.

Identifying these scams is difficult because fraudulent messages can look convincing, legitimate organizations may communicate through unfamiliar channels, and the same piece of evidence can have different meanings depending on the context.

ScamLens AI aims to help users make more informed decisions by examining the evidence, investigating suspicious indicators, consulting trusted information sources and explaining the reasons behind its assessment.

Users will be able to submit suspicious content in several forms, including:

- Text copied from an SMS, email, social-media post or WhatsApp message.
- Screenshots of suspicious messages or conversations.
- Website URLs and links embedded in messages.
- QR codes that may contain URLs or payment-related information.
- Images or text describing promotional offers, job opportunities, prizes, investments or requests for payment.
- Multiple pieces of evidence relating to the same suspected incident.

The system will return a risk assessment, an understandable explanation, the evidence supporting its findings and practical recommendations for what the user should do next.

The goal is not merely to predict whether a message is spam. It is to build a trustworthy investigation assistant that helps users understand *why* something appears suspicious, *what remains uncertain*, and *what action is appropriate*.

## 2. Problem Statement

Existing spam filters and scam detectors can identify familiar suspicious patterns, but a user often needs more information than a binary classification.

For example, someone may receive a WhatsApp message claiming that their bank account will be suspended unless they complete KYC verification through an attached link.

The user needs to understand:

1. Whether the message contains suspicious claims or requests.
2. Whether the linked domain matches the organization being impersonated.
3. Whether independent evidence supports or contradicts the message.
4. Whether the message is attempting to obtain sensitive information or money.
5. How confident the assessment should be, given the available evidence.
6. What the user should do before taking the requested action.

A simple classifier may label the message as phishing without explaining the decision. A language model may generate a convincing explanation without verifying the underlying facts. A website reputation check may return no known threat even when a newly created fraudulent website has not yet been reported.

ScamLens AI will address these limitations by treating scam detection as an evidence-gathering and decision-support problem.

The system should distinguish confirmed findings from suspicious indicators, identify contradictions, communicate uncertainty and avoid declaring a website or offer safe merely because no warning was found.

## 3. Project Vision

Build an accessible, multimodal AI assistant that helps people recognize potential digital fraud, investigate suspicious communications and make better-informed decisions before sharing sensitive information or transferring money.

The longer-term vision is to create an open-source platform with a reproducible evaluation benchmark for measuring how well AI systems detect, investigate and explain scams across different input types and real-world scenarios.

## 4. Project Objectives

### Objective 1: Support multimodal scam analysis

Allow users to submit different kinds of digital evidence through a unified interface.

The system should support text, message screenshots, URLs, QR codes and descriptions of suspicious offers. It should accommodate cases where users provide several related items together instead of requiring each item to be investigated independently.

### Objective 2: Identify and assess potential scam indicators

Identify patterns associated with phishing, impersonation, fraudulent payment requests, fake job offers, suspicious investment opportunities, fake prizes and other deceptive activities.

Relevant indicators may include suspicious URLs, misleading claims, requests for credentials or OTPs, unusual payment instructions, artificial urgency and inconsistencies between the claimed sender and available evidence.

The presence of an individual indicator should not automatically establish that a message is fraudulent.

### Objective 3: Investigate evidence rather than rely on pattern matching alone

Evaluate relevant evidence using available information sources and verification mechanisms.

Where appropriate, this may include examining URL characteristics, checking available domain or threat-intelligence information, decoding QR codes, consulting trusted security guidance and comparing claims against independently available information.

The investigation should preserve the distinction between a verified finding, an unverified claim and an inference made by the AI.

### Objective 4: Produce an explainable risk assessment

Return an understandable verdict accompanied by supporting evidence.

The assessment should identify suspicious indicators, explain how they affect the conclusion, disclose important uncertainties and identify missing information when additional context is required.

A risk score should be treated as an estimate whose reliability must be measured against labelled evaluation data, not as a guarantee of fraud or legitimacy.

### Objective 5: Recommend appropriate next steps

Help users decide what to do after receiving an assessment.

Recommendations may include avoiding a suspicious link, verifying a claim through an organization's independently located official channel, refusing to disclose sensitive credentials, preserving relevant evidence, or using the appropriate official reporting process.

When a user has already shared information or transferred money, the system should recognize that this is a different situation and provide appropriately urgent guidance.

### Objective 6: Build a measurable and reproducible evaluation benchmark

Evaluate the system on more than overall classification accuracy.

The benchmark should assess scam detection, false positives, missed scams, information extraction, evidence quality, source attribution, appropriate uncertainty, recommendation correctness and end-to-end investigation performance.

The objective is to make improvements measurable and enable fair comparisons between models and system variants.

### Objective 7: Design for privacy and responsible use

Treat screenshots, messages, phone numbers, financial information and transaction references as potentially sensitive data.

The project should minimize unnecessary collection and retention, mask sensitive details where appropriate, clearly communicate how submitted data is handled, and prevent the system from asking users to disclose passwords, OTPs, PINs or other authentication secrets.

ScamLens AI should assist users in making decisions rather than autonomously executing payments, accessing accounts or submitting reports without consent.

## 5. Primary Use Cases

### Use Case A: Suspicious SMS or WhatsApp message

A user submits a message claiming that a bank account, delivery or digital service will be blocked unless immediate action is taken.

The system extracts the relevant claims, identifies suspicious requests, examines any supplied URL and provides an evidence-backed assessment with recommended next steps.

### Use Case B: Suspicious website or link

A user submits a URL received through a message, advertisement or social-media post.

The system examines the available URL and domain evidence, checks relevant sources where available, and determines whether the evidence supports a high-risk, suspicious or inconclusive assessment.

The system should not assume a website is safe simply because a threat-intelligence service has no record of it.

### Use Case C: QR code or payment request

A user submits a QR code found in a message, advertisement, invoice or payment request.

The system decodes the QR payload, identifies its type and evaluates the available context. A payment QR code must not be classified as fraudulent solely because it requests payment; the recipient, claim and surrounding evidence matter.

### Use Case D: Suspicious promotional offer

A user receives an offer involving a prize, a job, an investment or an unusually attractive discount.

The system examines the wording, claimed organization, payment requirements, contact information and any supporting links. It explains which aspects are suspicious and what remains unverified.

### Use Case E: Multiple pieces of related evidence

A user submits a message screenshot, its associated URL and additional details about a payment request.

The system treats the submissions as one investigation, correlates the findings and identifies whether the evidence collectively supports or contradicts the original claim.

### Use Case F: Suspected scam that has already caused harm

A user reports that they clicked a link, shared credentials or transferred money.

The system recognizes the incident's stage and provides appropriate guidance for reducing further harm, preserving evidence and contacting relevant official channels. It must not promise recovery of funds or imply that reporting guarantees a particular outcome.

## 6. Expected Output

For each investigated case, ScamLens AI should aim to provide the following results.

### A. Verdict

Use carefully defined assessment categories such as:

- **Likely scam:** Multiple material indicators support a fraudulent interpretation.
- **Suspicious — further verification needed:** Relevant warning signs exist, but the evidence does not justify a stronger conclusion.
- **Insufficient evidence:** The available information is incomplete or inconclusive.
- **No clear scam indicators found:** The investigation has not identified sufficient evidence of a scam. This does not guarantee safety.

These categories should be supported by documented decision criteria and evaluated against labelled examples.

### B. Risk score

Provide a score on a 0–100 scale when there is sufficient evidence and a validated scoring approach.

The score should indicate estimated risk rather than imply mathematical certainty. Its interpretation, calibration and limitations must be documented.

### C. Evidence and explanation

Identify the specific findings behind the assessment, including:

- Suspicious or inconsistent claims.
- Potential impersonation indicators.
- Relevant URL or QR-code observations.
- Requests for sensitive information or unusual payments.
- Findings from trusted external sources.
- Contradictory evidence, unresolved questions and important limitations.

The system should distinguish direct observations from inferences.

### D. Recommended action

Present practical, context-specific next steps. These may include independent verification, avoiding disclosure of sensitive information, preserving evidence or contacting an appropriate official organization.

### E. Investigation provenance

Where external sources are consulted, provide their source identity, relevant supporting information and retrieval time where available. Distinguish verified source findings from model-generated reasoning and disclose checks that could not be completed.

## 7. Scope and Priorities

### Initial scope

The first version will focus on digital scam investigation, particularly phishing, impersonation, fraudulent offers and suspicious payment requests.

The initial experience should support:

- Text-based submissions.
- Image and screenshot submissions.
- URL submissions.
- QR-code submissions.
- Contextual descriptions of offers and payment requests.
- An evidence-backed verdict and recommendations.
- Evaluation using labelled cases.

### Potential future extensions

Once the initial capabilities are reliable, the project may expand to include:

- More Indian languages and realistic Hinglish messages.
- Additional scam types, including impersonation and investment fraud.
- Mobile application support.
- Related-incident grouping and investigation history.
- Post-incident response and evidence organization.
- Additional verification sources and threat-intelligence integrations.
- An open benchmark and public leaderboard.

These extensions are possible directions, not prerequisites for the initial release.

## 8. What Is Out of Scope?

To maintain a focused and responsible project, ScamLens AI will not initially attempt to:

- Guarantee that a message, URL, website or offer is safe.
- Replace official cybersecurity investigations or law-enforcement decisions.
- Recover transferred money or guarantee a refund.
- Access the user's banking, email or social-media accounts autonomously.
- Perform payments, submit complaints or contact third parties without appropriate user authorization.
- Treat every unsolicited advertisement as fraud.
- Make unsupported claims about a person's identity or intent.
- Use the model's confidence or generated explanation as a substitute for verifiable evidence.

## 9. Evaluation and Success Criteria

The project's quality will be assessed using a dedicated evaluation suite containing benign messages, suspicious communications, phishing examples, QR-code cases, fraudulent offers, inconclusive examples and multi-evidence incidents.

Evaluation will cover the following dimensions:

**Scam classification**
- Precision, recall and macro F1 across defined scam categories.
- False-positive rate on legitimate messages and offers.
- Recall for high-risk cases.

**Evidence extraction**
- Correct extraction of URLs, organization names, payment amounts, contact information and other relevant fields.
- Robustness to screenshots, incomplete text and formatting differences.

**Evidence grounding**
- Correctness of source references.
- Whether cited sources actually support the associated claims.
- Frequency of unsupported or fabricated factual claims.

**Decision quality**
- Correctness of risk assessments against labelled examples.
- Appropriate handling of contradictory or insufficient evidence.
- Correctness and safety of recommended next steps.

**Operational quality**
- Processing time, cost and failure rate.
- Performance across different input formats.
- Reproducibility of results across model or system changes.

Overall performance should not conceal critical failures. False negatives on dangerous scams, false accusations against legitimate organizations, and unsafe recommendations should be reported separately.

The initial release will establish baseline results before numerical improvement targets are set.

## 10. Dataset and Benchmark Strategy

The evaluation dataset will combine appropriate publicly available data with a carefully documented set of investigation scenarios.

Public data may be used to study message classification, URL-based phishing detection and multimodal phishing evidence, subject to its licensing and permitted uses.

A complementary scenario set will cover complete user journeys, including the user's context, submitted evidence, expected findings, acceptable uncertainty and appropriate next steps.

Cases may include verified examples, carefully constructed synthetic cases and manually reviewed scenarios. Their provenance must be recorded so that synthetic examples are never misrepresented as real-world incidents.

The dataset should include both malicious and legitimate examples, difficult borderline cases, contradictory evidence and examples where the correct outcome is to abstain from making a definitive claim.

Training, development and test splits should be designed to minimize leakage between duplicated messages, related campaigns and near-identical examples. A held-out test set will help make the benchmark more reliable.

## 11. Guiding Principles

ScamLens AI will follow these principles throughout development:

1. **Evidence before confidence:** A persuasive explanation is not proof.
2. **Verification over guesswork:** Important claims should be grounded in available evidence.
3. **Uncertainty is an acceptable outcome:** The system must be able to say that it cannot establish a conclusion.
4. **Safety over automation:** The application should help users act carefully, not take consequential actions without authorization.
5. **Privacy by design:** Sensitive information should be minimized, protected and handled transparently.
6. **Evaluation over anecdotes:** Claims of effectiveness should be supported by reproducible testing.
7. **Accessibility:** The product should eventually accommodate different levels of technical literacy and relevant regional languages.
8. **Honest reporting:** Limitations, failures and false positives must be documented alongside successful results.

## 12. Intended Deliverables

The intended project deliverables are:

- An open-source ScamLens AI codebase.
- A functional prototype that accepts supported forms of suspicious evidence.
- An investigation experience that returns an explainable verdict and recommended next steps.
- A documented dataset and evaluation methodology.
- A reproducible benchmark and baseline results.
- A demonstration interface suitable for a future mobile application.
- Technical documentation covering limitations, privacy, evaluation and known failure cases.

## 13. Definition of Success

ScamLens AI will be considered a successful initial research prototype when a user can submit suspicious content, receive a reasoned assessment grounded in identifiable evidence, understand what remains uncertain and obtain appropriate next-step guidance.

Beyond the prototype, the project's success should be measured by its ability to distinguish scams from legitimate communications, avoid unsupported accusations, handle ambiguous cases responsibly and demonstrate reproducible improvements on an independently held-out evaluation set.

The longer-term goal is to make ScamLens AI useful to consumers while contributing an open and measurable approach to evaluating AI-driven scam investigation.

---

**Project summary**

ScamLens AI is an open-source, multimodal scam investigation assistant that combines evidence analysis, external verification and AI-driven reasoning to help people assess suspicious communications and take safer next steps. Its defining contribution is not just scam classification, but evidence-backed investigation with explicit uncertainty and reproducible evaluation.

---

## 14. Technical Architecture & Quick Start

### A. Repository Structure

```text
ScamLens-AI/
├── src/
│   ├── scamlens/
│   │   ├── ai/               # AI clients (custom endpoint, Groq, Ollama), catalog prompts, tool schemas
│   │   ├── api/              # FastAPI REST endpoints (/investigate, /health)
│   │   ├── core/             # Configuration, Pydantic/dataclass models, custom exceptions
│   │   ├── extractors/       # Forensic extractors (email, url, text, qr, vision, privacy PII)
│   │   ├── intelligence/     # Threat intel connectors (VirusTotal, Google Safe Browsing, mock intel)
│   │   ├── investigator/     # ScamInvestigator engine, multi-evidence scorer, action recommender
│   │   └── rag/              # Domain knowledge base & Indian trusted entities catalog
│   └── data_generate_dummy/  # Offline benchmark generation scripts (1.eml ... 20.eml, JSON, MD)
├── data/
│   ├── raw_emails/           # Local numbered RFC 5322 MIME files (1.eml ... 20.eml - git-ignored)
│   ├── spam-indian-bank-emails.json  # Full Gmail REST API JSON format (20 benchmark emails)
│   └── spam-indian-bank-emails.md    # Raw RFC 5322 MIME email blocks
├── claude/
│   └── agentic-ai-plan.md    # v3.0.0 Architecture Blueprint (Cyclic ReAct & Multi-Agent)
├── tests/                    # 30 passing unit tests (extractors, investigator, models, readers)
├── SETUP.md                  # Comprehensive local development and environment setup guide
├── pyproject.toml            # Project packaging & dependency groups ([dev], [ai], [gmail], [agentic])
└── requirements.txt          # Frozen development dependencies
```

### B. Email Forensics & Offline PoC Pipeline

ScamLens-AI features unified email analysis designed for both offline PoC development and live inbox scanning:

- **Offline Local Reader (`LocalEmailReader`)**: Read from `data/raw_emails/1.eml` ... `20.eml`, `data/spam-indian-bank-emails.json`, or `.md` files without Google Cloud credentials or network calls.
- **Live Gmail REST API (`GmailReader`)**: Connects to user inboxes using OAuth 2.0 with read-only permissions (`https://www.googleapis.com/auth/gmail.readonly`).
- **Forensic Checks Extracted**:
  - Sender vs. Reply-To domain spoofing detection
  - RFC 5322 authentication records (`SPF`, `DKIM`, `DMARC`)
  - Malicious / phishing URL harvesting
  - Dangerous attachment detection (`.exe`, `.iso`, `.apk`, macro-enabled files)

```python
from scamlens.extractors.email import LocalEmailReader, extract_email_evidence
from scamlens.investigator.engine import ScamInvestigator

# 1. Load local emails (exact 1..20 numerical order)
reader = LocalEmailReader("data/raw_emails")
emails = reader.fetch_messages()

# 2. Analyze first email
first_email = emails[0]
print(f"Subject: {first_email.subject} | From: {first_email.sender_email}")
print(f"SPF: {first_email.spf_status} | URLs: {len(first_email.extracted_urls)}")

# 3. Investigate through multi-evidence engine
investigator = ScamInvestigator()
result = investigator.investigate_email(first_email)
print(f"Verdict: {result.verdict.value} | Risk Score: {result.risk_score}/100")
```

### C. Agentic AI & LangGraph State Machine

ScamLens-AI supports next-generation autonomous investigation architectures:
- **Plan A (Hierarchical Multi-Agent)**: A supervisor agent orchestrates specialized subagents (Email Forensics, URL Intel, Content Triage, Evidence Synthesizer).
- **Plan B (Cyclic ReAct State Machine)**: A stateful ReAct cycle with iterative tool calling, uncertainty reduction, and maximum iteration termination safeguards.
- **Plan C (Unified Hybrid Engine)**: Dynamically selects Plan B for fast single email triage and Plan A for complex, multi-evidence incidents.

*Full blueprints, state graphs, and tool availability matrices are documented in [claude/agentic-ai-plan.md](claude/agentic-ai-plan.md).*

### D. Quick Installation & Running Tests

```bash
# 1. Create and activate virtual environment
python3 -m venv .venv
source .venv/bin/activate

# 2. Install dependencies (including agentic AI extras)
pip install -e ".[dev,ai,gmail,agentic]"

# 3. Configure environment
cp .env.example .env

# 4. Run full unit test suite (30 passing tests)
python3 -m unittest discover tests
```

*For complete step-by-step instructions on setting up custom AI endpoints, Groq, Ollama, CLI scanners, and FastAPI service, see [SETUP.md](SETUP.md).*
