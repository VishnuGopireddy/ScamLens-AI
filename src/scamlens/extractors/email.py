"""Gmail REST API connector and forensic email evidence extractor.

Provides:
- OAuth2 authentication manager for Google Gmail API.
- Email MIME parsing and URL extraction.
- Email header forensics: SPF, DKIM, DMARC validation and Reply-To mismatch detection.
- Seamless conversion to InvestigationSubmission for ScamLens-AI investigation.
"""

from __future__ import annotations

import base64
import email
from email import policy
import html
import json
import logging
import os
import re
from dataclasses import dataclass, field
from email.utils import parseaddr
from html.parser import HTMLParser
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union
from urllib.parse import urlparse

from scamlens.core.config import get_settings
from scamlens.core.models import (
    EvidenceCategory,
    EvidenceItem,
    IncidentStage,
    InvestigationSubmission,
    SeverityLevel,
)
from scamlens.extractors.url import extract_urls

logger = logging.getLogger(__name__)

# Trusted official domains for impersonation cross-checks
_KNOWN_BRAND_DOMAINS: Dict[str, List[str]] = {
    "sbi": ["sbi.co.in", "onlinesbi.sbi", "statebankofindia.com"],
    "hdfc": ["hdfcbank.com", "hdfc.com"],
    "icici": ["icicibank.com"],
    "axis": ["axisbank.com"],
    "pnb": ["pnbindia.in"],
    "kotak": ["kotak.com"],
    "paytm": ["paytm.com"],
    "phonepe": ["phonepe.com"],
    "google": ["google.com", "gmail.com"],
    "paypal": ["paypal.com"],
    "amazon": ["amazon.in", "amazon.com"],
    "flipkart": ["flipkart.com"],
    "netflix": ["netflix.com"],
    "apple": ["apple.com", "icloud.com"],
    "microsoft": ["microsoft.com", "live.com", "outlook.com"],
    "income tax": ["incometax.gov.in", "gov.in"],
    "uidai": ["uidai.gov.in", "gov.in"],
    "india post": ["indiapost.gov.in", "gov.in"],
}


class _HTMLTextExtractor(HTMLParser):
    """Clean HTML parser that extracts visible text and collects anchor href links."""

    def __init__(self) -> None:
        super().__init__()
        self.text_parts: List[str] = []
        self.links: List[str] = []
        self._ignore = False

    def handle_starttag(self, tag: str, attrs: List[Tuple[str, Optional[str]]]) -> None:
        if tag.lower() in ("script", "style"):
            self._ignore = True
        elif tag.lower() == "a":
            for attr_name, attr_val in attrs:
                if attr_name.lower() == "href" and attr_val:
                    self.links.append(attr_val.strip())

    def handle_endtag(self, tag: str) -> None:
        if tag.lower() in ("script", "style"):
            self._ignore = False

    def handle_data(self, data: str) -> None:
        if not self._ignore:
            cleaned = data.strip()
            if cleaned:
                self.text_parts.append(cleaned)

    def get_text(self) -> str:
        return " ".join(self.text_parts)


@dataclass
class EmailAttachment:
    """Metadata describing an email attachment."""

    filename: str
    mime_type: str
    size_bytes: int
    attachment_id: Optional[str] = None


