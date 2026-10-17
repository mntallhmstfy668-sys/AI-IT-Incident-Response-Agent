from agents import function_tool

# Demo-only data. Replace these deterministic mock checks with approved internal IT APIs.
# The tools do not access real accounts, devices, networks, or ticketing systems.

@function_tool
def check_account_status(employee_id: str = "DEMO-001") -> str:
    """Check a demo employee account status. Never request or return passwords or tokens."""
    return "Demo account status: active; failed_sign_ins_last_hour=2; password_reset_required=false."

@function_tool
def check_vpn_status(location: str = "office") -> str:
    """Check the demo VPN service status for a location."""
    return "Demo VPN status: operational; authentication_service=operational; known_outage=false."

@function_tool
def check_device_status(device_name: str = "employee-laptop") -> str:
    """Check a demo device's health summary."""
    return "Demo device status: online; disk_space=adequate; endpoint_protection=enabled; reboot_pending=false."

@function_tool
def check_network_status(location: str = "office") -> str:
    """Check the demo network status for a location."""
    return "Demo network status: operational; packet_loss=0.2%; known_outage=false."

@function_tool
def search_it_knowledge(query: str) -> str:
    """Search a small built-in IT knowledge base for safe troubleshooting guidance."""
    q = query.lower()
    if "vpn" in q:
        return "VPN guidance: confirm internet access, reconnect to the approved VPN client, check service status, then contact IT if the issue persists. Never ask for credentials."
    if "account" in q or "sign in" in q or "login" in q or "locked" in q:
        return "Account guidance: use the official password-reset flow and verify account status with IT. Never share passwords, one-time codes, or recovery tokens."
    if "network" in q or "internet" in q:
        return "Network guidance: check whether the issue affects one device or multiple users, verify Wi-Fi/Ethernet connection, and check the approved network status page."
    if "device" in q or "laptop" in q:
        return "Device guidance: save work, check power/connectivity, record any error message, and use approved endpoint support procedures."
    if "security" in q or "suspicious" in q or "unauthorized" in q or "phishing" in q:
        return "Security guidance: do not investigate by opening suspicious links. Preserve relevant details and escalate to the security/IT team immediately."
    return "Knowledge base: collect the exact error message, affected service, approximate start time, and whether other users are affected. Escalate if impact is broad or security-related."

@function_tool
def create_support_ticket(title: str, description: str, priority: str) -> str:
    """Create a simulated support ticket after safe validation. This demo tool does not create a real ticket."""
    allowed = {"low", "medium", "high", "critical"}
    if priority.lower() not in allowed:
        return "Ticket blocked: priority must be low, medium, high, or critical."
    if not title.strip() or not description.strip():
        return "Ticket blocked: title and description are required."
    return f"SIMULATED TICKET CREATED: IT-DEMO-1042 | priority={priority.lower()} | title={title[:100]}"

@function_tool
def request_human_review(reason: str, incident_summary: str) -> str:
    """Record a simulated human-review request. This does not contact a real person."""
    if not reason.strip() or not incident_summary.strip():
        return "Review request blocked: reason and incident summary are required."
    return f"HUMAN REVIEW REQUIRED (simulated): reason={reason[:200]}; incident={incident_summary[:300]}"
﻿ 
