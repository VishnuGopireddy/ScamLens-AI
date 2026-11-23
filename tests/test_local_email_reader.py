"""Unit tests for LocalEmailReader, parse_raw_email, and local email dataset loading."""

from __future__ import annotations

import unittest
from pathlib import Path

from scamlens.extractors.email import (
    EmailMessage,
    LocalEmailReader,
    load_emails_from_file,
    parse_raw_email,
)


class TestLocalEmailReader(unittest.TestCase):
    """Test suite for reading and parsing raw emails from local sources for PoC pipelines."""

    def test_parse_raw_email_basic(self) -> None:
        """Test parsing of raw RFC 5322 MIME string."""
        raw = (
            "From: Alerts <alerts@bank.example.com>\n"
            "To: user@example.com\n"
            "Cc: audit@bank.example.com\n"
            "Subject: Your Monthly Statement\n"
            "Date: Mon, 20 Oct 2026 10:00:00 +0530\n"
            "Reply-To: support@bank.example.com\n"
            "Authentication-Results: mx.google.com; spf=pass; dkim=pass; dmarc=pass\n"
            "Received-SPF: pass\n"
            "Content-Type: text/plain; charset=utf-8\n"
            "\n"
            "Dear Customer, your statement is ready. Visit https://bank.example.com/portal\n"
        )
        msg = parse_raw_email(raw, msg_id="test_msg_001")

        self.assertEqual(msg.id, "test_msg_001")
        self.assertEqual(msg.subject, "Your Monthly Statement")
        self.assertEqual(msg.sender_email, "alerts@bank.example.com")
        self.assertEqual(msg.sender_name, "Alerts")
        self.assertEqual(msg.recipient, "user@example.com")
        self.assertEqual(msg.cc, "audit@bank.example.com")
        self.assertEqual(msg.reply_to_email, "support@bank.example.com")
        self.assertEqual(msg.spf_status, "pass")
        self.assertEqual(msg.dkim_status, "pass")
        self.assertEqual(msg.dmarc_status, "pass")
        self.assertIn("https://bank.example.com/portal", msg.extracted_urls)
        self.assertIn("Dear Customer", msg.body_cleaned)

    def test_local_reader_json_source(self) -> None:
        """Test loading all 20 emails from local JSON dataset (Gmail API format)."""
        json_path = Path("data/spam-indian-bank-emails.json")
        if not json_path.is_file():
            self.skipTest("data/spam-indian-bank-emails.json not present")

        reader = LocalEmailReader(json_path)
        emails = reader.fetch_messages()

        self.assertEqual(len(emails), 20)
        first = emails[0]
        self.assertIsInstance(first, EmailMessage)
        self.assertTrue(first.subject)
        self.assertTrue(first.sender_email)
        self.assertIn(first.spf_status, ("pass", "fail", "softfail", "unknown"))

        # Test get_message by id
        fetched = reader.get_message(first.id)
        self.assertEqual(fetched.id, first.id)

        # Test summaries
        summaries = reader.list_message_summaries(max_results=5)
        self.assertEqual(len(summaries), 5)
        self.assertIn("subject", summaries[0])

    def test_local_reader_markdown_source(self) -> None:
        """Test loading all 20 raw RFC 5322 emails from Markdown (.md) dataset."""
        md_path = Path("data/spam-indian-bank-emails.md")
        if not md_path.is_file():
            self.skipTest("data/spam-indian-bank-emails.md not present")

        reader = LocalEmailReader(md_path)
        emails = reader.fetch_messages()

        self.assertEqual(len(emails), 20)
        first = emails[0]
        self.assertIsInstance(first, EmailMessage)
        self.assertEqual(first.sender_email, "alerts@hdfcbank.net")
        self.assertEqual(first.spf_status, "pass")
        self.assertGreater(len(first.extracted_urls), 0)

    def test_local_reader_eml_directory(self) -> None:
        """Test loading all 20 emails from raw_emails directory in exact 1..20 order."""
        eml_dir = Path("data/raw_emails")
        if not eml_dir.is_dir():
            self.skipTest("data/raw_emails directory not present")

        reader = LocalEmailReader(eml_dir)
        emails = reader.fetch_messages()

        self.assertEqual(len(emails), 20)
        self.assertEqual(emails[0].id, "1")
        self.assertEqual(emails[19].id, "20")

    def test_email_submission_includes_cc(self) -> None:
        """Test that converting EmailMessage to InvestigationSubmission preserves CC field."""
        msg = EmailMessage(
            id="msg_cc_test",
            thread_id="thr_cc_test",
            subject="Audit Notice",
            sender="Manager <manager@corp.example.com>",
            sender_email="manager@corp.example.com",
            recipient="employee@corp.example.com",
            cc="compliance@corp.example.com",
            body_plain="Please review attached compliance policy.",
        )
        submission = msg.to_submission()
        self.assertIn("Cc: compliance@corp.example.com", submission.text)


if __name__ == "__main__":
    unittest.main()