@dataclass
class EmailMessage:
    """Structured representation of a parsed email message."""

    id: str
    thread_id: str
    snippet: str = ""
    subject: str = "(No Subject)"
    sender: str = ""
    sender_name: str = ""
    sender_email: str = ""
    sender_domain: str = ""
    recipient: str = ""
    cc: str = ""
    date: str = ""
    reply_to: Optional[str] = None
    reply_to_email: Optional[str] = None
    return_path: Optional[str] = None
    auth_results: str = ""
    spf_status: str = "unknown"
    dkim_status: str = "unknown"
    dmarc_status: str = "unknown"
    body_plain: str = ""
    body_html: str = ""
    body_cleaned: str = ""
    extracted_urls: List[str] = field(default_factory=list)
    attachments: List[EmailAttachment] = field(default_factory=list)
    raw_headers: Dict[str, str] = field(default_factory=dict)

    @property
    def has_attachment(self) -> bool:
        """Return True if message has one or more file attachments."""
        return len(self.attachments) > 0

    def to_submission(
        self, incident_stage: IncidentStage = IncidentStage.PRE_ACTION
    ) -> InvestigationSubmission:
        """Convert this email into an InvestigationSubmission for ScamLens-AI."""
        combined_text = (
            f"Subject: {self.subject}\n"
            f"From: {self.sender}\n"
            f"Date: {self.date}\n"
        )
        if self.cc:
            combined_text += f"Cc: {self.cc}\n"
        if self.reply_to:
            combined_text += f"Reply-To: {self.reply_to}\n"
        combined_text += f"\n{self.body_cleaned or self.body_plain or self.snippet}"

        context_notes = [
            f"Email ID: {self.id}",
            f"Sender: {self.sender_email} (domain: {self.sender_domain})",
            f"Authentication: SPF={self.spf_status}, DKIM={self.dkim_status}, DMARC={self.dmarc_status}",
        ]
        if self.reply_to_email and self.reply_to_email.lower() != self.sender_email.lower():
            context_notes.append(
                f"FLAG: Reply-To ({self.reply_to_email}) differs from From ({self.sender_email})"
            )
        if self.attachments:
            names = [a.filename for a in self.attachments if a.filename]
            context_notes.append(f"Attachments ({len(self.attachments)}): {', '.join(names)}")

        return InvestigationSubmission(
            text=combined_text,
            urls=list(self.extracted_urls),
            context_description=" | ".join(context_notes),
            incident_stage=incident_stage,
        )

    def to_dict(self) -> Dict[str, Any]:
        """Convert to serializable dictionary."""
        return {
            "id": self.id,
            "thread_id": self.thread_id,
            "subject": self.subject,
            "sender": self.sender,
            "sender_name": self.sender_name,
            "sender_email": self.sender_email,
            "sender_domain": self.sender_domain,
            "recipient": self.recipient,
            "cc": self.cc,
            "date": self.date,
            "time_of_email": self.date,
            "has_attachment": self.has_attachment,
            "reply_to": self.reply_to,
            "reply_to_email": self.reply_to_email,
            "spf_status": self.spf_status,
            "dkim_status": self.dkim_status,
            "dmarc_status": self.dmarc_status,
            "email_content": self.body_cleaned or self.body_plain or self.snippet,
            "extracted_urls": self.extracted_urls,
            "attachments": [
                {
                    "filename": a.filename,
                    "mime_type": a.mime_type,
                    "size_bytes": a.size_bytes,
                }
                for a in self.attachments
            ],
        }


def _extract_auth_status(auth_text: str, protocol: str) -> str:
    """Extract auth result status (e.g. spf=pass, dkim=fail, dmarc=pass) from header text."""
    if not auth_text:
        return "unknown"
    pattern = rf"\b{re.escape(protocol)}\s*=\s*([a-zA-Z0-9_-]+)"
    match = re.search(pattern, auth_text, re.IGNORECASE)
    if match:
        return match.group(1).lower()
    return "unknown"


def _decode_body_data(data_b64: str) -> str:
    """Safely decode base64url-encoded Gmail body data."""
    if not data_b64:
        return ""
    try:
        # Standardize padding
        padded = data_b64 + "=" * (-len(data_b64) % 4)
        raw_bytes = base64.urlsafe_b64decode(padded)
        return raw_bytes.decode("utf-8", errors="replace")
    except Exception as exc:
        logger.warning(f"Failed to decode message body part: {exc}")
        return ""


