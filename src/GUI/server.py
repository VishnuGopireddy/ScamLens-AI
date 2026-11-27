"""Zero-dependency HTTP + Server-Sent Events (SSE) GUI server for ScamLens-AI.

Serves the interactive web interface and streams real-time step-by-step
investigation updates (reading email, parsing email, analyzing URLs, tool calls,
and final results) using Python's standard library ThreadingHTTPServer.
"""

from __future__ import annotations

import json
import logging
import mimetypes
import queue
import threading
import time
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any, Dict, Optional
from urllib.parse import parse_qs, urlparse

from scamlens.api.routes.architecture import get_architecture_details
from scamlens.api.routes.emails import (
    build_non_interactive_gmail_reader,
    clear_email_caches,
    get_gmail_status,
    get_registry_info,
    get_sample_cases,
    list_gmail_emails,
    list_local_emails,
    resolve_default_local_email_source,
)
from scamlens.api.routes.health import health_check
from scamlens.api.routes.investigate import (
    handle_email_investigate_request,
    handle_investigate_request,
)
from scamlens.core.config import clear_settings_cache
from scamlens.core.models import IncidentStage
from scamlens.extractors.email import LocalEmailReader
from scamlens.investigator.engine import ScamInvestigator

logger = logging.getLogger(__name__)

_STATIC_DIR = Path(__file__).resolve().parent / "static"


def _format_sse(event_name: str, data: Dict[str, Any]) -> bytes:
    """Format a Server-Sent Event frame."""
    payload = json.dumps(data, ensure_ascii=False)
    return f"event: {event_name}\ndata: {payload}\n\n".encode("utf-8")


