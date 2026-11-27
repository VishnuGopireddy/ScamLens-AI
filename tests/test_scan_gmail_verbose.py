"""Tests for live verbose CLI process logging (--v) in scripts/scan_gmail.py."""

from __future__ import annotations

import io
import json
import sys
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path
from unittest.mock import MagicMock, patch

_PROJECT_ROOT = Path(__file__).resolve().parent.parent
_SRC = _PROJECT_ROOT / "src"
_SCRIPTS = _PROJECT_ROOT / "scripts"
for p in (str(_SRC), str(_SCRIPTS)):
    if p not in sys.path:
        sys.path.insert(0, p)

import scan_gmail  # noqa: E402
from scamlens.ai.openai_compat import OpenAICompatibleClient  # noqa: E402
from scamlens.cli_live import LiveProgressDisplay  # noqa: E402
from scamlens.extractors.email import EmailMessage  # noqa: E402
from scamlens.investigator.engine import ScamInvestigator  # noqa: E402


def _sample_email() -> EmailMessage:
    return EmailMessage(
        id="msg_test_001",
        thread_id="thread_test_001",
        subject="Urgent: HDFC PAN KYC Update Required",
        sender="HDFC Alerts <alert@hdfc-pan-update.online>",
        sender_name="HDFC Alerts",
        sender_email="alert@hdfc-pan-update.online",
        sender_domain="hdfc-pan-update.online",
        date="Thu, 26 Nov 2026 10:00:00 +0000",
        spf_status="fail",
        dkim_status="fail",
        dmarc_status="fail",
        body_cleaned="Immediate debit freeze within 24 hours! Verify OTP at http://hdfc-pan-update.online/auth/login",
        extracted_urls=["http://hdfc-pan-update.online/auth/login"],
    )


