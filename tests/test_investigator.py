"""Test investigation engine and scoring."""

import json
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

_SRC = Path(__file__).resolve().parent.parent / "src"
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

from scamlens.ai.openai_compat import OpenAICompatibleClient
from scamlens.api.routes.investigate import handle_investigate_request
from scamlens.core.exceptions import ModelInferenceError
from scamlens.core.models import (
    IncidentStage,
    InvestigationSubmission,
    VerdictEnum,
)
from scamlens.extractors.email import parse_raw_email
from scamlens.investigator.engine import ScamInvestigator


class TestInvestigator(unittest.TestCase):
    def setUp(self):
        self.investigator = ScamInvestigator()

    def test_benign_submission(self):
        submission = InvestigationSubmission(
            text="Hello, here is the meeting notes link https://docs.google.com for today.",
            urls=["https://docs.google.com"],
            incident_stage=IncidentStage.PRE_ACTION,
        )
        result = self.investigator.investigate(submission)
        self.assertEqual(result.verdict, VerdictEnum.NO_CLEAR_INDICATORS)
        self.assertLess(result.risk_score, 40)

    def test_phishing_submission(self):
        submission = InvestigationSubmission(
            text="Dear customer, your bank account blocked within 24 hours. Click http://hdfc-update.xyz to complete KYC immediately.",
            urls=["http://hdfc-update.xyz"],
            incident_stage=IncidentStage.PRE_ACTION,
        )
        result = self.investigator.investigate(submission)
        self.assertIn(result.verdict, (VerdictEnum.LIKELY_SCAM, VerdictEnum.SUSPICIOUS))
        self.assertGreaterEqual(result.risk_score, 50)
        self.assertGreater(len(result.recommended_actions), 0)

    def test_post_harm_emergency_guidance(self):
        submission = InvestigationSubmission(
            text="I transferred Rs 5000 to fraudster",
            incident_stage=IncidentStage.POST_ACTION,
        )
        result = self.investigator.investigate(submission)
        self.assertTrue(any("1930" in act or "bank" in act.lower() for act in result.recommended_actions))

    def test_invalid_strategy_raises(self):
        submission = InvestigationSubmission(text="hello")
        with self.assertRaises(ValueError):
            self.investigator.investigate(submission, strategy="unknown_strategy")

    @patch.object(OpenAICompatibleClient, "chat_completion")
    def test_orchestrator_strategy_redacts_pii_and_scores_deterministically(self, mock_chat):
        captured_prompts = []

        def _fake_chat(messages, tools=None, **kwargs):
            captured_prompts.append(messages)
            if tools is not None:
                return {
                    "choices": [{
                        "message": {
                            "role": "assistant",
                            "content": None,
                            "tool_calls": [
                                {
                                    "id": "call_url",
                                    "type": "function",
                                    "function": {
                                        "name": "analyze_url_structure",
                                        "arguments": json.dumps({"url": "http://hdfc-pan-update.online/auth/login"}),
                                    },
                                },
                                {
                                    "id": "call_text",
                                    "type": "function",
                                    "function": {
                                        "name": "extract_text_indicators",
                                        "arguments": json.dumps({
                                            "text": "Immediate debit freeze at 23:59. Enter Customer ID and NetBanking IPIN."
                                        }),
                                    },
                                },
                            ],
                        }
                    }]
                }
            return {
                "choices": [{
                    "message": {
                        "role": "assistant",
                        "content": "Correlated Report: Credential harvesting phishing impersonating HDFC Bank.",
                        "tool_calls": None,
                    }
                }]
            }

        mock_chat.side_effect = _fake_chat

        inv = ScamInvestigator()
        inv.ai = OpenAICompatibleClient(api_key="test_key", provider="groq")
        submission = InvestigationSubmission(
            text=(
                "HDFC Bank alert: Immediate debit freeze at 23:59! "
                "Visit http://hdfc-pan-update.online/auth/login with OTP: 998877 and call +91 9123456789."
            ),
            urls=["http://hdfc-pan-update.online/auth/login"],
        )
        result = inv.investigate(submission, strategy="orchestrator")

        # Sensitive OTP & raw mobile number must be redacted before reaching the LLM
        user_msg_sent = captured_prompts[0][1]["content"]
        self.assertNotIn("998877", user_msg_sent)
        self.assertNotIn("9123456789", user_msg_sent)
        self.assertIn("[REDACTED_OTP]", user_msg_sent)
        self.assertIn("[REDACTED_PHONE]", user_msg_sent)

        self.assertEqual(result.verdict, VerdictEnum.LIKELY_SCAM)
        self.assertGreaterEqual(result.risk_score, 70)
        self.assertIn("Correlated Report:", result.summary)
        self.assertTrue(any(p.get("strategy") == "orchestrator_phase1" for p in result.provenance))

    @patch.object(OpenAICompatibleClient, "chat_completion")
    def test_orchestrator_fallback_when_llm_unreachable(self, mock_chat):
        mock_chat.side_effect = ModelInferenceError("Endpoint unreachable")

        inv = ScamInvestigator()
        inv.ai = OpenAICompatibleClient(api_key="test_key", provider="custom")
        submission = InvestigationSubmission(
            text="Your SBI account blocked within 24 hours. Click http://sbi-update.xyz/login",
            urls=["http://sbi-update.xyz/login"],
        )
        result = inv.investigate(submission, strategy="orchestrator")
        self.assertIn(result.verdict, (VerdictEnum.LIKELY_SCAM, VerdictEnum.SUSPICIOUS))
        self.assertTrue(any(p.get("strategy") == "orchestrator_fallback_to_linear" for p in result.provenance))

    @patch.object(OpenAICompatibleClient, "chat_completion")
    def test_investigate_email_orchestrator_on_hdfc_eml(self, mock_chat):
        eml_path = Path("data/raw_emails/8.eml")
        if not eml_path.is_file():
            self.skipTest("data/raw_emails/8.eml not present")

        msg = parse_raw_email(eml_path.read_bytes(), msg_id="8")

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
                                    "name": "inspect_email_authentication",
                                    "arguments": json.dumps({
                                        "from_addr": msg.sender,
                                        "reply_to": msg.reply_to or "",
                                        "spf": msg.spf_status,
                                        "dkim": msg.dkim_status,
                                        "dmarc": msg.dmarc_status,
                                    }),
                                },
                            },
                            {
                                "id": "c2",
                                "type": "function",
                                "function": {
                                    "name": "analyze_url_structure",
                                    "arguments": json.dumps({"url": "http://hdfc-pan-update.online/auth/login"}),
                                },
                            },
                            {
                                "id": "c3",
                                "type": "function",
                                "function": {
                                    "name": "verify_brand_official_domain",
                                    "arguments": json.dumps({"brand": "hdfc", "domain": "hdfc-pan-update.online"}),
                                },
                            },
                            {
                                "id": "c4",
                                "type": "function",
                                "function": {
                                    "name": "extract_text_indicators",
                                    "arguments": json.dumps({"text": msg.body_plain}),
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
                        "content": "HDFC PAN phishing confirmed across auth, URL, and urgency vectors.",
                        "tool_calls": None,
                    }
                }]
            },
        ]

        inv = ScamInvestigator()
        inv.ai = OpenAICompatibleClient(api_key="test_key", provider="groq")
        result = inv.investigate_email(msg, strategy="orchestrator")

        self.assertEqual(result.verdict, VerdictEnum.LIKELY_SCAM)
        sources = [e.source for e in result.evidence_findings]
        # Verify SPF failure wasn't double-counted when both pre-check and tool ran
        self.assertEqual(sources.count("email_headers_spf"), 1)
        self.assertIn("url_path_heuristic", sources)
        self.assertIn("brand_registry", sources)
        self.assertIn("contact_heuristic", sources)

    def test_api_handle_investigate_request_strategy_validation(self):
        res = handle_investigate_request(
            {"text": "Hello team, meeting at 3pm."},
            strategy="linear",
        )
        self.assertEqual(res["verdict"], VerdictEnum.NO_CLEAR_INDICATORS.value)

        with self.assertRaises(ValueError):
            handle_investigate_request({"text": "Hello"}, strategy="bogus")

    def test_benign_marketing_email_with_tracking_base64_urls_not_flagged_as_scam(self):
        from scamlens.extractors.email import EmailMessage

        msg = EmailMessage(
            id="grammarly_marketing",
            thread_id="t_g1",
            subject="Get Grammarly Plus today",
            sender="Grammarly <hello@mail.grammarly.com>",
            sender_name="Grammarly",
            sender_email="hello@mail.grammarly.com",
            sender_domain="mail.grammarly.com",
            spf_status="pass",
            dkim_status="pass",
            dmarc_status="pass",
            body_cleaned="Grammarly Get Plus today, and feel more confident in your written communication.",
            extracted_urls=[
                "http://grammarly.com/",
                "https://www.grammarly.com/upgrade/plus",
                "https://click.grammarly.com/s/c/9mihnDwOdzlpym4mGWCQo6J6WyERI0V0CsNw4sD-CVu-x9WoCkCNnfhw9x3vUuo_PR2myVblMTNyOYecoidPqTj-JBFgJGInN3sZoVwe9_ND4a5ufBrbxiHrgAn6oMlIaxMixzVHTCJIBvAF-3KSH07l2FvXyzVuKehbSNefOkKOXfDs4hdXKA6Ks0-RjdP54FAhRYyrlP-PHt1ilB1XsyaGUJRW3iVDKtRsBkdQZqLyGbyuoOtKN6Jc-v7ijP-UciY8Dnj_8wL9S4uy_0G6aH06psNTvgARDWUD5noXfh5g80-yl40RTk6jFTJ2inge3pb69hg4b5b5tfkL8UFvXY-DEEA6IGpQj3PXP-c3UIAlw2Xds27cu3iER-KWEkvuvX2f2fxcNj8MnzRSUTc2QoUG6rztYwUPw_rAjM0PfSK4-zvX5VNae-XjDEdW_hhRRDNDyrxGM9eStOArGEfCFPtE_7o_wfnPEYln3erxyLkYnCJieoyN8fLi734RKTcK5GNv6z2L2kRzkcIhjFCXsIXeoLIfTMSYNjD1R08Q83CW0XYF6tu50gqA1oQz7o8xUSq_uWdU_F-Rt5v0A5bv9-ZoxwQOxYOPm9Sliw/U4xe20QUaRYkn2EcehcfV8e1-LM8x0QI/26",
            ],
        )
        res = self.investigator.investigate_email(msg, strategy="linear")
        self.assertEqual(res.verdict, VerdictEnum.NO_CLEAR_INDICATORS)
        self.assertLess(res.risk_score, 35)


if __name__ == "__main__":
    unittest.main()
