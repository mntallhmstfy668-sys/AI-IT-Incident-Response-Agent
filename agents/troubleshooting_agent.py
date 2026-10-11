
from typing import Any

from guardrails.safety_filters import (
    check_output_safety,
    requires_human_approval,
)
from models.schemas import IncidentReport, TriageResult


def suggest_troubleshooting_steps(
    incident: IncidentReport,
    triage: TriageResult,
    diagnostic_result: dict[str, Any],
) -> dict[str, Any]:
    """
    Suggest safe troubleshooting steps based on triage and diagnostics.

    This function provides recommendations only. It does not execute
    remediation actions or close incidents.
    """

    # Critical incidents and security issues must be escalated.
    if (
        triage.priority == "critical"
        or triage.category == "security"
        or triage.requires_human
        or requires_human_approval(
            action=triage.recommended_action,
            priority=triage.priority,
        )
    ):
        return {
            "incident_id": incident.incident_id,
            "status": "escalation_required",
            "steps": [
                "Escalate the incident to the appropriate IT or security team.",
                "Preserve relevant logs and error messages.",
                "Do not perform sensitive changes without authorization.",
                "Keep the incident open until an authorized person reviews it.",
            ],
            "requires_human": True,
            "resolution_applied": False,
        }

    # Provide recommendations based on the incident category.
    troubleshooting_steps = {
        "network": [
            "Check whether other users are experiencing the same issue.",
            "Review the network status and any known outages.",
            "Check the affected device's network connection.",
            "Escalate if the issue affects multiple users or persists.",
        ],
        "vpn": [
            "Confirm that the device has a working internet connection.",
            "Check the VPN service status using approved IT tools.",
            "Record the exact VPN error message.",
            "Escalate persistent connection failures to IT support.",
        ],
        "account": [
            "Verify account status using an approved IT support tool.",
            "Review the authentication error message.",
            "Follow the organization's approved account recovery process.",
            "Never ask the user to share their password.",
        ],
        "device": [
            "Identify the device and record the reported symptoms.",
            "Review device health information using approved tools.",
            "Check for relevant error messages.",
            "Escalate suspected hardware failures to IT support.",
        ],
        "software": [
            "Record the application name and exact error message.",
            "Check the approved IT knowledge base for known issues.",
            "Determine whether the problem affects other users.",
            "Escalate persistent failures to the application support team.",
        ],
        "other": [
            "Collect additional details about the problem.",
            "Search the approved IT knowledge base.",
            "Record any error messages and when the issue started.",
            "Escalate if the cause remains unclear.",
        ],
    }

    steps = troubleshooting_steps.get(
        triage.category,
        troubleshooting_steps["other"],
    )

    # Check the generated recommendations before returning them.
    output_text = " ".join(steps)
    is_safe, safety_reason = check_output_safety(output_text)

    if not is_safe:
        return {
            "incident_id": incident.incident_id,
            "status": "safety_review_required",
            "steps": [
                "Pause the troubleshooting workflow.",
                "Ask an authorized human to review the recommendations.",
            ],
            "requires_human": True,
            "safety_reason": safety_reason,
            "resolution_applied": False,
        }

    return {
        "incident_id": incident.incident_id,
        "status": "recommendations_ready",
        "steps": steps,
        "diagnostic_information": diagnostic_result,
        "requires_human": False,
        "resolution_applied": False,
        "message": (
            "These are recommendations only. "
            "No changes have been made to IT systems."
        ),
    }
