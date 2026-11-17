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
        self.assertFalse(brand_res["is_official"])
        self.assertEqual(brand_res["cybercrime_helpline"], "1930")

        # 3. QR UPI decode tool
        qr_res = dispatcher.execute_tool(
            "decode_qr_payment",
            {"qr_payload": "upi://pay?pa=scammer@upi&pn=LuckyDraw&am=5000"}
        )
        self.assertIn("findings", qr_res)

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


if __name__ == "__main__":
    unittest.main()
