
import re

from models.schemas import IncidentReport


BLOCKED_INPUT_PATTERNS = [
    r"\bpassword\s*[:=]",
    r"\bpasscode\s*[:=]",
    r"\b(?:api[_ -]?key|secret[_ -]?key)\s*[:=]",
    r"\b(?:ignore|bypass|disable)\b.{0,50}\b(?:security|guardrails|safety)\b",
]

UNSAFE_ACTION_PATTERNS = [
    r"\bdisable\s+(?:firewall|antivirus|security)\b",
    r"\bdelete\s+(?:all\s+)?(?:logs|backups|audit records)\b",
    r"\bexfiltrat\w*\b",
    r"\bshutdown\s+(?:all\s+)?servers\b",
]


def validate_incident_input(
    incident: IncidentReport,
) -> tuple[bool, str]:
    """Reject incident descriptions containing sensitive data patterns."""
    for pattern in BLOCKED_INPUT_PATTERNS:
        if re.search(
            pattern,
            incident.description,
            re.IGNORECASE,
        ):
            return False, "Input rejected by security guardrails."

    return True, "Input passed security checks."


def is_high_risk_incident(
    incident: IncidentReport,
) -> bool:
    """Identify incidents that always require human review."""
    return (
        incident.priority == "critical"
        or incident.category == "security"
    )


def requires_human_approval(
    incident: IncidentReport,
    triage=None,
    diagnostic_result=None,
) -> bool:
    """Require human approval for high-risk incidents or agent findings."""
    if is_high_risk_incident(incident):
        return True

    if triage is not None:
        if getattr(triage, "requires_human", False):
            return True

        if getattr(triage, "priority", "") == "critical":
            return True

        if getattr(triage, "category", "") == "security":
            return True

    if diagnostic_result is not None:
        if getattr(diagnostic_result, "requires_human", False):
            return True

        if isinstance(diagnostic_result, dict):
            if diagnostic_result.get("requires_human", False):
                return True

            if diagnostic_result.get("requires_human_approval", False):
                return True

            if diagnostic_result.get("priority") == "critical":
                return True

            if diagnostic_result.get("category") == "security":
                return True

    return False


def validate_recommended_action(
    action: str,
) -> tuple[bool, str]:
    """Block recommendations that contain explicitly unsafe actions."""
    for pattern in UNSAFE_ACTION_PATTERNS:
        if re.search(pattern, action, re.IGNORECASE):
            return (
                False,
                "Recommendation blocked. Obtain authorized human review.",
            )

    return True, "Recommendation passed safety checks."


def check_output_safety(
    output: str,
) -> tuple[bool, str]:
    """Check generated agent output before returning it."""
    return validate_recommended_action(output)


def validate_resolution_claim(
    resolution_applied: bool,
    evidence: list[str],
) -> tuple[bool, str]:
    """Prevent claiming a resolution without supporting evidence."""
    if resolution_applied and not evidence:
        return (
            False,
            "Resolution claim rejected because no supporting evidence was provided.",
        )

    if resolution_applied:
        return True, "Resolution claim has supporting evidence."

    return True, "Recommendation only; no resolution claimed."
