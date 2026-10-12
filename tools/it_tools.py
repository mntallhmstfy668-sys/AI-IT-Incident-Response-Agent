from agents import function_tool


# DEMO ONLY: these tools return simulated data.
# They do not access real company systems or change configurations.


@function_tool
def check_account_status(username: str) -> str:
    """Check a simulated IT account status for a username."""
    return (
        f"DEMO DATA: Account '{username}' is enabled. "
        "No real account system was queried."
    )


@function_tool
def check_vpn_status(username: str) -> str:
    """Check simulated VPN connectivity for a user."""
    return (
        f"DEMO DATA: VPN status for '{username}' is unknown. "
        "Ask the user for the error message and connection time. "
        "No real VPN system was queried."
    )


@function_tool
def check_device_status(device_name: str) -> str:
    """Check simulated device health information."""
    return (
        f"DEMO DATA: Device '{device_name}' has not been queried in a real system. "
        "Verify power, connectivity, recent updates, and error messages."
    )


@function_tool
def check_network_status(location: str) -> str:
    """Check simulated network status for a location."""
    return (
        f"DEMO DATA: No live network telemetry is available for '{location}'. "
        "Check whether multiple users are affected and verify approved monitoring tools."
    )


@function_tool
def search_it_knowledge(query: str) -> str:
    """Search a small built-in demo IT knowledge base."""
    q = query.lower()

    if any(word in q for word in ("wifi", "wi-fi", "network", "internet")):
        return (
            "Knowledge article: Network troubleshooting. "
            "Check scope of impact, connection status, known outages, "
            "and error timestamps. Escalate suspected widespread outages."
        )

    if any(word in q for word in ("vpn", "remote access")):
        return (
            "Knowledge article: VPN troubleshooting. "
            "Confirm internet access, capture the exact error, "
            "check approved VPN service status, and escalate repeated failures."
        )

    if any(word in q for word in ("password", "account", "login", "sign in")):
        return (
            "Knowledge article: Account access. "
            "Confirm the username and error message through approved procedures. "
            "Never ask the user to share their password or authentication codes."
        )

    if any(word in q for word in ("security", "phishing", "unauthorized", "suspicious")):
        return (
            "Knowledge article: Security incident. "
            "Escalate promptly to the authorized security team. "
            "Do not automatically close the incident or perform unapproved changes."
        )

    return (
        "No exact demo article found. Collect symptoms, timestamps, scope, "
        "and error messages, then consult the organization's approved IT knowledge base."
    )


@function_tool
def create_incident_ticket(
    incident_id: str, summary: str, priority: str
) -> str:
    """Prepare a simulated ticket record without creating a real ticket."""
    return (
        f"DEMO TICKET PREPARED: {incident_id}; priority={priority}; "
        f"summary={summary[:300]}. No external ticket was created."
    )
