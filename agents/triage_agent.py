
from models.schemas import IncidentReport, TriageResult
from guardrails.safety_filters import check_input_safety


def triage_incident(incident: IncidentReport) -> TriageResult:
    """
    Classify an IT incident and recommend the next step.
    This initial version uses deterministic Python rules.
    """
    description = incident.description.strip()
    normalized_description = description.lower()

    # Check whether the incident description is safe to process.
    is_safe, safety_reason = check_input_safety(description)

    if not is_safe:
        return TriageResult(
            category="security",
            priority="high",
            summary=f"Incident requires safety review: {safety_reason}",
            requires_human=True,
            recommended_action=(
                "Escalate the request for human review. "
                "Do not perform sensitive actions automatically."
            ),
            confidence=1.0,
        )

    # Identify the incident category using simple keyword rules.
    if any(word in normalized_description for word in [
        "vpn", "virtual private network", "remote access"
    ]):
        category = "vpn"

    elif any(word in normalized_description for word in [
        "wifi", "wi-fi", "network", "internet", "connection"
    ]):
        category = "network"

    elif any(word in normalized_description for word in [
        "password", "login", "locked account", "account access"
    ]):
        category = "account"

    elif any(word in normalized_description for word in [
        "laptop", "desktop", "keyboard", "mouse", "printer", "device"
    ]):
        category = "device"

    elif any(word in normalized_description for word in [
        "malware", "phishing", "ransomware", "unauthorized access",
        "security breach"
    ]):
        category = "security"

    elif any(word in normalized_description for word in [
        "application", "software", "program", "app crash"
    ]):
        category = "software"

    else:
        category = "other"

    # Determine priority from severity indicators.
    critical_keywords = [
        "ransomware",
        "security breach",
        "data breach",
        "entire company",
        "all users",
        "critical system down",
    ]

    high_keywords = [
        "urgent",
        "multiple users",
        "production down",
        "cannot work",
        "major outage",
    ]

    low_keywords = [
        "minor",
        "occasionally",
        "cosmetic",
        "small issue",
    ]

    if any(word in normalized_description for word in critical_keywords):
        priority = "critical"
    elif category == "security":
        priority = "high"
    elif any(word in normalized_description for word in high_keywords):
        priority = "high"
    elif any(word in normalized_description for word in low_keywords):
        priority = "low"
    else:
        priority = "medium"

    # Critical incidents and security issues require human intervention.
    requires_human = (
        priority == "critical"
        or category == "security"
    )

    # Recommend a safe next step without performing any IT action.
    recommended_actions = {
        "network": "Check network connectivity and network service status.",
        "vpn": "Check VPN service status and the user's connection settings.",
        "account": "Verify account status using approved IT support tools.",
        "device": "Check device health and relevant hardware status.",
        "software": "Collect the application error details and check known issues.",
        "security": "Escalate to the security team for human investigation.",
        "other": "Gather more details and search the IT knowledge base.",
    }

    if requires_human:
        recommended_action = (
            "Escalate to the appropriate IT team for human review. "
            "Do not automatically close this incident."
        )
    else:
        recommended_action = recommended_actions[category]

    return TriageResult(
        category=category,
        priority=priority,
        summary=description,
        requires_human=requires_human,
        recommended_action=recommended_action,
        confidence=0.8,
    )