class TestScanGmailVerbose(unittest.TestCase):
    def test_arg_parser_supports_v_flags(self) -> None:
        parser = scan_gmail.build_arg_parser()
        for flag in ("-v", "--v", "--verbose"):
            args = parser.parse_args(["--max-results", "1", flag])
            self.assertEqual(args.max_results, 1)
            self.assertTrue(args.verbose, f"Expected verbose=True for {flag}")

        default_args = parser.parse_args(["--max-results", "1"])
        self.assertFalse(default_args.verbose)

    def test_live_display_renders_linear_and_orchestrator_events(self) -> None:
        buf = io.StringIO()
        display = LiveProgressDisplay(stderr=False)
        display.console.file = buf

        with display:
            display.print_header("ScamLens-AI Live Process", ["Target: test", "Strategy: orchestrator"])
            display.begin_step("gmail_auth", "Authenticating Gmail OAuth2 session...")
            display.complete_step("Gmail API session ready")
            display.log_email_loaded(1, 1, _sample_email())

            display.handle_event({
                "stage": "orchestrator_start",
                "message": "Launching Phase 1 AI Orchestrator...",
            })
            display.handle_event({
                "stage": "orchestrator_turn",
                "message": "AI Orchestrator turn 1/2: selecting forensic tools...",
            })
            display.handle_event({
                "stage": "orchestrator_tools_dispatched",
                "message": "Dispatching 2 tool(s): analyze_url_structure, extract_text_indicators",
            })
            display.handle_event({
                "stage": "orchestrator_tool_done",
                "message": "Tool 'analyze_url_structure' completed (4.2 ms, 2 indicator(s))",
                "data": {
                    "tool": "analyze_url_structure",
                    "arguments": {"url": "http://hdfc-pan-update.online/auth/login"},
                    "findings_summary": ["Credential harvesting risk"],
                },
            })
            display.handle_event({
                "stage": "scoring",
                "message": "Correlating 3 unique evidence item(s)...",
            })
            display.handle_event({
                "stage": "completed",
                "message": "Investigation complete — Likely Scam (Risk Score: 85/100)",
                "data": {"verdict": "Likely Scam", "risk_score": 85},
            })
            display.print_footer(1)

        output = buf.getvalue()
        self.assertIn("ScamLens-AI Live Process", output)
        self.assertIn("Gmail API session ready", output)
        self.assertIn("Urgent: HDFC PAN KYC Update Required", output)
        self.assertIn("Dispatching 2 tool(s)", output)
        self.assertIn("analyze_url_structure", output)
        self.assertIn("Credential harvesting risk", output)
        self.assertIn("Investigation complete", output)
        self.assertIn("Live process finished: 1 email(s) scanned", output)

    @patch("scan_gmail.GmailReader")
    @patch("scan_gmail.GmailAuthManager")
    def test_scan_gmail_main_with_v_flag_streams_live_process(
        self, _mock_auth_cls: MagicMock, mock_reader_cls: MagicMock
    ) -> None:
        mock_reader = MagicMock()
        mock_reader.service = MagicMock()
        mock_reader.list_message_summaries.return_value = [{"id": "msg_test_001"}]
        mock_reader.get_message.return_value = _sample_email()
        mock_reader_cls.return_value = mock_reader

        stdout_buf = io.StringIO()
        stderr_buf = io.StringIO()
        with redirect_stdout(stdout_buf), redirect_stderr(stderr_buf):
            scan_gmail.main(["--max-results", "1", "--v"])

        out = stdout_buf.getvalue()
        self.assertEqual(stderr_buf.getvalue(), "")
        self.assertIn("ScamLens-AI Live Process", out)
        self.assertIn("Gmail API session ready", out)
        self.assertIn("Email parsed:", out)
        self.assertIn("Inspecting email headers & authentication", out)
        self.assertIn("Analyzing URL (1/1):", out)
        self.assertIn("Investigation complete", out)
        self.assertIn("Verdict:", out)
        self.assertIn("Live process finished: 1 email(s) scanned", out)

    @patch("scan_gmail.GmailReader")
    @patch("scan_gmail.GmailAuthManager")
    def test_scan_gmail_main_with_v_and_json_keeps_stdout_valid_json(
        self, _mock_auth_cls: MagicMock, mock_reader_cls: MagicMock
    ) -> None:
        mock_reader = MagicMock()
        mock_reader.service = MagicMock()
        mock_reader.list_message_summaries.return_value = [{"id": "msg_test_001"}]
        mock_reader.get_message.return_value = _sample_email()
        mock_reader_cls.return_value = mock_reader

        stdout_buf = io.StringIO()
        stderr_buf = io.StringIO()
        with redirect_stdout(stdout_buf), redirect_stderr(stderr_buf):
            scan_gmail.main(["--max-results", "1", "--v", "--json"])

        parsed = json.loads(stdout_buf.getvalue())
        self.assertEqual(len(parsed), 1)
        self.assertEqual(parsed[0]["email_id"], "msg_test_001")
        err = stderr_buf.getvalue()
        self.assertIn("ScamLens-AI Live Process", err)
        self.assertIn("Investigation complete", err)

    @patch("scan_gmail.GmailReader")
    @patch("scan_gmail.GmailAuthManager")
    def test_scan_gmail_with_v_handles_rich_markup_brackets_in_subject(
        self, _mock_auth_cls: MagicMock, mock_reader_cls: MagicMock
    ) -> None:
        tricky_msg = _sample_email()
        tricky_msg.subject = "[/broken] [EXTERNAL] Alert [tag=1]"
        mock_reader = MagicMock()
        mock_reader.service = MagicMock()
        mock_reader.list_message_summaries.return_value = [{"id": "msg_test_001"}]
        mock_reader.get_message.return_value = tricky_msg
        mock_reader_cls.return_value = mock_reader

        stdout_buf = io.StringIO()
        with redirect_stdout(stdout_buf):
            scan_gmail.main(["--max-results", "1", "--v"])

        out = stdout_buf.getvalue()
        self.assertIn("[/broken] [EXTERNAL] Alert [tag=1]", out)
        self.assertIn("[1/1] Email Subject:", out)
        self.assertIn("[HIGH]", out)

    @patch.object(OpenAICompatibleClient, "chat_completion")
    def test_parallel_orchestrator_emits_tool_findings_live(self, mock_chat: MagicMock) -> None:
        mock_chat.side_effect = [
            {
                "choices": [{
                    "message": {
                        "role": "assistant",
                        "content": None,
                        "tool_calls": [
                            {
                                "id": "c1",
                                "type": "function",
                                "function": {
                                    "name": "analyze_url_structure",
                                    "arguments": json.dumps({"url": "http://hdfc-pan-update.online/auth/login"}),
                                },
                            },
                            {
                                "id": "c2",
                                "type": "function",
                                "function": {
                                    "name": "extract_text_indicators",
                                    "arguments": json.dumps({"text": "Immediate debit freeze! Enter OTP."}),
                                },
                            },
                        ],
                    }
                }]
            },
            {
                "choices": [{
                    "message": {
                        "role": "assistant",
                        "content": "Phishing confirmed.",
                        "tool_calls": None,
                    }
                }]
            },
        ]

        inv = ScamInvestigator()
        inv.ai = OpenAICompatibleClient(api_key="test_key", provider="groq")
        events = []
        inv.investigate_email(_sample_email(), strategy="orchestrator", on_progress=events.append)

        tool_done_events = [e for e in events if e["stage"] == "orchestrator_tool_done"]
        self.assertEqual(len(tool_done_events), 2)
        self.assertTrue(all("findings_summary" in e.get("data", {}) for e in tool_done_events))

        llm_done_events = [e for e in events if e["stage"] == "llm_call_done"]
        self.assertEqual(len(llm_done_events), 2)
        self.assertEqual(llm_done_events[0]["data"]["tool_calls_count"], 2)
        self.assertEqual(llm_done_events[1]["data"]["tool_calls_count"], 0)

    @patch.object(OpenAICompatibleClient, "chat_completion")
    @patch("scan_gmail.GmailReader")
    @patch("scan_gmail.GmailAuthManager")
    def test_scan_gmail_orchestrator_highlights_llm_calls_and_tokens(
        self,
        _mock_auth_cls: MagicMock,
        mock_reader_cls: MagicMock,
        mock_chat: MagicMock,
    ) -> None:
        mock_reader = MagicMock()
        mock_reader.service = MagicMock()
        mock_reader.list_message_summaries.return_value = [{"id": "msg_test_001"}]
        mock_reader.get_message.return_value = _sample_email()
        mock_reader_cls.return_value = mock_reader

        mock_chat.side_effect = [
            {
                "model": "Qwen/Qwen3-8B",
                "usage": {"prompt_tokens": 500, "completion_tokens": 45, "total_tokens": 545},
                "choices": [{
                    "finish_reason": "tool_calls",
                    "message": {
                        "role": "assistant",
                        "content": None,
                        "tool_calls": [{
                            "id": "c1",
                            "type": "function",
                            "function": {
                                "name": "analyze_url_structure",
                                "arguments": json.dumps({"url": "http://hdfc-pan-update.online/auth/login"}),
                            },
                        }],
                    },
                }],
            },
            {
                "model": "Qwen/Qwen3-8B",
                "usage": {"prompt_tokens": 700, "completion_tokens": 120, "total_tokens": 820},
                "choices": [{
                    "finish_reason": "stop",
                    "message": {
                        "role": "assistant",
                        "content": "Phishing confirmed.",
                        "tool_calls": None,
                    },
                }],
            },
        ]

        stdout_buf = io.StringIO()
        with redirect_stdout(stdout_buf):
            scan_gmail.main(["--max-results", "1", "--strategy", "orchestrator", "--v"])

        out = stdout_buf.getvalue()
        self.assertIn("[LLM CALL #1]", out)
        self.assertIn("[LLM CALL #2]", out)
        self.assertIn("Tokens: in=500, out=45, total=545", out)
        self.assertIn("Tokens: in=700, out=120, total=820", out)
        self.assertIn("LLM Calls:   2 call(s)", out)
        self.assertIn("1365 tokens", out)
        self.assertIn("LLM Calls: 2", out)


if __name__ == "__main__":
    unittest.main()
