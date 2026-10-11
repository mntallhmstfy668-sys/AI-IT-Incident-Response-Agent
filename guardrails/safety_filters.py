
import re
from typing import Optional


# Requests that may expose passwords or other sensitive credentials.
CREDENTIAL_PATTERNS = [
    r"\bpassword\b",
    r"\bpassphrase\b",
    r"\bsecret key\b",
    r"\bprivate key\b",
    r"\baccess token\b",
    r"\bapi key\b",
]


# Phrases that may indicate an attempt to override agent instructions.
PROMPT_INJECTION_PATTERNS = [
    r"\bignore (all )?(previous|prior) instructions\b",
    r"\bdisregard (all )?(previous|prior) instructions\b",
    r"\breveal (your )?(system prompt|hidden instructions)\b",
    r"\bignore your safety rules\b",
]


# Actions that should never be performed automatically.
UNSAFE_ACTION_PATTERNS = [
    r"\bdelete all (user )?accounts\b",
    r"\bdisable (all )?security controls\b",
    r"\bdisable (all )?firewalls\b",
    r"\bdelete (all )?backups\b",
    r"\bexfiltrate\b",
]


def _contains_pattern(text: str, patterns: list[str]) -> bool:
    """Return True if the text matches any configured safety pattern."""
    return any(
        re.search(pattern, text, flags=re.IGNORECASE)
        for pattern in patterns
    )


def check_input_safety(text: str) -> tuple[bool, Optional[str]]:
    """
    Check an incoming user request for common safety risks.

    Returns:
        A tuple containing (is_safe, reason).
    """
    if not text or not text.strip():
        return False, "The request is empty."

    if _contains_pattern(text, PROMPT_INJECTION_PATTERNS):
        return False, "The request may contain a prompt injection attempt."

    if _contains_pattern(text, UNSAFE_ACTION_PATTERNS):
        return False, "The request contains a potentially unsafe IT action."

    if _contains_pattern(text, CREDENTIAL_PATTERNS):
        return (
            False,
            "The request mentions credentials or secrets. "
            "Do not request or expose sensitive authentication data.",
        )

    return True, None


def check_output_safety(text: str) -> tuple[bool, Optional[str]]:
    """
    Check an agent response before returning it to the user.

    This is a basic pattern-based check, not a complete security guarantee.
    """
    if not text or not text.strip():
        return False, "The response is empty."

    if _contains_pattern(text, UNSAFE_ACTION_PATTERNS):
        return False, "The response may recommend an unsafe IT action."

    if _contains_pattern(text, CREDENTIAL_PATTERNS):
        return False, "The response may expose or request sensitive credentials."

    return True, None


def requires_human_approval(
    action: str,
    priority: str = "medium",
) -> bool:
    """
    Require human review for critical incidents and sensitive actions.
    """
    normalized_action = action.lower()
    normalized_priority = priority.lower()

    sensitive_actions = [
        "delete",
        "disable security",
        "reset password",
        "change permissions",
        "close security incident",
        "modify firewall",
        "disable account",
    ]

    if normalized_priority == "critical":
        return True

    return any(
        phrase in normalized_action
        for phrase in sensitive_actions
    )