def parse_gmail_message(msg_data: Dict[str, Any]) -> EmailMessage:
    """Parse a Gmail API message resource into an EmailMessage dataclass."""
    msg_id = msg_data.get("id", "")
    thread_id = msg_data.get("threadId", "")
    snippet = html.unescape(msg_data.get("snippet", ""))

    payload = msg_data.get("payload", {})
    headers_list = payload.get("headers", [])
    headers: Dict[str, str] = {h.get("name", ""): h.get("value", "") for h in headers_list}

    # Case-insensitive header lookup helper
    lower_headers = {k.lower(): v for k, v in headers.items()}

    subject = lower_headers.get("subject", "(No Subject)")
    sender_raw = lower_headers.get("from", "")
    recipient = lower_headers.get("to", "")
    cc = lower_headers.get("cc", "")
    date = lower_headers.get("date", "")
    reply_to = lower_headers.get("reply-to")
    return_path = lower_headers.get("return-path")

    # Parse sender info
    sender_name, sender_email = parseaddr(sender_raw)
    sender_domain = ""
    if "@" in sender_email:
        sender_domain = sender_email.split("@")[-1].lower()

    # Parse reply-to info
    reply_to_email = None
    if reply_to:
        _, reply_to_email = parseaddr(reply_to)

    # Security & authentication headers
    auth_results = lower_headers.get("authentication-results", "")
    received_spf = lower_headers.get("received-spf", "")

    spf_status = _extract_auth_status(auth_results, "spf")
    if spf_status == "unknown" and received_spf:
        spf_match = re.match(r"^([a-zA-Z]+)", received_spf.strip())
        if spf_match:
            spf_status = spf_match.group(1).lower()

    dkim_status = _extract_auth_status(auth_results, "dkim")
    dmarc_status = _extract_auth_status(auth_results, "dmarc")

    # Traverse MIME parts for body and attachments
    plain_parts: List[str] = []
    html_parts: List[str] = []
    attachments: List[EmailAttachment] = []
    html_links: List[str] = []

    def _walk_parts(part: Dict[str, Any]) -> None:
        mime_type = part.get("mimeType", "").lower()
        filename = part.get("filename", "")
        body = part.get("body", {})
        data = body.get("data", "")
        attachment_id = body.get("attachmentId")
        size = body.get("size", 0)

        if filename and attachment_id:
            attachments.append(
                EmailAttachment(
                    filename=filename,
                    mime_type=mime_type,
                    size_bytes=size,
                    attachment_id=attachment_id,
                )
            )

        if data:
            decoded = _decode_body_data(data)
            if mime_type == "text/plain":
                plain_parts.append(decoded)
            elif mime_type == "text/html":
                html_parts.append(decoded)
                parser = _HTMLTextExtractor()
                try:
                    parser.feed(decoded)
                    html_links.extend(parser.links)
                except Exception:
                    pass

        # Recurse sub-parts
        for sub_part in part.get("parts", []):
            _walk_parts(sub_part)

    _walk_parts(payload)

    body_plain = "\n".join(plain_parts)
    body_html = "\n".join(html_parts)

    # Clean text representation
    body_cleaned = body_plain.strip()
    if not body_cleaned and body_html:
        parser = _HTMLTextExtractor()
        try:
            parser.feed(body_html)
            body_cleaned = parser.get_text().strip()
        except Exception:
            body_cleaned = re.sub(r"<[^>]+>", " ", body_html).strip()

    # Extract all embedded URLs
    urls_found = extract_urls(body_cleaned) + extract_urls(body_plain) + html_links
    deduped_urls: List[str] = list(dict.fromkeys([u for u in urls_found if u.startswith("http")]))

    return EmailMessage(
        id=msg_id,
        thread_id=thread_id,
        snippet=snippet,
        subject=subject,
        sender=sender_raw,
        sender_name=sender_name,
        sender_email=sender_email,
        sender_domain=sender_domain,
        recipient=recipient,
        cc=cc,
        date=date,
        reply_to=reply_to,
        reply_to_email=reply_to_email,
        return_path=return_path,
        auth_results=auth_results,
        spf_status=spf_status,
        dkim_status=dkim_status,
        dmarc_status=dmarc_status,
        body_plain=body_plain,
        body_html=body_html,
        body_cleaned=body_cleaned,
        extracted_urls=deduped_urls,
        attachments=attachments,
        raw_headers=headers,
    )


