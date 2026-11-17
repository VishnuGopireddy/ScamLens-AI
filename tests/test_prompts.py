"""Tests for YAML prompt loader and catalog definitions."""

import sys
import unittest
from pathlib import Path

_SRC = Path(__file__).resolve().parent.parent / "src"
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

from scamlens.ai.prompts import (
    PromptTemplate,
    list_available_prompts,
    load_prompt,
)


class TestPromptCatalog(unittest.TestCase):
    def test_list_available_prompts(self):
        prompts = list_available_prompts()
        expected = [
            "action_guidance_v1",
            "evidence_synthesis_v1",
            "investigation_agent_v1",
            "text_triage_v1",
            "vision_screenshot_v1",
        ]
        for exp in expected:
            self.assertIn(exp, prompts)

    def test_load_text_triage_prompt(self):
        prompt = load_prompt("text_triage_v1")
        self.assertIsInstance(prompt, PromptTemplate)
        self.assertEqual(prompt.name, "text_triage_v1")
        self.assertGreater(len(prompt.few_shot_examples), 0)
        self.assertIn("text", prompt.input_variables)

        # Test rendering messages
        messages = prompt.render_messages(text="Test suspicious SMS")
        self.assertGreaterEqual(len(messages), 3)  # system + few-shot + user
        self.assertEqual(messages[0]["role"], "system")
        self.assertEqual(messages[-1]["role"], "user")
        self.assertIn("Test suspicious SMS", messages[-1]["content"])

    def test_missing_input_variable_raises(self):
        prompt = load_prompt("text_triage_v1")
        with self.assertRaises(ValueError) as ctx:
            prompt.render_user_prompt()
        self.assertIn("Missing required prompt variable", str(ctx.exception))

    def test_load_evidence_synthesis_prompt(self):
        prompt = load_prompt("evidence_synthesis_v1")
        self.assertEqual(prompt.model_parameters.get("response_format"), "json_object")
        messages = prompt.render_messages(
            text="KYC link",
            urls="http://fake.xyz",
            qr_payloads="None",
            findings_summary="Suspicious TLD match",
        )
        self.assertEqual(messages[0]["role"], "system")
        self.assertIn("thought_process", messages[0]["content"])
        self.assertIn("fake.xyz", messages[-1]["content"])

    def test_prompt_not_found(self):
        with self.assertRaises(FileNotFoundError):
            load_prompt("non_existent_prompt_v99")


if __name__ == "__main__":
    unittest.main()

