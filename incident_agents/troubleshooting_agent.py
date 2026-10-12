
import json

from agents import Agent, Runner

from guardrails.safety_filters import (
    check_output_safety,
    requires_human_approval,
)
from models.schemas import (
    IncidentReport,
    TriageResult,
    TroubleshootingResult,
)


troubleshooting_agent = Agent(
    name="IT Troubleshooting Agent",
    instructions="""
    You are an IT troubleshooting specialist.

    Analyze the incident, triage result, and diagnostic information.

    Responsibilities:
    - Recommend safe, relevant, evidence-based troubleshooting steps.
    - Explain steps clearly and in a practical order.
    - Request additional diagnostic information when evidence is insufficient.
    - Escalate critical incidents and suspected security incidents.
    - Return output matching the TroubleshootingResult schema.

    Safety rules:
    - Never invent diagnostic findings or claim unsupported facts.
    - Never claim that an incident has been fixed.
    - Never request passwords, API keys, or authentication codes.
    - Never recommend disabling security controls or destructive actions.
    - Never make changes to IT systems.
    - Recommendations must not be presented as executed actions.
    - Human review is required whenever the incident cannot be handled safely.
    """,
    output_type=TroubleshootingResult,
)


def suggest_troubleshooting_steps(
    incident: IncidentReport,
    triage: TriageResult,
    diagnostic_result: dict,
) -> dict:
    """Generate safe troubleshooting recommendations without applying fixes."""

    requires_review = (
        requires_human_approval(
            incident,
            triage,
            diagnostic_result,
        )
        or triage.priority == "critical"
        or triage.category == "security"
        or triage.requires_human
    )

    if requires_review:
        return TroubleshootingResult(
            incident_id=incident.incident_id,
            status="escalation_required",
            steps=[
                "Escalate the incident to the authorized IT or security team.",
                "Preserve relevant logs and error messages.",
                "Avoid sensitive changes until an authorized technician reviews the incident.",
            ],
            requires_human=True,
            resolution_applied=False,
            diagnostic_information=diagnostic_result,
            message=(
                "Human review is required. No changes were made to IT systems."
            ),
        ).model_dump()

    payload = {
        "incident": incident.model_dump(),
        "triage": triage.model_dump(),
        "diagnostic_result": diagnostic_result,
    }

    try:
        result = Runner.run_sync(
            troubleshooting_agent,
            json.dumps(payload, ensure_ascii=False),
        )

        recommendation: TroubleshootingResult = result.final_output

        is_safe, reason = check_output_safety(
            " ".join(recommendation.steps)
        )

        if not is_safe:
            return TroubleshootingResult(
                incident_id=incident.incident_id,
                status="safety_review_required",
                steps=[
                    "Pause automated troubleshooting recommendations.",
                    "Request review from an authorized IT technician.",
                ],
                requires_human=True,
                resolution_applied=False,
                diagnostic_information=diagnostic_result,
                safety_reason=reason,
                message=(
                    "The recommendation did not pass safety checks. "
                    "No changes were made to IT systems."
                ),
            ).model_dump()

        recommendation.incident_id = incident.incident_id
        recommendation.resolution_applied = False
        recommendation.diagnostic_information = diagnostic_result
        recommendation.message = (
            "Recommendations only. No changes were made to IT systems."
        )

        return recommendation.model_dump()

    except Exception as exc:
        return TroubleshootingResult(
            incident_id=incident.incident_id,
            status="safety_review_required",
            steps=[
                "Pause automated troubleshooting.",
                "Ask an authorized IT technician to review the incident.",
            ],
            requires_human=True,
            resolution_applied=False,
            diagnostic_information=diagnostic_result,
            safety_reason=f"Agent execution failed: {type(exc).__name__}",
            message=(
                "Troubleshooting could not be completed safely. "
                "No changes were made to IT systems."
            ),
        ).model_dump()