def parse_raw_email(raw_content: Union[str, bytes], msg_id: Optional[str] = None) -> EmailMessage:
    """Parse a raw RFC 5322 / MIME email string or bytes into an EmailMessage dataclass."""
    if isinstance(raw_content, bytes):
        msg = email.message_from_bytes(raw_content, policy=policy.default)
    else:
        msg = email.message_from_string(raw_content, policy=policy.default)

    headers: Dict[str, str] = {k: str(v) for k, v in msg.items()}
    lower_headers = {k.lower(): v for k, v in headers.items()}

    subject = lower_headers.get("subject", "(No Subject)")
    sender_raw = lower_headers.get("from", "")
    recipient = lower_headers.get("to", "")
    cc = lower_headers.get("cc", "")
    date = lower_headers.get("date", "")
    reply_to = lower_headers.get("reply-to")
    return_path = lower_headers.get("return-path")

    sender_name, sender_email = parseaddr(sender_raw)
    sender_domain = ""
    if "@" in sender_email:
        sender_domain = sender_email.split("@")[-1].lower()

    reply_to_email = None
    if reply_to:
        _, reply_to_email = parseaddr(reply_to)

    auth_results = lower_headers.get("authentication-results", "")
    received_spf = lower_headers.get("received-spf", "")

    spf_status = _extract_auth_status(auth_results, "spf")
    if spf_status == "unknown" and received_spf:
        spf_match = re.match(r"^([a-zA-Z]+)", received_spf.strip())
        if spf_match:
            spf_status = spf_match.group(1).lower()

    dkim_status = _extract_auth_status(auth_results, "dkim")
    dmarc_status = _extract_auth_status(auth_results, "dmarc")

    plain_parts: List[str] = []
    html_parts: List[str] = []
    attachments: List[EmailAttachment] = []
    html_links: List[str] = []

    for part in msg.walk():
        content_disposition = str(part.get("Content-Disposition", ""))
        content_type = part.get_content_type()
        filename = part.get_filename()

        if filename or "attachment" in content_disposition.lower():
            fname = filename or "unnamed_attachment"
            try:
                payload_bytes = part.get_payload(decode=True) or b""
            except Exception:
                payload_bytes = b""
            attachments.append(
                EmailAttachment(
                    filename=fname,
                    mime_type=content_type,
                    size_bytes=len(payload_bytes),
                    attachment_id=part.get("Content-ID", fname),
                )
            )
        elif content_type == "text/plain":
            try:
                text_content = part.get_content()
            except Exception:
                payload = part.get_payload(decode=True)
                text_content = payload.decode("utf-8", errors="replace") if payload else ""
            if text_content:
                plain_parts.append(text_content)
        elif content_type == "text/html":
            try:
                html_content = part.get_content()
            except Exception:
                payload = part.get_payload(decode=True)
                html_content = payload.decode("utf-8", errors="replace") if payload else ""
            if html_content:
                html_parts.append(html_content)
                parser = _HTMLTextExtractor()
                try:
                    parser.feed(html_content)
                    html_links.extend(parser.links)
                except Exception:
                    pass

    body_plain = "\n".join(plain_parts)
    body_html = "\n".join(html_parts)
    body_cleaned = body_plain.strip()
    if not body_cleaned and body_html:
        parser = _HTMLTextExtractor()
        try:
            parser.feed(body_html)
            body_cleaned = parser.get_text().strip()
        except Exception:
            body_cleaned = re.sub(r"<[^>]+>", " ", body_html).strip()

    urls_found = extract_urls(body_cleaned) + extract_urls(body_plain) + html_links
    deduped_urls = list(dict.fromkeys([u for u in urls_found if u.startswith("http")]))

    derived_id = msg_id or msg.get("Message-ID", "") or f"msg_{abs(hash(subject + sender_raw)):x}"
    clean_id = derived_id.strip("<> ")

    return EmailMessage(
        id=clean_id,
        thread_id=clean_id,
        snippet=body_cleaned[:120],
        subject=subject,
        sender=sender_raw,
        sender_name=sender_name,
        sender_email=sender_email,
        sender_domain=sender_domain,
        recipient=recipient,
        cc=cc,
        date=date,
        reply_to=reply_to,
        reply_to_email=reply_to_email,
        return_path=return_path,
        auth_results=auth_results,
        spf_status=spf_status,
        dkim_status=dkim_status,
        dmarc_status=dmarc_status,
        body_plain=body_plain,
        body_html=body_html,
        body_cleaned=body_cleaned,
        extracted_urls=deduped_urls,
        attachments=attachments,
        raw_headers=headers,
    )


