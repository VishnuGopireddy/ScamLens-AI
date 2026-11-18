"""Multimodal evidence extractors."""

from scamlens.extractors.email import (
    EmailAttachment,
    EmailMessage,
    GmailAuthManager,
    GmailReader,
    extract_email_evidence,
    parse_gmail_message,
)
from scamlens.extractors.privacy import redact_pii
from scamlens.extractors.qr import analyze_qr_payload
from scamlens.extractors.text import extract_text_indicators
from scamlens.extractors.url import analyze_url

__all__ = [
    "redact_pii",
    "analyze_qr_payload",
    "extract_text_indicators",
    "analyze_url",
    "EmailAttachment",
    "EmailMessage",
    "GmailAuthManager",
    "GmailReader",
    "extract_email_evidence",
    "parse_gmail_message",
]

