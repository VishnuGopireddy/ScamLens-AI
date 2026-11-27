"""Command Line Interface for ScamLens-AI."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

# Enable direct script execution without installing wheel
_SRC_DIR = Path(__file__).resolve().parent.parent
if str(_SRC_DIR) not in sys.path:
    sys.path.insert(0, str(_SRC_DIR))

from scamlens import __version__
from scamlens.core.models import IncidentStage, InvestigationSubmission
from scamlens.investigator.engine import ScamInvestigator


def main() -> None:
    parser = argparse.ArgumentParser(
        description="ScamLens-AI: Multimodal Scam Detection, Investigation and Response"
    )
    parser.add_argument("--version", action="version", version=f"ScamLens-AI {__version__}")
    parser.add_argument("--gui", action="store_true", help="Launch the interactive Web GUI server")
    parser.add_argument("--host", default="127.0.0.1", help="GUI bind host (default: 127.0.0.1)")
    parser.add_argument("--port", type=int, default=8080, help="GUI bind port (default: 8080)")
    parser.add_argument("--text", type=str, help="Suspicious message or claim text")
    parser.add_argument("--url", type=str, help="Suspicious URL or link")
    parser.add_argument("--qr", type=str, help="Decoded QR code payload (e.g. UPI URI or URL)")
    parser.add_argument("--post-action", action="store_true", help="Flag if money/credentials were already transferred")
    parser.add_argument("--json", action="store_true", help="Output results in JSON format")

    args = parser.parse_args()

    if args.gui:
        from GUI.server import run_gui_server

        run_gui_server(host=args.host, port=args.port)
        return

    if not (args.text or args.url or args.qr):
        parser.print_help()
        sys.exit(1)

    stage = IncidentStage.POST_ACTION if args.post_action else IncidentStage.PRE_ACTION
    urls = [args.url] if args.url else []
    qr_payloads = [args.qr] if args.qr else []

    submission = InvestigationSubmission(
        text=args.text,
        urls=urls,
        qr_payloads=qr_payloads,
        incident_stage=stage,
    )

    investigator = ScamInvestigator()
    result = investigator.investigate(submission)

    if args.json:
        print(json.dumps(result.to_dict(), indent=2))
        return

    print("\n" + "=" * 60)
    print(f"ScamLens-AI Investigation Report")
    print("=" * 60)
    print(f"Verdict:        {result.verdict.value}")
    print(f"Risk Score:     {result.risk_score} / 100")
    print(f"Confidence:     {int(result.confidence * 100)}%")
    print(f"Summary:        {result.summary}")
    print("\nFindings:")
    for idx, item in enumerate(result.evidence_findings, 1):
        print(f"  {idx}. [{item.severity.value}] {item.summary} ({item.source})")
        if item.details:
            print(f"     -> {item.details}")

    if result.uncertainties:
        print("\nUncertainties / Limitations:")
        for unc in result.uncertainties:
            print(f"  - {unc}")

    print("\nRecommended Actions:")
    for act in result.recommended_actions:
        print(f"  * {act}")
    print("=" * 60 + "\n")


if __name__ == "__main__":
    main()