def extract_email_evidence(msg: EmailMessage) -> List[EvidenceItem]:
    """Perform forensic security checks on email metadata, headers, and authentication."""
    findings: List[EvidenceItem] = []

    # 1. SPF Failure Check
    if msg.spf_status in ("fail", "softfail"):
        findings.append(
            EvidenceItem(
                category=EvidenceCategory.IMPERSONATION,
                severity=SeverityLevel.HIGH,
                summary=f"SPF email authentication failed ({msg.spf_status})",
                details=(
                    f"The sending mail server is not authorized by the domain owner of "
                    f"'{msg.sender_domain}'. This is a strong indicator of email spoofing."
                ),
                is_verified=True,
                source="email_headers_spf",
            )
        )

    # 2. DKIM Failure Check
    if msg.dkim_status == "fail":
        findings.append(
            EvidenceItem(
                category=EvidenceCategory.IMPERSONATION,
                severity=SeverityLevel.HIGH,
                summary="DKIM cryptographic signature verification failed",
                details=(
                    f"The cryptographic signature on this email does not match domain '{msg.sender_domain}', "
                    "indicating possible tampering in transit or a forged sender address."
                ),
                is_verified=True,
                source="email_headers_dkim",
            )
        )

    # 3. DMARC Failure Check
    if msg.dmarc_status == "fail":
        findings.append(
            EvidenceItem(
                category=EvidenceCategory.IMPERSONATION,
                severity=SeverityLevel.CRITICAL,
                summary="DMARC policy alignment check failed",
                details=(
                    f"Domain '{msg.sender_domain}' enforces DMARC, but the message failed alignment. "
                    "The sender identity cannot be verified."
                ),
                is_verified=True,
                source="email_headers_dmarc",
            )
        )

    # 4. Reply-To / From Domain Mismatch Check
    if (
        msg.reply_to_email
        and msg.sender_email
        and msg.reply_to_email.lower() != msg.sender_email.lower()
    ):
        reply_domain = msg.reply_to_email.split("@")[-1].lower() if "@" in msg.reply_to_email else ""
        if reply_domain != msg.sender_domain:
            findings.append(
                EvidenceItem(
                    category=EvidenceCategory.IMPERSONATION,
                    severity=SeverityLevel.HIGH,
                    summary="Reply-To address mismatch detected",
                    details=(
                        f"Email claims to be from '{msg.sender_email}', but replies will be routed to "
                        f"'{msg.reply_to_email}'. This is a classic tactic to hijack responses in phishing."
                    ),
                    is_verified=True,
                    source="email_headers_reply_to",
                )
            )

    # 5. Display Name Brand Spoofing Check
    sender_name_lower = msg.sender_name.lower()
    for brand, valid_domains in _KNOWN_BRAND_DOMAINS.items():
        if brand in sender_name_lower:
            is_valid_domain = any(
                msg.sender_domain == d or msg.sender_domain.endswith(f".{d}")
                for d in valid_domains
            )
            if not is_valid_domain and msg.sender_domain:
                findings.append(
                    EvidenceItem(
                        category=EvidenceCategory.IMPERSONATION,
                        severity=SeverityLevel.HIGH,
                        summary=f"Display name impersonates '{brand.title()}' on unverified domain",
                        details=(
                            f"Display name '{msg.sender_name}' references trusted brand '{brand.title()}', "
                            f"but the sending address is '@{msg.sender_domain}' (expected {', '.join(valid_domains)})."
                        ),
                        is_verified=True,
                        source="email_sender_impersonation",
                    )
                )

    # 6. Suspicious attachment types (executables, scripts, macro docs)
    dangerous_exts = {".exe", ".scr", ".bat", ".vbs", ".js", ".iso", ".wsf", ".hta", ".xlsm", ".docm"}
    for att in msg.attachments:
        _, ext = os.path.splitext(att.filename.lower())
        if ext in dangerous_exts:
            findings.append(
                EvidenceItem(
                    category=EvidenceCategory.EXTERNAL_INTEL,
                    severity=SeverityLevel.CRITICAL,
                    summary=f"Dangerous executable attachment detected: {att.filename}",
                    details=f"Attachment '{att.filename}' ({att.mime_type}) has a high-risk executable extension.",
                    is_verified=True,
                    source="email_attachment_analysis",
                )
            )

    return findings


