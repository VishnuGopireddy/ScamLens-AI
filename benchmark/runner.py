"""Benchmark runner to evaluate ScamLens-AI against labelled scenarios.

Aligns with README §9 & §10.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

# Add src to sys.path so benchmark can run standalone
_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_ROOT / "src"))

from scamlens.core.models import IncidentStage, InvestigationSubmission
from scamlens.investigator.engine import ScamInvestigator


def run_benchmark() -> None:
    dataset_file = _ROOT / "benchmark" / "datasets" / "sample_cases.json"
    if not dataset_file.is_file():
        print(f"Dataset file not found: {dataset_file}")
        sys.exit(1)

    with open(dataset_file, "r", encoding="utf-8") as f:
        cases = json.load(f)

    investigator = ScamInvestigator()
    total = len(cases)
    passed = 0

    print("=" * 70)
    print(f"ScamLens-AI Evaluation Benchmark: Running {total} scenario(s)")
    print("=" * 70)

    for case in cases:
        case_id = case["id"]
        name = case["name"]
        sub_data = case["submission"]
        expected = case["expected"]

        stage = (
            IncidentStage.POST_ACTION
            if sub_data.get("incident_stage") == "POST_ACTION"
            else IncidentStage.PRE_ACTION
        )

        submission = InvestigationSubmission(
            text=sub_data.get("text"),
            urls=sub_data.get("urls", []),
            qr_payloads=sub_data.get("qr_payloads", []),
            incident_stage=stage,
        )

        result = investigator.investigate(submission)

        # Validate assertions
        verdict_ok = True
        if "verdict" in expected:
            verdict_ok = (result.verdict.value == expected["verdict"])

        score_ok = True
        if "min_risk_score" in expected:
            score_ok = score_ok and (result.risk_score >= expected["min_risk_score"])
        if "max_risk_score" in expected:
            score_ok = score_ok and (result.risk_score <= expected["max_risk_score"])

        post_harm_ok = True
        if expected.get("emergency_guidance_present"):
            post_harm_ok = any("1930" in act or "bank" in act.lower() for act in result.recommended_actions)

        is_success = verdict_ok and score_ok and post_harm_ok
        if is_success:
            passed += 1
            status_str = "[PASS]"
        else:
            status_str = "[FAIL]"

        print(f"{status_str} {case_id}: {name}")
        print(f"       Outcome: Verdict='{result.verdict.value}', RiskScore={result.risk_score}/100, Actions={len(result.recommended_actions)}")
        if not is_success:
            print(f"       Expected: {expected}")

    print("=" * 70)
    accuracy = (passed / total) * 100 if total > 0 else 0.0
    print(f"Summary: {passed}/{total} scenarios satisfied ({accuracy:.1f}%)")
    print("=" * 70)


if __name__ == "__main__":
    run_benchmark()

