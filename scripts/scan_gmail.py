#!/usr/bin/env python3
"""CLI utility to scan and investigate Gmail messages for scams and phishing using ScamLens-AI.

Usage:
  # Scan recent unread messages
  python scripts/scan_gmail.py --query "is:unread" --max-results 5

  # Scan a specific message by Gmail ID
  python scripts/scan_gmail.py --msg-id 18cb12345678abcd

  # Output in JSON format
  python scripts/scan_gmail.py --query "label:SPAM" --json
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

# Add project root to sys.path
_PROJECT_ROOT = Path(__file__).resolve().parent.parent
_SRC_DIR = _PROJECT_ROOT / "src"
if str(_SRC_DIR) not in sys.path:
    sys.path.insert(0, str(_SRC_DIR))

from scamlens.core.models import IncidentStage
from scamlens.extractors.email import GmailAuthManager, GmailReader
from scamlens.investigator.engine import ScamInvestigator


def main() -> None:
    parser = argparse.ArgumentParser(
        description="ScamLens-AI: Scan and triage Gmail messages using Gmail REST API."
    )
    parser.add_argument(
        "--query",
        type=str,
        default="is:unread",
        help="Gmail search query (default: 'is:unread', e.g. 'from:unknown', 'label:SPAM')",
    )
    parser.add_argument(
        "--max-results",
        type=int,
        default=5,
        help="Maximum number of messages to scan (default: 5)",
    )
    parser.add_argument(
        "--msg-id",
        type=str,
        help="Specific Gmail message ID to inspect",
    )
    parser.add_argument(
        "--credentials",
        type=str,
        help="Path to Google Cloud credentials.json",
    )
    parser.add_argument(
        "--token",
        type=str,
        help="Path to cached token.json",
    )
    parser.add_argument(
        "--post-action",
        action="store_true",
        help="Mark incident as post-action (e.g. user already clicked link or entered details)",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Output full forensic investigation results in JSON",
    )

    args = parser.parse_args()

    auth_manager = GmailAuthManager(
        credentials_file=args.credentials,
        token_file=args.token,
    )

    try:
        reader = GmailReader(auth_manager=auth_manager)
    except (ImportError, FileNotFoundError) as exc:
        print(f"\n[Error] {exc}", file=sys.stderr)
        sys.exit(1)

    stage = IncidentStage.POST_ACTION if args.post_action else IncidentStage.PRE_ACTION
    investigator = ScamInvestigator()

    messages_to_scan = []
    if args.msg_id:
        try:
            print(f"Fetching message ID: {args.msg_id}...")
            msg = reader.get_message(args.msg_id)
            messages_to_scan.append(msg)
        except Exception as e:
            print(f"[Error] Failed to fetch message {args.msg_id}: {e}", file=sys.stderr)
            sys.exit(1)
    else:
        print(f"Searching Gmail with query: '{args.query}' (max: {args.max_results})...")
        try:
            messages_to_scan = reader.fetch_messages(
                query=args.query, max_results=args.max_results
            )
        except Exception as e:
            print(f"[Error] Failed to fetch messages: {e}", file=sys.stderr)
            sys.exit(1)

    if not messages_to_scan:
        print("No messages found matching query.")
        return

    print(f"Found {len(messages_to_scan)} message(s). Beginning ScamLens analysis...\n")

    all_results = []
    for idx, msg in enumerate(messages_to_scan, start=1):
        result = investigator.investigate_email(msg, incident_stage=stage)
        payload = {
            "email_id": msg.id,
            "subject": msg.subject,
            "sender": msg.sender,
            "date": msg.date,
            "investigation": result.to_dict(),
        }
        all_results.append(payload)

        if not args.json:
            print("=" * 70)
            print(f"[{idx}/{len(messages_to_scan)}] Email Subject: {msg.subject}")
            print(f"From:        {msg.sender}")
            print(f"Date:        {msg.date}")
            if msg.reply_to:
                print(f"Reply-To:    {msg.reply_to}")
            print(f"SPF:         {msg.spf_status.upper()} | DKIM: {msg.dkim_status.upper()} | DMARC: {msg.dmarc_status.upper()}")
            print("-" * 70)
            print(f"Verdict:     {result.verdict.value}")
            print(f"Risk Score:  {result.risk_score} / 100")
            print(f"Confidence:  {int(result.confidence * 100)}%")
            print(f"Summary:     {result.summary}")

            if result.evidence_findings:
                print("\nEvidence Findings:")
                for item in result.evidence_findings:
                    print(f" - [{item.severity.value}] ({item.category.value}) {item.summary}")

            if result.recommended_actions:
                print("\nRecommended Next Steps:")
                for action in result.recommended_actions:
                    print(f" * {action}")
            print("=" * 70 + "\n")

    if args.json:
        print(json.dumps(all_results, indent=2))


if __name__ == "__main__":
    main()