class GmailAuthManager:
    """Handles OAuth 2.0 authentication and token caching for Gmail REST API."""

    def __init__(
        self,
        credentials_file: Optional[str] = None,
        token_file: Optional[str] = None,
        scopes: Optional[List[str]] = None,
    ) -> None:
        settings = get_settings()
        self.credentials_file = credentials_file or settings.gmail_credentials_file
        self.token_file = token_file or settings.gmail_token_file
        self.scopes = scopes or [s.strip() for s in settings.gmail_scopes.split(",") if s.strip()]

    def get_credentials(self) -> Any:
        """Obtain valid user OAuth2 credentials from cache or initiate consent flow."""
        try:
            from google.auth.transport.requests import Request
            from google.oauth2.credentials import Credentials
            from google_auth_oauthlib.flow import InstalledAppFlow
        except ImportError as exc:
            raise ImportError(
                "Google API client libraries are not installed.\n"
                "Install them with:\n"
                "  pip install 'scamlens-ai[gmail]'\n"
                "or:\n"
                "  pip install google-api-python-client google-auth-httplib2 google-auth-oauthlib"
            ) from exc

        creds = None
        token_path = Path(self.token_file)

        # 1. Load cached token if available
        if token_path.is_file():
            try:
                creds = Credentials.from_authorized_user_file(str(token_path), self.scopes)
            except Exception as e:
                logger.warning(f"Could not load token file {token_path}: {e}")
                creds = None

        # 2. Refresh or authenticate if credentials are not valid
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                try:
                    logger.info("Refreshing expired Gmail OAuth token...")
                    creds.refresh(Request())
                except Exception as e:
                    logger.warning(f"Token refresh failed, re-authenticating: {e}")
                    creds = None

            if not creds:
                cred_path = Path(self.credentials_file)
                if not cred_path.is_file():
                    raise FileNotFoundError(
                        f"Gmail OAuth client secrets file not found at: '{self.credentials_file}'.\n"
                        "To set up Gmail REST API access:\n"
                        "1. Go to Google Cloud Console (https://console.cloud.google.com)\n"
                        "2. Enable the Gmail API (APIs & Services > Library > Gmail API)\n"
                        "3. Configure OAuth Consent Screen & create OAuth 2.0 Client ID (type: 'Desktop app')\n"
                        f"4. Download JSON and save it as '{self.credentials_file}' (or set GMAIL_CREDENTIALS_FILE in .env)."
                    )

                # Inspect client type (desktop 'installed' vs 'web')
                server_port = 0
                try:
                    with open(cred_path, "r", encoding="utf-8") as f:
                        cfg_data = json.load(f)
                    if "web" in cfg_data:
                        web_cfg = cfg_data["web"]
                        uris = web_cfg.get("redirect_uris") or []
                        found_port = None
                        for u in uris:
                            parsed_u = urlparse(u)
                            if parsed_u.hostname in ("localhost", "127.0.0.1") and parsed_u.port:
                                found_port = parsed_u.port
                                break
                        if found_port:
                            server_port = found_port
                        elif not uris:
                            server_port = 8080
                except Exception:
                    pass

                logger.info(f"Initiating OAuth flow using {cred_path} on port {server_port}...")
                flow = InstalledAppFlow.from_client_secrets_file(str(cred_path), self.scopes)
                print("\nOpening Google OAuth consent screen...")
                print("If a browser does not open automatically, copy and visit the authorization URL below:\n")
                creds = flow.run_local_server(
                    port=server_port,
                    access_type="offline",
                    prompt="consent",
                )

            # Save cached credentials
            try:
                token_path.parent.mkdir(parents=True, exist_ok=True)
                with open(token_path, "w", encoding="utf-8") as token_out:
                    token_out.write(creds.to_json())
                logger.info(f"Saved OAuth credentials to {token_path}")
            except Exception as e:
                logger.warning(f"Could not cache token to {token_path}: {e}")

        return creds

    def build_service(self) -> Any:
        """Build and return an authorized Gmail API service resource."""
        try:
            from googleapiclient.discovery import build
        except ImportError as exc:
            raise ImportError(
                "google-api-python-client is not installed. Install with: pip install google-api-python-client"
            ) from exc

        creds = self.get_credentials()
        return build("gmail", "v1", credentials=creds)


