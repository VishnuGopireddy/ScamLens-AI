# ScamLens-AI Evaluation Benchmark

This module implements the evaluation strategy outlined in **Section 9 & 10 of README.md**.

## Purpose
Rather than measuring simple binary classification accuracy, the benchmark measures:
1. **Scam Classification**: Precision, recall, macro F1, and false-positive rate on benign communications.
2. **Evidence Extraction**: Identification of suspicious claims, URLs, brand impersonation, and QR payloads.
3. **Evidence Grounding**: Attribution of findings to verified external sources vs inferences.
4. **Decision Quality & Uncertainty**: Calibrated risk scores, identification of contradictions, and appropriate abstention (`Insufficient evidence`).
5. **Action Safety**: Quality and urgency of recommendations, especially for pre-action vs post-harm scenarios.

## Dataset Structure
Evaluation scenarios are stored under `benchmark/datasets/`:
- `sample_cases.json`: Seed scenarios including benign, phishing, QR code fraud, and borderline cases.

## Running the Benchmark
```bash
python3 benchmark/runner.py
```

