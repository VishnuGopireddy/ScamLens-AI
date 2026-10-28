"""Test extractors: privacy, URL analysis, QR payload, and text indicators."""

import sys
import unittest
from pathlib import Path

_SRC = Path(__file__).resolve().parent.parent / "src"
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

from scamlens.core.models import EvidenceCategory
from scamlens.extractors.privacy import redact_pii
from scamlens.extractors.qr import analyze_qr_payload
from scamlens.extractors.text import extract_text_indicators
from scamlens.extractors.url import analyze_url, extract_urls


class TestExtractors(unittest.TestCase):
    def test_redact_pii(self):
        text = "Please enter OTP: 839201 and send to +919876543210 with password: mySecretPassword"
        redacted, count = redact_pii(text)
        self.assertGreaterEqual(count, 2)
        self.assertNotIn("839201", redacted)
        self.assertNotIn("mySecretPassword", redacted)
        self.assertIn("[REDACTED_OTP]", redacted)

    def test_url_extractor(self):
        text = "Visit http://sbi-fake-kyc.xyz/login to update"
        urls = extract_urls(text)
        self.assertEqual(len(urls), 1)
        self.assertIn("http://sbi-fake-kyc.xyz/login", urls)

        findings = analyze_url(urls[0])
        categories = [f.category for f in findings]
        self.assertIn(EvidenceCategory.URL_DOMAIN, categories)
        self.assertIn(EvidenceCategory.IMPERSONATION, categories)

    def test_qr_payment_payload(self):
        payload = "upi://pay?pa=merchant@upi&pn=RetailStore&am=150"
        findings = analyze_qr_payload(payload)
        self.assertGreaterEqual(len(findings), 1)
        self.assertEqual(findings[0].category, EvidenceCategory.PAYMENT_UPI)
        self.assertEqual(findings[0].metadata.get("vpa"), "merchant@upi")

    def test_text_urgency_extractor(self):
        text = "Urgent: Your account will be blocked within 24 hours. Immediately complete your KYC."
        findings = extract_text_indicators(text)
        self.assertGreaterEqual(len(findings), 1)
        summaries = [f.summary for f in findings]
        self.assertTrue(any("urgency" in s.lower() for s in summaries))


if __name__ == "__main__":
    unittest.main()
