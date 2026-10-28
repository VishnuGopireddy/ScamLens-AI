"""Investigation API endpoint."""

from __future__ import annotations

from typing import Any, Dict

from scamlens.core.models import IncidentStage, InvestigationSubmission
from scamlens.investigator.engine import ScamInvestigator

_investigator = ScamInvestigator()


def handle_investigate_request(payload: Dict[str, Any]) -> Dict[str, Any]:
    """Execute investigation for an incoming payload dictionary."""
    stage_str = payload.get("incident_stage", "PRE_ACTION")
    try:
        stage = IncidentStage(stage_str)
    except Exception:
        stage = IncidentStage.PRE_ACTION

    submission = InvestigationSubmission(
        text=payload.get("text"),
        image_paths=payload.get("image_paths", []),
        urls=payload.get("urls", []),
        qr_payloads=payload.get("qr_payloads", []),
        context_description=payload.get("context_description"),
        incident_stage=stage,
        user_region=payload.get("user_region", "IN"),
    )

    result = _investigator.investigate(submission)
    return result.to_dict()

