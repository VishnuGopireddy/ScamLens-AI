"""Unit tests for the Gmail REST API extractor and email forensics module."""

from __future__ import annotations

import base64
import unittest
from unittest.mock import MagicMock, patch

from scamlens.core.models import (
    EvidenceCategory,
    IncidentStage,
    InvestigationSubmission,
    SeverityLevel,
    VerdictEnum,
)
from scamlens.extractors.email import (
    EmailAttachment,
    EmailMessage,
    GmailAuthManager,
    GmailReader,
    extract_email_evidence,
    parse_gmail_message,
)
from scamlens.investigator.engine import ScamInvestigator


def _encode_b64(text: str) -> str:
    """Helper to encode text to URL-safe base64 string."""
    return base64.urlsafe_b64encode(text.encode("utf-8")).decode("utf-8")


class TestEmailExtractor(unittest.TestCase):
    """Test suite for parsing and analyzing Gmail messages."""

    def test_parse_gmail_message_multipart(self) -> None:
        """Test parsing of multipart MIME message with plain text and HTML links."""
        raw_msg = {
            "id": "18cf123456789abc",
            "threadId": "thread_999",
            "snippet": "Your KYC has expired. Please verify now.",
            "payload": {
                "headers": [
                    {"name": "Subject", "value": "Urgent: SBI Account Suspended"},
                    {"name": "From", "value": "State Bank Support <alert@sbi-online-kyc.xyz>"},
                    {"name": "To", "value": "victim@example.com"},
                    {"name": "Date", "value": "Tue, 17 Nov 2026 12:00:00 +0000"},
                    {"name": "Reply-To", "value": "attacker@dropmail.com"},
                    {
                        "name": "Authentication-Results",
                        "value": "mx.google.com; spf=fail (google.com: domain does not designate 1.2.3.4) smtp.mailfrom=alert@sbi-online-kyc.xyz; dkim=fail; dmarc=fail action=none",
                    },
                ],
                "parts": [
                    {
                        "mimeType": "text/plain",
                        "body": {
                            "data": _encode_b64(
                                "Dear customer, your SBI account is locked. Update KYC at https://sbi-verification.xyz/login immediately."
                            )
                        },
                    },
                    {
                        "mimeType": "text/html",
                        "body": {
                            "data": _encode_b64(
                                '<html><body>Click <a href="https://sbi-verification.xyz/login">here</a> to unlock.</body></html>'
                            )
                        },
                    },
                    {
                        "mimeType": "application/x-msdownload",
                        "filename": "KYC_Update.exe",
                        "body": {
                            "size": 204800,
                            "attachmentId": "att_123",
                        },
                    },
                ],
            },
        }

        email_msg = parse_gmail_message(raw_msg)

        self.assertEqual(email_msg.id, "18cf123456789abc")
        self.assertEqual(email_msg.subject, "Urgent: SBI Account Suspended")
        self.assertEqual(email_msg.sender_name, "State Bank Support")
        self.assertEqual(email_msg.sender_email, "alert@sbi-online-kyc.xyz")
        self.assertEqual(email_msg.sender_domain, "sbi-online-kyc.xyz")
        self.assertEqual(email_msg.reply_to_email, "attacker@dropmail.com")

        # Check authentication parsing
        self.assertEqual(email_msg.spf_status, "fail")
        self.assertEqual(email_msg.dkim_status, "fail")
        self.assertEqual(email_msg.dmarc_status, "fail")

        # Check extracted URLs
        self.assertIn("https://sbi-verification.xyz/login", email_msg.extracted_urls)

        # Check attachment detection
        self.assertTrue(email_msg.has_attachment)
        self.assertEqual(len(email_msg.attachments), 1)
        self.assertEqual(email_msg.attachments[0].filename, "KYC_Update.exe")

    def test_extract_email_evidence_forensics(self) -> None:
        """Test extraction of spoofing indicators (SPF/DKIM fail, Reply-To mismatch, brand spoof)."""
        msg = EmailMessage(
            id="msg_001",
            thread_id="thr_001",
            subject="Action Required: KYC Expired",
            sender="State Bank Support <alert@sbi-online-kyc.xyz>",
            sender_name="State Bank Support (SBI)",
            sender_email="alert@sbi-online-kyc.xyz",
            sender_domain="sbi-online-kyc.xyz",
            reply_to="attacker@dropmail.com",
            reply_to_email="attacker@dropmail.com",
            spf_status="fail",
            dkim_status="fail",
            dmarc_status="fail",
            body_plain="Click here to verify",
            attachments=[
                EmailAttachment(filename="invoice.scr", mime_type="application/octet-stream", size_bytes=100)
            ],
        )

        findings = extract_email_evidence(msg)
        summaries = [f.summary for f in findings]

        # Verify SPF, DKIM, DMARC findings
        self.assertTrue(any("SPF email authentication failed" in s for s in summaries))
        self.assertTrue(any("DKIM" in s for s in summaries))
        self.assertTrue(any("DMARC" in s for s in summaries))

        # Verify Reply-To mismatch
        self.assertTrue(any("Reply-To address mismatch detected" in s for s in summaries))

        # Verify brand spoofing detection (SBI claimed in display name, but domain is sbi-online-kyc.xyz)
        self.assertTrue(any("impersonates 'Sbi'" in s for s in summaries))

        # Verify dangerous attachment detection
        self.assertTrue(any("Dangerous executable attachment" in s for s in summaries))

    def test_legitimate_email_evidence(self) -> None:
        """Test that a legitimate authenticated email triggers no spoofing evidence."""
        msg = EmailMessage(
            id="msg_legit",
            thread_id="thr_legit",
            subject="Your SBI Statement",
            sender="SBI Alerts <notify@sbi.co.in>",
            sender_name="SBI Alerts",
            sender_email="notify@sbi.co.in",
            sender_domain="sbi.co.in",
            reply_to=None,
            spf_status="pass",
            dkim_status="pass",
            dmarc_status="pass",
            body_plain="Please find your statement attached.",
        )

        findings = extract_email_evidence(msg)
        self.assertEqual(len(findings), 0)

    def test_to_submission_conversion(self) -> None:
        """Test conversion of EmailMessage into an InvestigationSubmission."""
        msg = EmailMessage(
            id="msg_test",
            thread_id="thr_test",
            subject="Suspicious Notice",
            sender="billing@xyz.com",
            sender_email="billing@xyz.com",
            sender_domain="xyz.com",
            date="Mon, 16 Nov 2026 10:00:00 GMT",
            spf_status="pass",
            dkim_status="pass",
            dmarc_status="pass",
            body_cleaned="Please check your bill at https://example.com/pay",
            extracted_urls=["https://example.com/pay"],
        )

        submission = msg.to_submission(incident_stage=IncidentStage.PRE_ACTION)
        self.assertIsInstance(submission, InvestigationSubmission)
        self.assertIn("Subject: Suspicious Notice", submission.text)
        self.assertIn("https://example.com/pay", submission.urls)
        self.assertIn("Authentication: SPF=pass", submission.context_description)

    def test_investigate_email_end_to_end(self) -> None:
        """Test ScamInvestigator.investigate_email pipeline with a phishing message."""
        msg = EmailMessage(
            id="msg_phish",
            thread_id="thr_phish",
            subject="Electricity bill unpaid - power cut tonight!",
            sender="State Electricity Board <threat@fake-power.xyz>",
            sender_name="Electricity Board Support",
            sender_email="threat@fake-power.xyz",
            sender_domain="fake-power.xyz",
            spf_status="fail",
            dkim_status="fail",
            dmarc_status="fail",
            body_cleaned="Dear customer, electricity will be disconnected tonight at 9:30 PM. Click https://fake-power.xyz/bill to pay immediately or call 9876543210.",
            extracted_urls=["https://fake-power.xyz/bill"],
        )

        investigator = ScamInvestigator()
        result = investigator.investigate_email(msg)

        # Should be classified as likely scam or suspicious with high risk score
        self.assertIn(result.verdict, (VerdictEnum.LIKELY_SCAM, VerdictEnum.SUSPICIOUS))
        self.assertGreaterEqual(result.risk_score, 60)
        self.assertGreater(len(result.evidence_findings), 0)

        # Check that email header findings are present in evidence
        summaries = [f.summary for f in result.evidence_findings]
        self.assertTrue(any("SPF email authentication failed" in s for s in summaries))


