"""Email access, trusted registry, and benchmark sample route handlers."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List, Optional

from scamlens.core.config import get_settings
from scamlens.extractors.email import EmailMessage, GmailAuthManager, GmailReader, LocalEmailReader
from scamlens.rag.knowledge_base import RegionalKnowledgeBase

_PROJECT_ROOT = Path(__file__).resolve().parents[4]


def _resolve_repo_path(path_str: str) -> Path:
    path = Path(path_str)
    if not path.is_absolute():
        return _PROJECT_ROOT / path
    return path


def resolve_default_local_email_source(source: Optional[str] = None) -> Path:
    """Resolve local email dataset path (preferring data/raw_emails, falling back to JSON)."""
    if source:
        candidate = _resolve_repo_path(source)
        if candidate.exists():
            return candidate
        raise FileNotFoundError(f"Local email source not found: {source}")

    raw_dir = _PROJECT_ROOT / "data" / "raw_emails"
    if raw_dir.is_dir() and any(raw_dir.glob("*.eml")):
        return raw_dir

    json_file = _PROJECT_ROOT / "data" / "spam-indian-bank-emails.json"
    if json_file.is_file():
        return json_file

    raise FileNotFoundError("No local email dataset found under data/raw_emails or data/spam-indian-bank-emails.json")


def list_local_emails(
    source: Optional[str] = None,
    max_results: Optional[int] = None,
) -> Dict[str, Any]:
    """Load and summarize emails from local .eml or .json datasets."""
    resolved = resolve_default_local_email_source(source)
    reader = LocalEmailReader(resolved)
    messages = reader.fetch_messages(max_results=max_results)
    return {
        "source": str(resolved.relative_to(_PROJECT_ROOT)) if resolved.is_relative_to(_PROJECT_ROOT) else str(resolved),
        "count": len(messages),
        "emails": [msg.to_dict() for msg in messages],
    }


def get_local_email_message(email_id: str, source: Optional[str] = None) -> EmailMessage:
    """Retrieve a single local EmailMessage by ID."""
    resolved = resolve_default_local_email_source(source)
    reader = LocalEmailReader(resolved)
    return reader.get_message(email_id)


def get_gmail_status() -> Dict[str, Any]:
    """Inspect Gmail OAuth configuration and token state without blocking for consent."""
    settings = get_settings()
    cred_path = _resolve_repo_path(settings.gmail_credentials_file)
    token_path = _resolve_repo_path(settings.gmail_token_file)
    scopes = [s.strip() for s in settings.gmail_scopes.split(",") if s.strip()]

    token_valid = False
    token_expired = False
    has_refresh_token = False
    status_note = "Not authenticated"

    if token_path.is_file():
        try:
            from google.oauth2.credentials import Credentials

            creds = Credentials.from_authorized_user_file(str(token_path), scopes)
            token_valid = bool(creds.valid)
            token_expired = bool(creds.expired)
            has_refresh_token = bool(creds.refresh_token)
            if token_valid:
                status_note = "OAuth token valid"
            elif token_expired and has_refresh_token:
                status_note = "OAuth token expired (refreshable)"
            else:
                status_note = "OAuth token invalid or missing refresh token"
        except ImportError:
            status_note = "google-auth libraries not installed"
        except Exception as exc:
            status_note = f"Token parse error: {exc}"
    elif cred_path.is_file():
        status_note = "credentials.json present; token.json not created yet"
    else:
        status_note = "Neither credentials.json nor token.json found"

    return {
        "credentials_exists": cred_path.is_file(),
        "token_exists": token_path.is_file(),
        "token_valid": token_valid,
        "token_expired": token_expired,
        "refreshable": has_refresh_token,
        "ready": token_valid or (token_expired and has_refresh_token),
        "scopes": scopes,
        "status_note": status_note,
    }


def build_non_interactive_gmail_reader() -> GmailReader:
    """Build a GmailReader using cached/refreshable token.json without launching a browser OAuth server."""
    settings = get_settings()
    cred_path = _resolve_repo_path(settings.gmail_credentials_file)
    token_path = _resolve_repo_path(settings.gmail_token_file)
    scopes = [s.strip() for s in settings.gmail_scopes.split(",") if s.strip()]

    try:
        from google.auth.transport.requests import Request
        from google.oauth2.credentials import Credentials
        from googleapiclient.discovery import build
    except ImportError as exc:
        raise ImportError(
            "Gmail dependencies missing. Install with: pip install 'scamlens-ai[gmail]'"
        ) from exc

    if not token_path.is_file():
        raise RuntimeError(
            f"Gmail token file not found at '{token_path.name}'. "
            "Run 'python scripts/scan_gmail.py --max-results 1' in a terminal to complete one-time OAuth consent, "
            "or use the Local Email Dataset / Raw .eml tab."
        )

    creds = Credentials.from_authorized_user_file(str(token_path), scopes)
    if not creds.valid:
        if creds.expired and creds.refresh_token:
            creds.refresh(Request())
            token_path.write_text(creds.to_json(), encoding="utf-8")
        else:
            raise RuntimeError(
                "Cached Gmail OAuth token is invalid and cannot be refreshed automatically. "
                "Re-authenticate via 'python scripts/scan_gmail.py --max-results 1'."
            )

    service = build("gmail", "v1", credentials=creds)
    auth_manager = GmailAuthManager(
        credentials_file=str(cred_path),
        token_file=str(token_path),
        scopes=scopes,
    )
    return GmailReader(service=service, auth_manager=auth_manager)


def list_gmail_emails(query: str = "is:unread", max_results: int = 10) -> Dict[str, Any]:
    """Fetch and parse live Gmail messages matching a search query."""
    reader = build_non_interactive_gmail_reader()
    clamped = max(1, min(int(max_results), 25))
    messages = reader.fetch_messages(query=query or "is:unread", max_results=clamped)
    return {
        "source": "gmail",
        "query": query,
        "count": len(messages),
        "emails": [msg.to_dict() for msg in messages],
    }


def get_gmail_email_message(email_id: str) -> EmailMessage:
    """Fetch a single Gmail message by ID."""
    reader = build_non_interactive_gmail_reader()
    return reader.get_message(email_id)


def get_registry_info() -> Dict[str, Any]:
    """Return verified Indian banks, government services, and UPI safety guidelines."""
    kb = RegionalKnowledgeBase()
    return kb._data


def get_sample_cases() -> List[Dict[str, Any]]:
    """Return benchmark sample scenarios for quick testing in the GUI."""
    dataset_file = _PROJECT_ROOT / "benchmark" / "datasets" / "sample_cases.json"
    if not dataset_file.is_file():
        return []
    with open(dataset_file, "r", encoding="utf-8") as f:
        return json.load(f)
