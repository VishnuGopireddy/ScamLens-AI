"""FastAPI Application entrypoint for ScamLens-AI."""

from __future__ import annotations

from typing import Any, Dict

from scamlens.api.routes.health import health_check
from scamlens.api.routes.investigate import handle_investigate_request
from scamlens.core.config import get_settings

try:
    from fastapi import FastAPI, HTTPException
    from fastapi.middleware.cors import CORSMiddleware
    FASTAPI_AVAILABLE = True
except ImportError:
    FASTAPI_AVAILABLE = False


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

    @app.get("/")
    def root():
        return {
            "message": "Welcome to ScamLens-AI API. Use /docs for OpenAPI documentation or /health for status.",
            "version": "0.1.0",
        }

    @app.get("/health")
    def health():
        return health_check()

    @app.post("/api/v1/investigate")
    def investigate(payload: Dict[str, Any]):
        try:
            return handle_investigate_request(payload)
        except Exception as exc:
            raise HTTPException(status_code=400, detail=str(exc))

    return app


app = create_app()