class TestGmailReaderWithMocks(unittest.TestCase):
    """Test GmailReader interactions with mocked Google API client."""

    def test_gmail_reader_list_and_get(self) -> None:
        """Test listing and fetching messages with mocked Google Resource."""
        mock_service = MagicMock()
        mock_messages = mock_service.users.return_value.messages.return_value

        # Mock list response
        mock_messages.list.return_value.execute.return_value = {
            "messages": [{"id": "msg_1"}, {"id": "msg_2"}]
        }

        # Mock get response
        mock_messages.get.return_value.execute.return_value = {
            "id": "msg_1",
            "threadId": "thr_1",
            "snippet": "Test snippet",
            "payload": {
                "headers": [
                    {"name": "Subject", "value": "Test Subject"},
                    {"name": "From", "value": "Sender <sender@example.com>"},
                ],
                "parts": [
                    {
                        "mimeType": "text/plain",
                        "body": {"data": _encode_b64("Hello world")},
                    }
                ],
            },
        }

        reader = GmailReader(service=mock_service)
        summaries = reader.list_message_summaries(query="is:unread", max_results=2)
        self.assertEqual(len(summaries), 2)

        msg = reader.get_message("msg_1")
        self.assertEqual(msg.subject, "Test Subject")
        self.assertEqual(msg.sender_email, "sender@example.com")
        self.assertEqual(msg.body_plain, "Hello world")

    def test_gmail_auth_manager_missing_file_raises_clear_error(self) -> None:
        """Verify GmailAuthManager raises helpful FileNotFoundError when credentials.json is missing."""
        manager = GmailAuthManager(
            credentials_file="nonexistent_credentials.json",
            token_file="nonexistent_token.json",
        )

        with patch("pathlib.Path.is_file", return_value=False):
            with patch.dict("sys.modules", {
                "google.auth.transport.requests": MagicMock(),
                "google.oauth2.credentials": MagicMock(),
                "google_auth_oauthlib.flow": MagicMock(),
            }):
                with self.assertRaises(FileNotFoundError) as ctx:
                    manager.get_credentials()
                self.assertIn("Gmail OAuth client secrets file not found", str(ctx.exception))
                self.assertIn("console.cloud.google.com", str(ctx.exception))


if __name__ == "__main__":
    unittest.main()
