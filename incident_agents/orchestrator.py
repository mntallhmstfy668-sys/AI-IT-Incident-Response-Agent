
import json

from agents import Agent, Runner, trace

from models.schemas import (
    IncidentReport,
    DiagnosticResult,
)
from incident_agents.triage_agent import triage_agent
from incident_agents.diagnostic_workers import (
    network_agent,
    account_agent,
    device_agent,
)
from incident_agents.troubleshooting_agent import (
    suggest_troubleshooting_steps,
    troubleshooting_agent,
)
from guardrails.safety_filters import (
    validate_incident_input,
    requires_human_approval,
    check_output_safety,
)


SECURITY_TERMS = (
    "unauthorized",
    "suspicious access",
    "phishing",
    "ransomware",
    "malware",
    "data breach",
    "stolen account",
)


# Keep the SDK orchestrator available with its specialist handoffs.
# The function below uses explicit sequential routing for predictability.
orchestrator_agent = Agent(
    name="IT Incident Orchestrator",
    instructions="""
    You coordinate IT incident response.

    Never invent findings or claim that a fix was applied.
    Critical and security incidents require human review.
    Specialist agents provide diagnostic information and safe recommendations.
    Never perform unauthorized actions or modify IT systems.
    """,
    handoffs=[
        triage_agent,
        network_agent,
        account_agent,
        device_agent,
        troubleshooting_agent,
    ],
)


def requires_human_review(incident: IncidentReport) -> bool:
    """Identify incidents that require human review before processing."""
    description = incident.description.lower()

    return (
        requires_human_approval(incident)
        or any(term in description for term in SECURITY_TERMS)
    )


def _human_review_result(
    incident_id: str,
    message: str,
    **extra,
) -> dict:
    """Build a consistent human-review response."""
    return {
        "incident_id": incident_id,
        "status": "pending_human_review",
        "requires_human": True,
        "resolution_applied": False,
        "message": message,
        **extra,
    }


def orchestrate_incident(incident: IncidentReport) -> dict:
    """Run triage, specialist diagnostics, and safe troubleshooting in order."""

    # 1. Validate input before calling any model.
    input_is_valid, input_message = validate_incident_input(incident)

    if not input_is_valid:
        return {
            "incident_id": incident.incident_id,
            "status": "input_rejected",
            "requires_human": True,
            "resolution_applied": False,
            "message": input_message,
        }

    # 2. Escalate obvious high-risk incidents before model processing.
    if requires_human_review(incident):
        return _human_review_result(
            incident.incident_id,
            "Human review is required before automated processing.",
        )

    try:
        with trace("IT Incident Response Workflow"):

            # 3. Triage first.
            triage_run = Runner.run_sync(
                triage_agent,
                incident.model_dump_json(),
            )
            triage = triage_run.final_output

            if not requires_human_approval(incident, triage):
                triage_is_safe, triage_safety_message = (
                    check_output_safety(
                        triage.recommended_action
                    )
                )
            else:
                triage_is_safe = False
                triage_safety_message = (
                    "Triage identified a high-risk incident."
                )

            if (
                not triage_is_safe
                or triage.category == "security"
                or triage.priority == "critical"
                or triage.requires_human
            ):
                return _human_review_result(
                    incident.incident_id,
                    "Triage requires authorized human review.",
                    triage=triage.model_dump(),
                    safety_reason=triage_safety_message,
                )

            # 4. Route to one diagnostic specialist using the triage result.
            diagnostic_agents = {
                "network": network_agent,
                "account": account_agent,
                "device": device_agent,
                "vpn": device_agent,
            }

            diagnostic_agent = diagnostic_agents.get(
                triage.category
            )

            if diagnostic_agent is None:
                diagnostic = DiagnosticResult(
                    incident_id=incident.incident_id,
                    category=triage.category,
                    checks=[],
                    findings=[
                        "No dedicated diagnostic specialist is configured "
                        "for this incident category."
                    ],
                    recommended_next_step=(
                        "Collect additional details and consult the "
                        "organization's approved IT support process."
                    ),
                    automated_changes_performed=False,
                )
            else:
                diagnostic_payload = {
                    "incident": incident.model_dump(),
                    "triage": triage.model_dump(),
                }

                diagnostic_run = Runner.run_sync(
                    diagnostic_agent,
                    json.dumps(
                        diagnostic_payload,
                        ensure_ascii=False,
                    ),
                )
                diagnostic = diagnostic_run.final_output

            diagnostic_data = diagnostic.model_dump()

            # 5. Check diagnostic output before generating recommendations.
            diagnostic_text = json.dumps(
                diagnostic_data,
                ensure_ascii=False,
            )
            diagnostic_is_safe, diagnostic_safety_message = (
                check_output_safety(diagnostic_text)
            )

            findings_text = " ".join(diagnostic.findings).lower()
            contains_security_finding = any(
                term in findings_text
                for term in SECURITY_TERMS
            )

            if (
                not diagnostic_is_safe
                or contains_security_finding
                or diagnostic.category == "security"
            ):
                return _human_review_result(
                    incident.incident_id,
                    "Diagnostic findings require human review.",
                    triage=triage.model_dump(),
                    diagnostic=diagnostic_data,
                    safety_reason=diagnostic_safety_message,
                )

            # 6. Generate safe troubleshooting recommendations.
            troubleshooting = suggest_troubleshooting_steps(
                incident=incident,
                triage=triage,
                diagnostic_result=diagnostic_data,
            )

            troubleshooting_status = troubleshooting.get("status")
            requires_review = troubleshooting.get(
                "requires_human",
                True,
            )

            if (
                troubleshooting_status != "recommendations_ready"
                or requires_review
                or troubleshooting.get("resolution_applied", False)
            ):
                return _human_review_result(
                    incident.incident_id,
                    "Troubleshooting did not produce an approved "
                    "recommendations-only result.",
                    triage=triage.model_dump(),
                    diagnostic=diagnostic_data,
                    troubleshooting=troubleshooting,
                )

            # 7. Return evidence and recommendations without claiming a fix.
            return {
                "incident_id": incident.incident_id,
                "status": "workflow_completed",
                "requires_human": False,
                "resolution_applied": False,
                "triage": triage.model_dump(),
                "diagnostic": diagnostic_data,
                "troubleshooting": troubleshooting,
                "message": (
                    "Recommendations only. No changes were made "
                    "to IT systems."
                ),
            }

    except Exception as exc:
        return {
            "incident_id": incident.incident_id,
            "status": "workflow_failed",
            "requires_human": True,
            "resolution_applied": False,
            "message": (
                "The workflow could not complete safely. "
                "An authorized IT technician must review the incident."
            ),
            "error_type": type(exc).__name__,
        }
