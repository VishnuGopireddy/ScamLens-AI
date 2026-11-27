"""Tests for Universal OpenAI-Compatible client and tool calling engine."""

import json
import sys
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

_SRC = Path(__file__).resolve().parent.parent / "src"
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

from scamlens.ai.factory import get_ai_client
from scamlens.ai.openai_compat import OpenAICompatibleClient
from scamlens.ai.tools import SCAMLENS_TOOLS, ToolDispatcher
from scamlens.core.config import get_settings


class TestOpenAICompat(unittest.TestCase):
    def test_providers_initialization(self):
        settings = get_settings()
        # Test Groq preset
        groq_client = get_ai_client("groq")
        self.assertEqual(groq_client.base_url, "https://api.groq.com/openai/v1")
        self.assertEqual(groq_client.model, settings.groq_model)
        self.assertEqual(groq_client.vision_model, settings.groq_vision_model)

        # Test Ollama preset (local)
        ollama_client = get_ai_client("ollama")
        self.assertEqual(ollama_client.base_url, "http://localhost:11434/v1")

        # Test vLLM preset (self-hosted)
        vllm_client = get_ai_client("vllm")
        self.assertEqual(vllm_client.base_url, "http://localhost:8000/v1")

        # Test Gemini OpenAI-compatible endpoint
        gemini_client = get_ai_client("gemini")
        self.assertEqual(gemini_client.base_url, "https://generativelanguage.googleapis.com/v1beta/openai")

        # Test OpenAI preset
        openai_client = get_ai_client("openai")
        self.assertEqual(openai_client.base_url, "https://api.openai.com/v1")

    def test_mock_fallback_without_api_key(self):
        # Client without API key returns safe offline simulation
        client = OpenAICompatibleClient(api_key="", provider="groq")
        response = client.generate_text("Is this message suspicious?")
        self.assertIn("simulated groq", response.lower())

        json_resp = client.generate_json("Is this message suspicious?")
        self.assertIn("assessment", json_resp)

    @patch("urllib.request.urlopen")
    def test_live_api_call_formatting(self, mock_urlopen):
        mock_resp = MagicMock()
        mock_resp.read.return_value = json.dumps({
            "choices": [{
                "message": {
                    "content": '{"is_scam": true, "confidence": 0.95}'
                }
            }]
        }).encode("utf-8")
        mock_urlopen.return_value.__enter__.return_value = mock_resp

        client = OpenAICompatibleClient(api_key="gsk_test_key_123", provider="groq")
        res = client.generate_json("Check this URL: http://phish.xyz")
        self.assertTrue(res["is_scam"])
        self.assertEqual(res["confidence"], 0.95)

        # Verify request parameters
        call_args = mock_urlopen.call_args[0]
        req = call_args[0]
        self.assertEqual(req.get_header("Authorization"), "Bearer gsk_test_key_123")
        self.assertEqual(req.get_header("Content-type"), "application/json")

    def test_tool_definitions_schema(self):
        self.assertGreaterEqual(len(SCAMLENS_TOOLS), 4)
        for tool in SCAMLENS_TOOLS:
            self.assertEqual(tool["type"], "function")
            fn = tool["function"]
            self.assertIn("name", fn)
            self.assertIn("description", fn)
            self.assertIn("parameters", fn)
            self.assertEqual(fn["parameters"]["type"], "object")

    def test_tool_dispatcher_execution(self):
        dispatcher = ToolDispatcher()

        # 1. URL Analysis tool
        url_res = dispatcher.execute_tool("analyze_url_structure", {"url": "http://sbi-fake.xyz/login"})
        self.assertIn("findings", url_res)
        self.assertTrue(len(url_res["findings"]) > 0)

        # 2. Brand verification tool
        brand_res = dispatcher.execute_tool(
            "verify_brand_official_domain",
            {"brand": "sbi", "domain": "sbi-fake.xyz"}
        )
        self.assertIs(brand_res["is_official"], False)
        self.assertEqual(brand_res["cybercrime_helpline"], "1930")

        # 3. QR UPI decode tool
        qr_res = dispatcher.execute_tool(
            "decode_qr_payment",
            {"qr_payload": "upi://pay?pa=scammer@upi&pn=LuckyDraw&am=5000"}
        )
        self.assertIn("findings", qr_res)

        # 4. ICANN RDAP domain age tool
        rdap_res = dispatcher.execute_tool(
            "inspect_domain_whois_age",
            {"domain_or_url": "sbi-fake-login.xyz"}
        )
        self.assertIn("findings", rdap_res)
        self.assertTrue(len(rdap_res["findings"]) > 0)

        # 5. VirusTotal v3 reputation tool
        vt_res = dispatcher.execute_tool(
            "check_virustotal_reputation",
            {"url": "http://sbi-fake-login.xyz/update"}
        )
        self.assertIn("virustotal_findings", vt_res)
        self.assertTrue(len(vt_res["virustotal_findings"]) > 0)

        # 6. Text indicators tool (urgency & credentials)
        text_res = dispatcher.execute_tool(
            "extract_text_indicators",
            {"text": "Debit freeze at 23:59! Enter Customer ID and NetBanking IPIN immediately."}
        )
        self.assertIn("findings", text_res)
        self.assertTrue(text_res["has_urgency"])

        # 7. Email authentication tool (SPF, DKIM, DMARC, Sender Domain)
        auth_res = dispatcher.execute_tool(
            "inspect_email_authentication",
            {
                "from_addr": "HDFC Bank Compliance Unit <alert@hdfc-pan-update.online>",
                "reply_to": "support@hdfc-pan-update.online",
                "spf": "fail",
                "dkim": "fail",
                "dmarc": "fail",
            }
        )
        self.assertIn("auth_findings", auth_res)
        self.assertGreaterEqual(len(auth_res["auth_findings"]), 3)

        # 8. Contact details inspection tool
        contact_res = dispatcher.execute_tool(
            "inspect_contact_details",
            {
                "text": "Customer Safety Line: +91 9123456789\nGrievance: compliance@hdfc-pan-update.online",
                "claimed_brand": "HDFC Bank",
            }
        )
        self.assertIn("contact_findings", contact_res)
        self.assertGreaterEqual(len(contact_res["contact_findings"]), 2)

    @patch.object(OpenAICompatibleClient, "chat_completion")
    def test_agent_tool_loop(self, mock_chat):
        # Step 1: Model requests a tool call to check URL
        step1_response = {
            "choices": [{
                "message": {
                    "role": "assistant",
                    "content": None,
                    "tool_calls": [{
                        "id": "call_abc123",
                        "type": "function",
                        "function": {
                            "name": "verify_brand_official_domain",
                            "arguments": json.dumps({"brand": "sbi", "domain": "sbi-fake.xyz"}),
                        },
                    }],
                }
            }]
        }

        # Step 2: Model receives tool result and outputs final decision
        step2_response = {
            "choices": [{
                "message": {
                    "role": "assistant",
                    "content": "The domain sbi-fake.xyz does not match SBI's official domains. This is a phishing scam.",
                    "tool_calls": None,
                }
            }]
        }

        mock_chat.side_effect = [step1_response, step2_response]

        client = OpenAICompatibleClient(api_key="mock_key", provider="groq")
        dispatcher = ToolDispatcher()

        result = client.run_agent_loop(
            initial_prompt="Investigate this message claiming to be SBI from sbi-fake.xyz",
            system_prompt="You are a scam investigator.",
            dispatcher=dispatcher,
        )

        self.assertEqual(len(result["tool_history"]), 1)
        self.assertEqual(result["tool_history"][0]["tool"], "verify_brand_official_domain")
        self.assertFalse(result["tool_history"][0]["result"]["is_official"])
        self.assertIn("phishing scam", result["final_response"])
        self.assertGreaterEqual(len(result["evidence_items"]), 1)

    def test_tool_dispatcher_use_mock_config_and_evidence(self):
        # Explicit override works
        live_dispatcher = ToolDispatcher(use_mock=False)
        self.assertFalse(live_dispatcher.intel.use_mock)

        # Default reads Settings.use_mock_intelligence
        default_dispatcher = ToolDispatcher()
        self.assertEqual(default_dispatcher.intel.use_mock, get_settings().use_mock_intelligence)

        # execute_tool_with_evidence returns EvidenceItems uniformly
        res, evidence = default_dispatcher.execute_tool_with_evidence(
            "verify_brand_official_domain",
            {"brand": "hdfc", "domain": "hdfc-pan-update.online"},
        )
        self.assertFalse(res["is_official"])
        self.assertEqual(len(evidence), 1)
        self.assertEqual(evidence[0].source, "brand_registry")

    @patch.object(OpenAICompatibleClient, "chat_completion")
    def test_parallel_two_turn_orchestrator_loop(self, mock_chat):
        step1_response = {
            "choices": [{
                "message": {
                    "role": "assistant",
                    "content": None,
                    "tool_calls": [
                        {
                            "id": "call_1",
                            "type": "function",
                            "function": {
                                "name": "analyze_url_structure",
                                "arguments": json.dumps({"url": "http://hdfc-pan-update.online/auth/login"}),
                            },
                        },
                        {
                            "id": "call_2",
                            "type": "function",
                            "function": {
                                "name": "verify_brand_official_domain",
                                "arguments": json.dumps({"brand": "hdfc", "domain": "hdfc-pan-update.online"}),
                            },
                        },
                    ],
                }
            }]
        }
        step2_response = {
            "choices": [{
                "message": {
                    "role": "assistant",
                    "content": "Confirmed HDFC credential harvesting phishing attempt.",
                    "tool_calls": None,
                }
            }]
        }
        mock_chat.side_effect = [step1_response, step2_response]

        client = OpenAICompatibleClient(api_key="mock_key", provider="groq")
        result = client.run_agent_loop(
            initial_prompt="Investigate hdfc-pan-update.online/auth/login",
            system_prompt="Orchestrator",
            dispatcher=ToolDispatcher(use_mock=True),
            max_turns=2,
            parallel_tools=True,
        )

        self.assertEqual(len(result["tool_history"]), 2)
        self.assertEqual([h["tool"] for h in result["tool_history"]], [
            "analyze_url_structure",
            "verify_brand_official_domain",
        ])
        self.assertIn("execution_time_ms", result["tool_history"][0])
        self.assertGreaterEqual(len(result["evidence_items"]), 3)
        self.assertEqual(result["turns"], 2)
        # Turn 2 synthesis call must omit tools to guarantee final report generation
        second_call_kwargs = mock_chat.call_args_list[1].kwargs
        self.assertIsNone(second_call_kwargs["tools"])

    def test_whoisxml_live_integration_with_mock_http(self) -> None:
        from unittest.mock import MagicMock, patch
        from scamlens.intelligence.client import ThreatIntelligenceClient

        fake_resp = MagicMock()
        fake_resp.status_code = 200
        fake_resp.json.return_value = {
            "WhoisRecord": {
                "createdDate": "2026-11-24T00:00:00Z",
                "registrarName": "NameCheap, Inc.",
            }
        }
        client = ThreatIntelligenceClient(use_mock=False)
        client.whoisxml_api_key = "test_whoisxml_key"

        with patch("scamlens.intelligence.client.httpx.Client") as mock_http:
            mock_http.return_value.__enter__.return_value.get.return_value = fake_resp
            findings = client.inspect_domain_whois_rdap("http://fake-sbi.xyz/login")

        self.assertEqual(len(findings), 1)
        self.assertEqual(findings[0].source, "whoisxml")
        self.assertEqual(findings[0].metadata.get("registrar"), "NameCheap, Inc.")

    def test_virustotal_live_error_does_not_fall_back_to_mock(self) -> None:
        from unittest.mock import MagicMock, patch
        from scamlens.intelligence.client import ThreatIntelligenceClient

        fake_resp = MagicMock()
        fake_resp.status_code = 429
        client = ThreatIntelligenceClient(use_mock=False)
        client.vt_api_key = "test_vt_key"

        with patch("scamlens.intelligence.client.httpx.Client") as mock_http:
            mock_http.return_value.__enter__.return_value.get.return_value = fake_resp
            findings = client.check_virustotal_reputation("https://example.com")

        self.assertEqual(len(findings), 1)
        self.assertEqual(findings[0].source, "virustotal_v3_offline")
        self.assertNotIn("Simulated", findings[0].summary)


if __name__ == "__main__":
    unittest.main()
