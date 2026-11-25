"""Investigation API endpoint handlers (multimodal & email)."""

from __future__ import annotations

import base64
import tempfile
import time
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional

from scamlens.api.routes.emails import get_gmail_email_message, get_local_email_message
from scamlens.core.config import get_settings
from scamlens.core.models import IncidentStage, InvestigationSubmission
from scamlens.extractors.email import EmailMessage, parse_raw_email
from scamlens.investigator.engine import ProgressCallback, ScamInvestigator

_investigator = ScamInvestigator()
_ALLOWED_IMAGE_EXTS = {".png", ".jpg", ".jpeg", ".webp", ".gif", ".bmp"}


def _parse_stage(stage_str: Any) -> IncidentStage:
    try:
        return IncidentStage(str(stage_str))
    except Exception:
        return IncidentStage.PRE_ACTION


def _materialize_uploaded_images(
    uploaded_images: List[Dict[str, Any]],
    temp_dir: Path,
) -> List[str]:
    """Decode base64-encoded uploaded screenshots to temporary files safely."""
    settings = get_settings()
    max_bytes = settings.max_image_upload_mb * 1024 * 1024
    saved_paths: List[str] = []

    for idx, item in enumerate(uploaded_images):
        if not isinstance(item, dict):
            continue
        raw_b64 = str(item.get("data_base64") or item.get("content") or "").strip()
        if not raw_b64:
            continue
        if "," in raw_b64 and raw_b64.lower().startswith("data:"):
            raw_b64 = raw_b64.split(",", 1)[1]

        try:
            decoded = base64.b64decode(raw_b64, validate=True)
        except Exception as exc:
            raise ValueError(f"Invalid base64 image payload for upload #{idx + 1}: {exc}") from exc

        if len(decoded) > max_bytes:
            raise ValueError(
                f"Uploaded image #{idx + 1} exceeds {settings.max_image_upload_mb} MB limit."
            )

        orig_name = Path(str(item.get("filename") or f"upload_{idx + 1}.png")).name
        ext = Path(orig_name).suffix.lower()
        if ext not in _ALLOWED_IMAGE_EXTS:
            ext = ".png"
        safe_path = temp_dir / f"img_{idx + 1}{ext}"
        safe_path.write_bytes(decoded)
        saved_paths.append(str(safe_path))

    return saved_paths


def handle_investigate_request(
    payload: Dict[str, Any],
    strategy: Optional[str] = None,
    on_progress: ProgressCallback = None,
) -> Dict[str, Any]:
    """Execute investigation for an incoming payload dictionary."""
    stage = _parse_stage(payload.get("incident_stage", "PRE_ACTION"))
    resolved_strategy = (strategy or payload.get("strategy") or "linear").lower()

    uploaded_images = payload.get("uploaded_images") or []
    explicit_paths = list(payload.get("image_paths", []) or [])

    if uploaded_images:
        with tempfile.TemporaryDirectory(prefix="scamlens_ui_") as tmp_dir:
            temp_paths = _materialize_uploaded_images(uploaded_images, Path(tmp_dir))
            submission = InvestigationSubmission(
                text=payload.get("text"),
                image_paths=explicit_paths + temp_paths,
                urls=payload.get("urls", []) or [],
                qr_payloads=payload.get("qr_payloads", []) or [],
                context_description=payload.get("context_description"),
                incident_stage=stage,
                user_region=payload.get("user_region", "IN"),
            )
            result = _investigator.investigate(
                submission, strategy=resolved_strategy, on_progress=on_progress
            )
            return result.to_dict()

    submission = InvestigationSubmission(
        text=payload.get("text"),
        image_paths=explicit_paths,
        urls=payload.get("urls", []) or [],
        qr_payloads=payload.get("qr_payloads", []) or [],
        context_description=payload.get("context_description"),
        incident_stage=stage,
        user_region=payload.get("user_region", "IN"),
    )

    result = _investigator.investigate(
        submission, strategy=resolved_strategy, on_progress=on_progress
    )
    return result.to_dict()


def handle_email_investigate_request(
    payload: Dict[str, Any],
    strategy: Optional[str] = None,
    on_progress: ProgressCallback = None,
) -> Dict[str, Any]:
    """Read, parse, and investigate an email from local dataset, Gmail, or raw MIME text."""
    source = str(payload.get("source") or "local").lower()
    stage = _parse_stage(payload.get("incident_stage", "PRE_ACTION"))
    resolved_strategy = (strategy or payload.get("strategy") or "linear").lower()

    def _emit(stage_name: str, message: str, detail: Optional[str] = None, data: Optional[Dict[str, Any]] = None) -> None:
        if on_progress is None:
            return
        event: Dict[str, Any] = {
            "stage": stage_name,
            "message": message,
            "timestamp": time.strftime("%H:%M:%S"),
        }
        if detail:
            event["detail"] = detail
        if data is not None:
            event["data"] = data
        on_progress(event)

    email_msg: EmailMessage
    if source == "local":
        email_id = str(payload.get("email_id") or "").strip()
        if not email_id:
            raise ValueError("'email_id' is required when source='local'.")
        _emit(
            "reading_email",
            f"Reading email '{email_id}' from local dataset...",
            detail=f"Source: {payload.get('dataset_source') or 'default local dataset'}",
        )
        email_msg = get_local_email_message(email_id, source=payload.get("dataset_source"))
    elif source == "gmail":
        email_id = str(payload.get("email_id") or "").strip()
        if not email_id:
            raise ValueError("'email_id' is required when source='gmail'.")
        _emit(
            "reading_email",
            f"Connecting to Gmail REST API & reading message '{email_id}'...",
        )
        email_msg = get_gmail_email_message(email_id)
    elif source == "raw":
        raw_eml = str(payload.get("raw_eml") or "").strip()
        if not raw_eml:
            raise ValueError("'raw_eml' content is required when source='raw'.")
        _emit("reading_email", "Reading submitted RFC 5322 / .eml raw message...")
        email_msg = parse_raw_email(raw_eml, msg_id=payload.get("email_id") or "raw_ui_email")
    else:
        raise ValueError(f"Unsupported email source '{source}'. Expected 'local', 'gmail', or 'raw'.")

    _emit(
        "email_parsed",
        f"Parsed email: \"{email_msg.subject}\" from {email_msg.sender or email_msg.sender_email}",
        detail=(
            f"SPF={email_msg.spf_status.upper()} | DKIM={email_msg.dkim_status.upper()} | "
            f"DMARC={email_msg.dmarc_status.upper()} | URLs={len(email_msg.extracted_urls)} | "
            f"Attachments={len(email_msg.attachments)}"
        ),
        data={"email": email_msg.to_dict()},
    )

    result = _investigator.investigate_email(
        email_msg,
        incident_stage=stage,
        strategy=resolved_strategy,
        on_progress=on_progress,
    )
    return {
        "email": email_msg.to_dict(),
        "investigation": result.to_dict(),
    }
