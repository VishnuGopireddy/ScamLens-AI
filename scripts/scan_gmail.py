#!/usr/bin/env python3
"""CLI utility to scan and investigate Gmail messages for scams and phishing using ScamLens-AI.

Usage:
  # Scan recent unread messages
  python scripts/scan_gmail.py --query "is:unread" --max-results 5

  # Scan with live verbose process logging (Claude/Antigravity style)
  python scripts/scan_gmail.py --max-results 1 --v

  # Scan a specific message by Gmail ID
  python scripts/scan_gmail.py --msg-id 18cb12345678abcd

  # Output in JSON format
  python scripts/scan_gmail.py --query "label:SPAM" --json
"""

from __future__ import annotations

import argparse
import contextlib
import json
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

# Add project root to sys.path
_PROJECT_ROOT = Path(__file__).resolve().parent.parent
_SRC_DIR = _PROJECT_ROOT / "src"
if str(_SRC_DIR) not in sys.path:
    sys.path.insert(0, str(_SRC_DIR))

from scamlens.cli_live import LiveProgressDisplay
from scamlens.core.models import IncidentStage, InvestigationResult
from scamlens.extractors.email import EmailMessage, GmailAuthManager, GmailReader
from scamlens.investigator.engine import ScamInvestigator


def _format_llm_summary_line(llm_events: List[Dict[str, Any]]) -> Optional[str]:
    """Summarize LLM calls recorded during an email investigation."""
    if not llm_events:
        return None
    total_ms = sum(
        float(ev.get("data", {}).get("latency_ms", 0.0) or 0.0) for ev in llm_events
    )
    total_tokens = sum(
        int((ev.get("data", {}).get("usage") or {}).get("total_tokens") or 0)
        for ev in llm_events
    )
    models = []
    for ev in llm_events:
        d = ev.get("data", {})
        label = f"{d.get('provider', 'ai')}/{d.get('model', 'default')}"
        if label not in models:
            models.append(label)
    tok_part = f", {total_tokens} tokens" if total_tokens > 0 else ""
    return f"{len(llm_events)} call(s) [{', '.join(models)}] in {total_ms / 1000.0:.2f}s{tok_part}"


def _format_report_lines(
    idx: int,
    total: int,
    msg: EmailMessage,
    result: InvestigationResult,
    llm_events: Optional[List[Dict[str, Any]]] = None,
) -> List[str]:
    """Build standard human-readable investigation report lines."""
    lines = [
        "=" * 70,
        f"[{idx}/{total}] Email Subject: {msg.subject}",
        f"From:        {msg.sender}",
        f"Date:        {msg.date}",
    ]
    if msg.reply_to:
        lines.append(f"Reply-To:    {msg.reply_to}")
    lines.extend(
        [
            f"SPF:         {msg.spf_status.upper()} | DKIM: {msg.dkim_status.upper()} | DMARC: {msg.dmarc_status.upper()}",
            "-" * 70,
            f"Verdict:     {result.verdict.value}",
            f"Risk Score:  {result.risk_score} / 100",
            f"Confidence:  {int(result.confidence * 100)}%",
        ]
    )
    llm_summary = _format_llm_summary_line(llm_events or [])
    if llm_summary:
        lines.append(f"LLM Calls:   {llm_summary}")
    lines.append(f"Summary:     {result.summary}")
    if result.evidence_findings:
        lines.append("\nEvidence Findings:")
        for item in result.evidence_findings:
            lines.append(
                f" - [{item.severity.value}] ({item.category.value}) {item.summary}"
            )
    if result.recommended_actions:
        lines.append("\nRecommended Next Steps:")
        for action in result.recommended_actions:
            lines.append(f" * {action}")
    lines.append("=" * 70 + "\n")
    return lines


def _print_report(
    idx: int,
    total: int,
    msg: EmailMessage,
    result: InvestigationResult,
    display: Optional[LiveProgressDisplay] = None,
    llm_events: Optional[List[Dict[str, Any]]] = None,
) -> None:
    report_text = "\n".join(
        _format_report_lines(idx, total, msg, result, llm_events=llm_events)
    )
    if display is not None:
        display.print_text(report_text)
    else:
        print(report_text)


def build_arg_parser() -> argparse.ArgumentParser:
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
    parser.add_argument(
        "--strategy",
        "--agent-architecture",
        dest="strategy",
        choices=["orchestrator"],
        default="orchestrator",
        help="Investigation execution strategy (default: Phase 1 'orchestrator')",
    )
    parser.add_argument(
        "-v",
        "--v",
        "--verbose",
        dest="verbose",
        action="store_true",
        help="Show live verbose process logging (real-time steps, tool calls, and timings)",
    )
    return parser


