"""Tests for ScamLens-AI Web GUI server, SSE live status streaming, and email routes."""

from __future__ import annotations

import base64
import json
import sys
import threading
import unittest
import urllib.request
from pathlib import Path
from typing import Any, Dict, List, Tuple

_SRC = Path(__file__).resolve().parent.parent / "src"
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

from scamlens.core.models import InvestigationSubmission
from scamlens.investigator.engine import ScamInvestigator
from GUI.server import create_gui_server


def _parse_sse(raw_text: str) -> List[Tuple[str, Dict[str, Any]]]:
    events: List[Tuple[str, Dict[str, Any]]] = []
    for frame in raw_text.split("\n\n"):
        if not frame.strip() or frame.startswith(":"):
            continue
        ev_name = "message"
        data_lines: List[str] = []
        for line in frame.splitlines():
            if line.startswith("event:"):
                ev_name = line[6:].strip()
            elif line.startswith("data:"):
                data_lines.append(line[5:].strip())
        if data_lines:
            events.append((ev_name, json.loads("\n".join(data_lines))))
    return events


class TestGUIServerAndStreaming(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.server = create_gui_server(host="127.0.0.1", port=0)
        cls.port = cls.server.server_address[1]
        cls.base_url = f"http://127.0.0.1:{cls.port}"
        cls.thread = threading.Thread(target=cls.server.serve_forever, daemon=True)
        cls.thread.start()

    @classmethod
    def tearDownClass(cls) -> None:
        cls.server.shutdown()
        cls.server.server_close()

    def _get(self, path: str) -> Tuple[int, str, bytes]:
        with urllib.request.urlopen(f"{self.base_url}{path}", timeout=10) as resp:
            return resp.status, resp.headers.get("Content-Type", ""), resp.read()

    def _post_json(self, path: str, payload: Dict[str, Any]) -> Tuple[int, str, bytes]:
        body = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(
            f"{self.base_url}{path}",
            data=body,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=15) as resp:
            return resp.status, resp.headers.get("Content-Type", ""), resp.read()

    def test_static_pages_and_metadata_endpoints(self) -> None:
        status, ctype, html = self._get("/")
        self.assertEqual(status, 200)
        self.assertIn("text/html", ctype)
        self.assertIn("ScamLens-AI", html.decode("utf-8"))

        status_js, _, js = self._get("/static/app.js")
        self.assertEqual(status_js, 200)
        self.assertIn("streamSSE", js.decode("utf-8"))

        _, _, health_raw = self._get("/api/v1/health")
        health = json.loads(health_raw.decode("utf-8"))
        self.assertEqual(health["status"], "healthy")
        self.assertIn("ai_provider", health)

        _, _, samples_raw = self._get("/api/v1/samples")
        samples = json.loads(samples_raw.decode("utf-8"))
        self.assertGreaterEqual(len(samples["samples"]), 1)

        _, _, reg_raw = self._get("/api/v1/registry")
        reg = json.loads(reg_raw.decode("utf-8"))
        self.assertIn("banks", reg)

        _, _, gmail_status_raw = self._get("/api/v1/emails/gmail/status")
        gmail_status = json.loads(gmail_status_raw.decode("utf-8"))
        self.assertIn("ready", gmail_status)

        _, _, arch_raw = self._get("/api/v1/architecture")
        arch = json.loads(arch_raw.decode("utf-8"))
        self.assertEqual(arch["orchestrator"]["max_turns"], 2)
        self.assertEqual(len(arch["tools"]), 9)
        self.assertTrue(any(c["id"] == "orchestrator" for c in arch["components"]))

    def test_local_emails_endpoint(self) -> None:
        status, _, raw = self._get("/api/v1/emails/local?max_results=3")
        self.assertEqual(status, 200)
        data = json.loads(raw.decode("utf-8"))
        self.assertEqual(data["count"], 3)
        self.assertEqual(len(data["emails"]), 3)
        self.assertIn("subject", data["emails"][0])

    def test_multimodal_stream_sse_and_uploaded_image(self) -> None:
        tiny_png = base64.b64encode(
            b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x02\x00\x00\x00\x90wS\xde"
        ).decode("ascii")

        status, ctype, raw = self._post_json(
            "/api/v1/investigate/stream",
            {
                "text": "Urgent: SBI KYC blocked within 24 hours. Click http://sbi-kyc-fake.xyz/login",
                "urls": ["http://sbi-kyc-fake.xyz/login"],
                "uploaded_images": [
                    {"filename": "screenshot.png", "data_base64": f"data:image/png;base64,{tiny_png}"}
                ],
            },
        )
        self.assertEqual(status, 200)
        self.assertIn("text/event-stream", ctype)
        events = _parse_sse(raw.decode("utf-8"))
        stages = [data.get("stage") for name, data in events if name == "status"]
        self.assertIn("started", stages)
        self.assertIn("analyzing_image", stages)
        self.assertIn("analyzing_url", stages)
        self.assertIn("scoring", stages)
        self.assertIn("completed", stages)

        result_events = [data for name, data in events if name == "result"]
        self.assertEqual(len(result_events), 1)
        inv = result_events[0]["investigation"]
        self.assertIn(inv["verdict"], ("Likely scam", "Suspicious — further verification needed"))

    def test_raw_email_stream_shows_reading_parsing_url_and_result(self) -> None:
        raw_eml = (
            "From: HDFC Bank <alert@hdfc-pan-update.online>\n"
            "Reply-To: attacker@dropmail.com\n"
            "Authentication-Results: mx.google.com; spf=fail; dkim=fail; dmarc=fail\n"
            "Subject: Urgent PAN KYC Freeze\n\n"
            "Your account will be frozen immediately. Visit http://hdfc-pan-update.online/auth\n"
        )
        status, _, raw = self._post_json(
            "/api/v1/investigate/email/stream",
            {"source": "raw", "raw_eml": raw_eml},
        )
        self.assertEqual(status, 200)
        events = _parse_sse(raw.decode("utf-8"))
        stages = [data.get("stage") for name, data in events if name == "status"]
        self.assertIn("reading_email", stages)
        self.assertIn("email_parsed", stages)
        self.assertIn("email_forensics", stages)
        self.assertIn("analyzing_url", stages)
        self.assertIn("completed", stages)

        parsed_ev = next(data for name, data in events if name == "status" and data.get("stage") == "email_parsed")
        self.assertEqual(parsed_ev["data"]["email"]["subject"], "Urgent PAN KYC Freeze")

        result_ev = next(data for name, data in events if name == "result")
        self.assertEqual(result_ev["investigation"]["verdict"], "Likely scam")

    def test_local_single_email_stream(self) -> None:
        status, _, raw = self._post_json(
            "/api/v1/investigate/email/stream",
            {"source": "local", "email_id": "1"},
        )
        self.assertEqual(status, 200)
        events = _parse_sse(raw.decode("utf-8"))
        stages = [data.get("stage") for name, data in events if name == "status"]
        self.assertIn("reading_email", stages)
        self.assertIn("email_parsed", stages)
        self.assertIn("completed", stages)
        result_ev = next(data for name, data in events if name == "result")
        self.assertIn("email", result_ev)
        self.assertIn("investigation", result_ev)

    def test_local_inbox_batch_scan_stream(self) -> None:
        status, _, raw = self._post_json(
            "/api/v1/emails/scan/stream",
            {"source": "local", "max_results": 2},
        )
        self.assertEqual(status, 200)
        events = _parse_sse(raw.decode("utf-8"))
        email_results = [data for name, data in events if name == "email_result"]
        self.assertEqual(len(email_results), 2)
        self.assertTrue(any(name == "scan_complete" for name, _ in events))

    def test_investigator_progress_callback_directly(self) -> None:
        seen_stages: List[str] = []
        inv = ScamInvestigator()
        inv.investigate(
            InvestigationSubmission(
                text="Verify KYC at http://fake-bank.xyz",
                urls=["http://fake-bank.xyz"],
            ),
            on_progress=lambda ev: seen_stages.append(ev["stage"]),
        )
        self.assertIn("analyzing_url", seen_stages)
        self.assertIn("scoring", seen_stages)
        self.assertIn("completed", seen_stages)


if __name__ == "__main__":
    unittest.main()