class GmailReader:
    """High-level client to query, fetch, and convert Gmail messages for ScamLens."""

    def __init__(
        self,
        service: Optional[Any] = None,
        auth_manager: Optional[GmailAuthManager] = None,
    ) -> None:
        self._auth_manager = auth_manager or GmailAuthManager()
        self._service = service

    @property
    def service(self) -> Any:
        if self._service is None:
            self._service = self._auth_manager.build_service()
        return self._service

    def list_message_summaries(
        self, query: str = "is:unread", max_results: int = 10, user_id: str = "me"
    ) -> List[Dict[str, str]]:
        """List basic message references matching a query."""
        results = (
            self.service.users()
            .messages()
            .list(userId=user_id, q=query, maxResults=max_results)
            .execute()
        )
        return results.get("messages", [])

    def get_message(self, message_id: str, user_id: str = "me") -> EmailMessage:
        """Fetch and parse a complete message by ID."""
        raw = (
            self.service.users()
            .messages()
            .get(userId=user_id, id=message_id, format="full")
            .execute()
        )
        return parse_gmail_message(raw)

    def fetch_messages(
        self, query: str = "is:unread", max_results: int = 10, user_id: str = "me"
    ) -> List[EmailMessage]:
        """Fetch, decode, and parse all messages matching query."""
        summaries = self.list_message_summaries(
            query=query, max_results=max_results, user_id=user_id
        )
        messages: List[EmailMessage] = []
        for item in summaries:
            try:
                msg = self.get_message(item["id"], user_id=user_id)
                messages.append(msg)
            except Exception as e:
                logger.error(f"Failed to fetch message {item.get('id')}: {e}")
        return messages