def main(argv: Optional[List[str]] = None) -> None:
    parser = build_arg_parser()
    args = parser.parse_args(argv)

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

    display: Optional[LiveProgressDisplay] = (
        LiveProgressDisplay(stderr=bool(args.json)) if args.verbose else None
    )
    ctx: Any = display if display is not None else contextlib.nullcontext()

    all_results: List[dict[str, Any]] = []
    with ctx:
        if display is not None:
            ai_provider = investigator.settings.default_ai_provider
            ai_model = getattr(investigator.ai, "model", "default")
            intel_mode = (
                "Simulated Mock"
                if investigator.settings.use_mock_intelligence
                else "Live (ICANN RDAP / VirusTotal)"
            )
            target_desc = (
                f"Message ID: {args.msg_id}"
                if args.msg_id
                else f"Query: '{args.query}' (max: {args.max_results})"
            )
            display.print_header(
                "ScamLens-AI Live Process",
                [
                    f"Target: {target_desc}  |  Strategy: {args.strategy}  |  Stage: {stage.value}",
                    f"AI Engine: {ai_provider} ({ai_model})  |  Threat Intel: {intel_mode}",
                ],
            )
            display.begin_step("gmail_auth", "Authenticating Gmail OAuth2 session...")
            try:
                _ = reader.service
            except Exception as exc:
                display.complete_step(f"Gmail authentication failed: {exc}", status="error")
                sys.exit(1)
            display.complete_step("Gmail API session ready")

        # Resolve target message IDs
        target_ids: List[str] = []
        if args.msg_id:
            target_ids = [args.msg_id]
        else:
            if display is not None:
                display.begin_step(
                    "gmail_search",
                    f"Searching Gmail with query: '{args.query}' (max: {args.max_results})...",
                )
            else:
                print(
                    f"Searching Gmail with query: '{args.query}' (max: {args.max_results})..."
                )
            try:
                summaries = reader.list_message_summaries(
                    query=args.query, max_results=args.max_results
                )
            except Exception as exc:
                if display is not None:
                    display.complete_step(f"Failed to search Gmail: {exc}", status="error")
                else:
                    print(f"[Error] Failed to fetch messages: {exc}", file=sys.stderr)
                sys.exit(1)

            target_ids = [item["id"] for item in summaries if item.get("id")]
            if display is not None:
                if target_ids:
                    display.complete_step(
                        f"Found {len(target_ids)} Gmail message(s) matching '{args.query}'",
                        status="ok",
                    )
                else:
                    display.complete_step(
                        "No messages found matching query.",
                        status="warn",
                    )

        if not target_ids:
            if args.json:
                if not args.verbose:
                    print("No messages found matching query.", file=sys.stderr)
                print(json.dumps([]))
            elif not args.verbose:
                print("No messages found matching query.")
            return

        if display is None:
            if args.msg_id:
                print(f"Fetching message ID: {args.msg_id}...")
            else:
                print(
                    f"Found {len(target_ids)} message(s). Beginning ScamLens analysis...\n"
                )

        total = len(target_ids)
        for idx, msg_id in enumerate(target_ids, start=1):
            if display is not None:
                display.begin_step(
                    "reading_email",
                    f"[{idx}/{total}] Fetching & parsing Gmail message {msg_id}...",
                )
            try:
                msg = reader.get_message(msg_id)
            except Exception as exc:
                if display is not None:
                    display.complete_step(
                        f"[{idx}/{total}] Failed to fetch message {msg_id}: {exc}",
                        status="error",
                    )
                else:
                    print(
                        f"[Error] Failed to fetch message {msg_id}: {exc}",
                        file=sys.stderr,
                    )
                if args.msg_id:
                    sys.exit(1)
                continue

            if display is not None:
                display.log_email_loaded(idx, total, msg)

            llm_events: List[Dict[str, Any]] = []

            def _on_progress(ev: Dict[str, Any]) -> None:
                if ev.get("stage") in ("llm_call_done", "image_analyzed"):
                    llm_events.append(ev)
                if display is not None:
                    display.handle_event(ev)

            result = investigator.investigate_email(
                msg,
                incident_stage=stage,
                strategy=args.strategy,
                on_progress=_on_progress,
            )
            payload = {
                "email_id": msg.id,
                "subject": msg.subject,
                "sender": msg.sender,
                "date": msg.date,
                "strategy": args.strategy,
                "investigation": result.to_dict(),
            }
            all_results.append(payload)

            if not args.json:
                _print_report(
                    idx,
                    total,
                    msg,
                    result,
                    display=display,
                    llm_events=llm_events,
                )

        if display is not None:
            display.print_footer(len(all_results))

    if args.json:
        print(json.dumps(all_results, indent=2))


if __name__ == "__main__":
    main()
