
from typing import Any

from models.schemas import IncidentReport


def diagnose_network(incident: IncidentReport) -> dict[str, Any]:
    """Prepare safe diagnostic checks for a network incident."""
    return {
        "incident_id": incident.incident_id,
        "category": "network",
        "problem": incident.description,
        "checks": [
            "Check whether the issue affects one user or multiple users.",
            "Verify network service status using approved IT tools.",
            "Check for known network outages or maintenance.",
            "Collect relevant error messages and timestamps.",
        ],
        "recommended_next_step": (
            "Review the collected network status and escalate "
            "if a wider outage is suspected."
        ),
        "automated_changes_performed": False,
    }


def diagnose_vpn(incident: IncidentReport) -> dict[str, Any]:
    """Prepare safe diagnostic checks for a VPN incident."""
    return {
        "incident_id": incident.incident_id,
        "category": "vpn",
        "problem": incident.description,
        "checks": [
            "Verify VPN service availability using approved IT tools.",
            "Check whether the user has a general network connection.",
            "Collect the VPN error message and approximate time.",
            "Check for known VPN service incidents.",
        ],
        "recommended_next_step": (
            "Review VPN status and escalate persistent connection "
            "failures to the IT support team."
        ),
        "automated_changes_performed": False,
    }


def diagnose_device(incident: IncidentReport) -> dict[str, Any]:
    """Prepare safe diagnostic checks for a device incident."""
    return {
        "incident_id": incident.incident_id,
        "category": "device",
        "problem": incident.description,
        "checks": [
            "Identify the affected device and its symptoms.",
            "Check device health using approved diagnostic tools.",
            "Collect relevant error messages.",
            "Determine whether other devices are affected.",
        ],
        "recommended_next_step": (
            "Review the device health information and escalate "
            "possible hardware failures to IT support."
        ),
        "automated_changes_performed": False,
    }


def diagnose_account(incident: IncidentReport) -> dict[str, Any]:
    """Prepare safe diagnostic checks for an account incident."""
    return {
        "incident_id": incident.incident_id,
        "category": "account",
        "problem": incident.description,
        "checks": [
            "Verify account status using an approved IT tool.",
            "Check whether the account is locked or disabled.",
            "Review relevant authentication error messages.",
            "Never request or store the user's password.",
        ],
        "recommended_next_step": (
            "Follow the approved account recovery process "
            "and request human assistance when required."
        ),
        "automated_changes_performed": False,
    }


def run_diagnostic_checks(
    incident: IncidentReport,
) -> dict[str, Any]:
    """Select a diagnostic worker based on the incident category."""
    diagnostic_workers = {
        "network": diagnose_network,
        "vpn": diagnose_vpn,
        "device": diagnose_device,
        "account": diagnose_account,
    }

    worker = diagnostic_workers.get(incident.category)

    if worker is None:
        return {
            "incident_id": incident.incident_id,
            "category": incident.category,
            "problem": incident.description,
            "checks": [
                "Gather more information about the incident.",
                "Search the approved IT knowledge base.",
                "Escalate if the issue remains unclear.",
            ],
            "recommended_next_step": (
                "Collect additional details before choosing a resolution."
            ),
            "automated_changes_performed": False,
        }

    return worker(incident)