def load_emails_from_file(file_path: Union[str, Path]) -> List[EmailMessage]:
    """Load and parse emails from a local JSON, Markdown (.md), or raw .eml file.

    Supports:
    - .json: List or dict of Gmail REST API message objects (parsed via parse_gmail_message)
    - .md / .txt: Files containing raw RFC 5322 MIME email blocks (e.g. ```email ... ```)
    - .eml: Standard RFC 5322 MIME email files
    """
    path = Path(file_path)
    if not path.is_file():
        # Fallback to repo root resolution if relative path called from a subfolder
        repo_root = Path(__file__).resolve().parent.parent.parent
        if (repo_root / path).is_file():
            path = repo_root / path
        else:
            raise FileNotFoundError(f"Email dataset file not found: {path}")

    suffix = path.suffix.lower()
    if suffix == ".json":
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        items = data.get("emails", data) if isinstance(data, dict) else data
        if not isinstance(items, list):
            items = [items]
        return [parse_gmail_message(item) for item in items]

    content = path.read_text(encoding="utf-8")
    # Extract fenced raw email blocks (e.g. ```email ... ``` or ```rfc822 ... ```)
    email_blocks = re.findall(r"```(?:email|rfc822|eml|mail)\s*\n(.*?)\n```", content, re.DOTALL)
    if not email_blocks:
        email_blocks = re.findall(r"```(?:[a-zA-Z0-9_-]+)?\s*\n(.*?)\n```", content, re.DOTALL)
    if not email_blocks:
        # Check for demarcation or treat as single raw RFC822 email
        if "From:" in content and "Subject:" in content:
            email_blocks = [content]

    messages: List[EmailMessage] = []
    for idx, block in enumerate(email_blocks, start=1):
        clean_block = block.strip()
        if not clean_block or "From:" not in clean_block:
            continue
        msg = parse_raw_email(clean_block, msg_id=f"email_{idx:03d}")
        messages.append(msg)
    return messages


class LocalEmailReader:
    """Local drop-in replacement for GmailReader for offline testing, PoC, and pipelines.

    Loads raw emails from a local file (.json, .md, .eml) or directory of .eml files
    and provides the exact same API as GmailReader (`fetch_messages`, `get_message`, `list_message_summaries`).
    """

    def __init__(self, data_source: Union[str, Path] = "data/spam-indian-bank-emails.json") -> None:
        self.data_source = Path(data_source)
        self._messages: List[EmailMessage] = []
        self._load()

    def _load(self) -> None:
        source = self.data_source
        if not source.exists():
            repo_root = Path(__file__).resolve().parent.parent.parent
            if (repo_root / source).exists():
                source = repo_root / source

        if source.is_dir():
            def _eml_sort_key(p: Path) -> Any:
                return (0, int(p.stem)) if p.stem.isdigit() else (1, p.stem)

            eml_files = sorted(source.glob("*.eml"), key=_eml_sort_key)
            self._messages = [
                parse_raw_email(f.read_text(encoding="utf-8"), msg_id=f.stem)
                for f in eml_files
            ]
        elif source.is_file():
            self._messages = load_emails_from_file(source)
        else:
            raise FileNotFoundError(f"Local email data source not found: {self.data_source}")

    def list_message_summaries(
        self, query: str = "", max_results: Optional[int] = None, user_id: str = "me"
    ) -> List[Dict[str, str]]:
        """List summary dictionaries for available local messages."""
        results = [
            {"id": msg.id, "threadId": msg.thread_id, "subject": msg.subject}
            for msg in self._messages
        ]
        if max_results:
            return results[:max_results]
        return results

    def get_message(self, message_id: str, user_id: str = "me") -> EmailMessage:
        """Retrieve a specific message by its ID."""
        for msg in self._messages:
            if msg.id == message_id:
                return msg
        raise KeyError(f"Message ID '{message_id}' not found in local dataset.")

    def fetch_messages(
        self, query: str = "", max_results: Optional[int] = None, user_id: str = "me"
    ) -> List[EmailMessage]:
        """Return all parsed EmailMessage instances."""
        if max_results:
            return self._messages[:max_results]
        return list(self._messages)
