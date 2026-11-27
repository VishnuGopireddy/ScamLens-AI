"""FastAPI Application entrypoint for ScamLens-AI."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, Optional

from scamlens.api.routes.architecture import get_architecture_details
from scamlens.api.routes.emails import (
    get_gmail_status,
    get_registry_info,
    get_sample_cases,
    list_gmail_emails,
    list_local_emails,
)
from scamlens.api.routes.health import health_check
from scamlens.api.routes.investigate import (
    handle_email_investigate_request,
    handle_investigate_request,
)
from scamlens.core.config import get_settings

try:
    from fastapi import FastAPI, HTTPException
    from fastapi.middleware.cors import CORSMiddleware
    from fastapi.responses import FileResponse
    from fastapi.staticfiles import StaticFiles

    FASTAPI_AVAILABLE = True
except ImportError:
    FASTAPI_AVAILABLE = False

_UI_STATIC_DIR = Path(__file__).resolve().parents[2] / "GUI" / "static"


def create_app():
    """Create and configure the FastAPI web application."""
    if not FASTAPI_AVAILABLE:
        return None

    settings = get_settings()

    app = FastAPI(
        title="ScamLens-AI API",
        description="Multimodal Agentic AI for Scam Detection, Investigation and Response",
        version="0.1.0",
        docs_url="/docs" if settings.debug else None,
        redoc_url="/redoc" if settings.debug else None,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    if _UI_STATIC_DIR.is_dir():
        app.mount("/static", StaticFiles(directory=str(_UI_STATIC_DIR)), name="static")

    @app.get("/")
    def root():
        index_file = _UI_STATIC_DIR / "index.html"
        if index_file.is_file():
            return FileResponse(str(index_file))
        return {
            "message": "Welcome to ScamLens-AI API. Use /docs for OpenAPI documentation or /health for status.",
            "version": "0.1.0",
        }

    @app.get("/health")
    @app.get("/api/v1/health")
    def health():
        return health_check()

    @app.get("/api/v1/samples")
    def samples():
        return {"samples": get_sample_cases()}

    @app.get("/api/v1/registry")
    def registry():
        return get_registry_info()

    @app.get("/api/v1/architecture")
    def architecture():
        return get_architecture_details()

    @app.get("/api/v1/emails/local")
    def local_emails(source: Optional[str] = None, max_results: Optional[int] = None):
        try:
            return list_local_emails(source=source, max_results=max_results)
        except Exception as exc:
            raise HTTPException(status_code=400, detail=str(exc))

    @app.get("/api/v1/emails/gmail/status")
    def gmail_status():
        return get_gmail_status()

    @app.get("/api/v1/emails/gmail")
    def gmail_emails(query: str = "is:unread", max_results: int = 10):
        try:
            return list_gmail_emails(query=query, max_results=max_results)
        except Exception as exc:
            raise HTTPException(status_code=400, detail=str(exc))

    @app.post("/api/v1/investigate")
    def investigate(payload: Dict[str, Any], strategy: Optional[str] = None):
        try:
            return handle_investigate_request(payload, strategy=strategy)
        except Exception as exc:
            raise HTTPException(status_code=400, detail=str(exc))

    @app.post("/api/v1/investigate/email")
    def investigate_email(payload: Dict[str, Any], strategy: Optional[str] = None):
        try:
            return handle_email_investigate_request(payload, strategy=strategy)
        except Exception as exc:
            raise HTTPException(status_code=400, detail=str(exc))

    return app


app = create_app()