class ScamLensGUIHandler(BaseHTTPRequestHandler):
    """HTTP + SSE request handler for the ScamLens-AI GUI."""

    protocol_version = "HTTP/1.1"
    server_version = "ScamLensGUI/0.1"

    def log_message(self, format: str, *args: Any) -> None:
        logger.debug("GUI HTTP: " + format, *args)

    def _send_cors_headers(self) -> None:
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")

    def _send_json(self, status: int, data: Any) -> None:
        body = json.dumps(data, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self._send_cors_headers()
        self.end_headers()
        self.wfile.write(body)

    def _send_static_file(self, file_path: Path) -> None:
        if not file_path.is_file():
            self._send_json(HTTPStatus.NOT_FOUND, {"error": f"File not found: {file_path.name}"})
            return
        mime_type, _ = mimetypes.guess_type(str(file_path))
        content = file_path.read_bytes()
        self.send_response(HTTPStatus.OK)
        self.send_header("Content-Type", f"{mime_type or 'application/octet-stream'}; charset=utf-8")
        self.send_header("Content-Length", str(len(content)))
        self.send_header("Cache-Control", "no-store")
        self._send_cors_headers()
        self.end_headers()
        self.wfile.write(content)

    def _read_json_body(self) -> Dict[str, Any]:
        length_str = self.headers.get("Content-Length", "0")
        try:
            length = int(length_str)
        except ValueError:
            length = 0
        if length <= 0:
            return {}
        raw = self.rfile.read(length)
        if not raw:
            return {}
        parsed = json.loads(raw.decode("utf-8"))
        if not isinstance(parsed, dict):
            raise ValueError("JSON request body must be an object.")
        return parsed

    def _stream_sse_worker(self, worker_fn: Any) -> None:
        """Run a blocking investigation worker in a thread and stream SSE events live."""
        self.send_response(HTTPStatus.OK)
        self.send_header("Content-Type", "text/event-stream; charset=utf-8")
        self.send_header("Cache-Control", "no-cache")
        self.send_header("Connection", "close")
        self._send_cors_headers()
        self.end_headers()

        event_queue: "queue.Queue[Optional[tuple[str, Dict[str, Any]]]]" = queue.Queue()

        def emit(event_name: str, data: Dict[str, Any]) -> None:
            event_queue.put((event_name, data))

        def runner() -> None:
            try:
                worker_fn(emit)
            except Exception as exc:
                emit(
                    "error",
                    {
                        "message": str(exc),
                        "timestamp": time.strftime("%H:%M:%S"),
                    },
                )
            finally:
                event_queue.put(None)

        thread = threading.Thread(target=runner, daemon=True)
        thread.start()

        while True:
            try:
                item = event_queue.get(timeout=15.0)
            except queue.Empty:
                # Keepalive comment so browser EventSource/fetch stays alive on slow LLM calls
                try:
                    self.wfile.write(b": keepalive\n\n")
                    self.wfile.flush()
                except OSError:
                    break
                continue

            if item is None:
                break

            event_name, data = item
            try:
                self.wfile.write(_format_sse(event_name, data))
                self.wfile.flush()
            except OSError:
                break

        self.close_connection = True

    def do_OPTIONS(self) -> None:  # noqa: N802
        self.send_response(HTTPStatus.NO_CONTENT)
        self._send_cors_headers()
        self.send_header("Content-Length", "0")
        self.end_headers()

    def do_GET(self) -> None:  # noqa: N802
        parsed = urlparse(self.path)
        path = parsed.path
        params = parse_qs(parsed.query)

        if path in ("/", "/index.html"):
            self._send_static_file(_STATIC_DIR / "index.html")
            return

        if path.startswith("/static/"):
            rel = path[len("/static/"):]
            candidate = (_STATIC_DIR / rel).resolve()
            if not candidate.is_relative_to(_STATIC_DIR.resolve()):
                self._send_json(HTTPStatus.FORBIDDEN, {"error": "Invalid static path"})
                return
            self._send_static_file(candidate)
            return

        if path in ("/health", "/api/v1/health"):
            self._send_json(HTTPStatus.OK, health_check())
            return

        if path == "/api/v1/samples":
            self._send_json(HTTPStatus.OK, {"samples": get_sample_cases()})
            return

        if path == "/api/v1/registry":
            self._send_json(HTTPStatus.OK, get_registry_info())
            return

        if path == "/api/v1/architecture":
            self._send_json(HTTPStatus.OK, get_architecture_details())
            return

        if path == "/api/v1/emails/local":
            try:
                source = params.get("source", [None])[0]
                max_res_raw = params.get("max_results", [None])[0]
                max_res = int(max_res_raw) if max_res_raw else None
                self._send_json(HTTPStatus.OK, list_local_emails(source=source, max_results=max_res))
            except Exception as exc:
                self._send_json(HTTPStatus.BAD_REQUEST, {"detail": str(exc)})
            return

        if path == "/api/v1/emails/gmail/status":
            self._send_json(HTTPStatus.OK, get_gmail_status())
            return

        if path == "/api/v1/emails/gmail":
            try:
                query = params["query"][0] if "query" in params else "-in:trash -in:drafts"
                max_res = int(params.get("max_results", ["10"])[0])
                include_spam = params.get("include_spam_trash", ["true"])[0].lower() in ("1", "true", "yes")
                self._send_json(
                    HTTPStatus.OK,
                    list_gmail_emails(query=query, max_results=max_res, include_spam_trash=include_spam),
                )
            except Exception as exc:
                self._send_json(HTTPStatus.BAD_REQUEST, {"detail": str(exc)})
            return

        self._send_json(HTTPStatus.NOT_FOUND, {"error": f"Route not found: {path}"})

    def do_POST(self) -> None:  # noqa: N802
        parsed = urlparse(self.path)
        path = parsed.path
        params = parse_qs(parsed.query)
        strategy_q = params.get("strategy", [None])[0]

        try:
            payload = self._read_json_body()
        except Exception as exc:
            self._send_json(HTTPStatus.BAD_REQUEST, {"detail": f"Invalid JSON body: {exc}"})
            return

        if path == "/api/v1/cache/clear":
            clear_email_caches()
            clear_settings_cache()
            self._send_json(
                HTTPStatus.OK,
                {
                    "status": "cleared",
                    "health": health_check(),
                    "gmail": get_gmail_status(),
                },
            )
            return

        if path == "/api/v1/investigate":
            try:
                result = handle_investigate_request(payload, strategy=strategy_q)
                self._send_json(HTTPStatus.OK, result)
            except Exception as exc:
                self._send_json(HTTPStatus.BAD_REQUEST, {"detail": str(exc)})
            return

        if path == "/api/v1/investigate/email":
            try:
                result = handle_email_investigate_request(payload, strategy=strategy_q)
                self._send_json(HTTPStatus.OK, result)
            except Exception as exc:
                self._send_json(HTTPStatus.BAD_REQUEST, {"detail": str(exc)})
            return

        if path == "/api/v1/investigate/stream":
            def _worker(emit: Any) -> None:
                emit(
                    "status",
                    {
                        "stage": "started",
                        "message": "Starting ScamLens-AI multimodal investigation...",
                        "timestamp": time.strftime("%H:%M:%S"),
                    },
                )
                result = handle_investigate_request(
                    payload,
                    strategy=strategy_q,
                    on_progress=lambda ev: emit("status", ev),
                )
                emit("result", {"investigation": result})

            self._stream_sse_worker(_worker)
            return

        if path == "/api/v1/investigate/email/stream":
            def _email_worker(emit: Any) -> None:
                emit(
                    "status",
                    {
                        "stage": "started",
                        "message": "Initializing email forensic pipeline...",
                        "timestamp": time.strftime("%H:%M:%S"),
                    },
                )
                result = handle_email_investigate_request(
                    payload,
                    strategy=strategy_q,
                    on_progress=lambda ev: emit("status", ev),
                )
                emit("result", result)

            self._stream_sse_worker(_email_worker)
            return

        if path == "/api/v1/emails/scan/stream":
            def _scan_worker(emit: Any) -> None:
                source = str(payload.get("source") or "local").lower()
                raw_query = payload.get("query")
                query = "-in:trash -in:drafts" if raw_query is None else str(raw_query)
                include_spam_trash = bool(payload.get("include_spam_trash", True))
                max_results = max(1, min(int(payload.get("max_results") or 5), 25))
                strategy = (strategy_q or payload.get("strategy") or "orchestrator").lower()
                stage_str = str(payload.get("incident_stage") or "PRE_ACTION")
                try:
                    stage = IncidentStage(stage_str)
                except Exception:
                    stage = IncidentStage.PRE_ACTION

                investigator = ScamInvestigator()

                if source == "gmail":
                    raw_known = payload.get("known_ids") or []
                    known_ids = {str(x) for x in raw_known if x}
                    emit(
                        "status",
                        {
                            "stage": "reading_inbox",
                            "message": f"Connecting to Gmail REST API (query='{query}', max={max_results})...",
                            "timestamp": time.strftime("%H:%M:%S"),
                        },
                    )
                    reader = build_non_interactive_gmail_reader()
                    connected_email: Optional[str] = None
                    try:
                        connected_email = reader.get_profile_email()
                    except Exception:
                        connected_email = None
                    summaries = reader.list_message_summaries(
                        query=query,
                        max_results=max_results,
                        include_spam_trash=include_spam_trash,
                    )
                    pending = [
                        item for item in summaries
                        if item.get("id") and item["id"] not in known_ids
                    ]
                    total = len(pending)
                    emit(
                        "status",
                        {
                            "stage": "inbox_listed",
                            "message": (
                                f"Found {total} new Gmail message(s) ({len(summaries)} total matching '{query}')"
                                if known_ids
                                else f"Found {total} Gmail message(s) matching '{query}'"
                            ),
                            "timestamp": time.strftime("%H:%M:%S"),
                            "data": {
                                "total": len(summaries),
                                "new_count": total,
                                "connected_email": connected_email,
                            },
                        },
                    )
                    for idx, item in enumerate(pending, 1):
                        msg_id = item["id"]
                        emit(
                            "status",
                            {
                                "stage": "reading_email",
                                "message": f"[{idx}/{total}] Reading Gmail message {msg_id}...",
                                "timestamp": time.strftime("%H:%M:%S"),
                            },
                        )
                        msg = reader.get_message(msg_id)
                        emit(
                            "status",
                            {
                                "stage": "email_parsed",
                                "message": f"[{idx}/{total}] Parsed email: \"{msg.subject}\" from {msg.sender or msg.sender_email}",
                                "detail": f"SPF={msg.spf_status.upper()} | DKIM={msg.dkim_status.upper()} | DMARC={msg.dmarc_status.upper()} | {len(msg.extracted_urls)} URL(s)",
                                "timestamp": time.strftime("%H:%M:%S"),
                                "data": {"email": msg.to_dict(), "index": idx, "total": total},
                            },
                        )
                        res = investigator.investigate_email(
                            msg,
                            incident_stage=stage,
                            strategy=strategy,
                            on_progress=lambda ev: emit("status", ev),
                        )
                        emit(
                            "email_result",
                            {
                                "index": idx,
                                "total": total,
                                "email": msg.to_dict(),
                                "investigation": res.to_dict(),
                            },
                        )
                    emit(
                        "scan_complete",
                        {
                            "message": (
                                f"Poll complete: {total} new Gmail message(s) scanned."
                                if known_ids
                                else "Inbox scan complete."
                            ),
                            "timestamp": time.strftime("%H:%M:%S"),
                            "new_count": total,
                            "total": len(summaries),
                        },
                    )
                    return
                else:
                    resolved = resolve_default_local_email_source(payload.get("dataset_source"))
                    emit(
                        "status",
                        {
                            "stage": "reading_inbox",
                            "message": f"Reading local email dataset ({resolved.name})...",
                            "timestamp": time.strftime("%H:%M:%S"),
                        },
                    )
                    local_reader = LocalEmailReader(resolved)
                    msgs = local_reader.fetch_messages(max_results=max_results)
                    total = len(msgs)
                    emit(
                        "status",
                        {
                            "stage": "inbox_listed",
                            "message": f"Loaded {total} local email(s) for batch forensic scan",
                            "timestamp": time.strftime("%H:%M:%S"),
                            "data": {"total": total},
                        },
                    )
                    for idx, msg in enumerate(msgs, 1):
                        emit(
                            "status",
                            {
                                "stage": "email_parsed",
                                "message": f"[{idx}/{total}] Parsed email: \"{msg.subject}\" from {msg.sender or msg.sender_email}",
                                "detail": f"SPF={msg.spf_status.upper()} | DKIM={msg.dkim_status.upper()} | DMARC={msg.dmarc_status.upper()} | {len(msg.extracted_urls)} URL(s)",
                                "timestamp": time.strftime("%H:%M:%S"),
                                "data": {"email": msg.to_dict(), "index": idx, "total": total},
                            },
                        )
                        res = investigator.investigate_email(
                            msg,
                            incident_stage=stage,
                            strategy=strategy,
                            on_progress=lambda ev: emit("status", ev),
                        )
                        emit(
                            "email_result",
                            {
                                "index": idx,
                                "total": total,
                                "email": msg.to_dict(),
                                "investigation": res.to_dict(),
                            },
                        )

                emit(
                    "scan_complete",
                    {
                        "message": "Inbox scan complete.",
                        "timestamp": time.strftime("%H:%M:%S"),
                    },
                )

            self._stream_sse_worker(_scan_worker)
            return

        self._send_json(HTTPStatus.NOT_FOUND, {"error": f"Route not found: {path}"})


def create_gui_server(host: str = "127.0.0.1", port: int = 8080) -> ThreadingHTTPServer:
    """Create a configured ThreadingHTTPServer for the ScamLens-AI GUI."""
    ThreadingHTTPServer.allow_reuse_address = True
    return ThreadingHTTPServer((host, port), ScamLensGUIHandler)


def run_gui_server(host: str = "127.0.0.1", port: int = 8080) -> None:
    """Start the blocking ScamLens-AI GUI HTTP + SSE server."""
    server = create_gui_server(host=host, port=port)
    actual_host, actual_port = server.server_address[:2]
    print(f"ScamLens-AI GUI running at http://{actual_host}:{actual_port}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nShutting down ScamLens-AI GUI...")
    finally:
        server.server_close()
