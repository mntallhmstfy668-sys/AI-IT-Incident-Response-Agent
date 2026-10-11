
from typing import Any

from agents.diagnostic_workers import run_diagnostic_checks
from agents.triage_agent import triage_incident
from guardrails.safety_filters import requires_human_approval
from models.schemas import IncidentReport


def orchestrate_incident(
    incident: IncidentReport,
) -> dict[str, Any]:
    """
    Coordinate incident triage, diagnostics, and escalation.

    This initial implementation uses deterministic Python routing.
    It does not execute remediation actions.
    """

    # Step 1: Classify the incident.
    triage = triage_incident(incident)

    # Step 2: Decide whether human review is required.
    human_review_required = (
        triage.requires_human
        or requires_human_approval(
            action=triage.recommended_action,
            priority=triage.priority,
        )
    )

    # Step 3: Route the incident to the appropriate diagnostic worker.
    # Skip automated diagnostics when the request requires human review.
    if human_review_required:
        diagnostic_result = {
            "incident_id": incident.incident_id,
            "status": "skipped_pending_human_review",
            "message": (
                "Automated diagnostic routing was paused. "
                "Human review is required before proceeding."
            ),
            "automated_changes_performed": False,
        }
    else:
        diagnostic_result = run_diagnostic_checks(incident)

    # Step 4: Return a structured summary for the next agent or UI.
    return {
        "incident_id": incident.incident_id,
        "triage": triage.model_dump(),
        "diagnostics": diagnostic_result,
        "requires_human": human_review_required,
        "status": (
            "pending_human_review"
            if human_review_required
            else "diagnostics_prepared"
        ),
        "resolution_applied": False,
        "next_step": (
            "Escalate to the appropriate IT team for human review."
            if human_review_required
            else triage.recommended_action
        ),
    }
