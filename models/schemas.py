
from typing import Optional, Literal

from pydantic import BaseModel, Field


class IncidentReport(BaseModel):
    """Structured information about an IT incident."""

    incident_id: str = Field(
        description="Unique identifier for the incident"
    )
    description: str = Field(
        min_length=1,
        description="Description of the reported IT problem"
    )
    category: Literal[
        "network",
        "vpn",
        "account",
        "device",
        "software",
        "security",
        "other",
    ] = Field(
        description="Category that best describes the incident"
    )
    priority: Literal["low", "medium", "high", "critical"] = Field(
        description="Severity and urgency of the incident"
    )
    affected_service: Optional[str] = Field(
        default=None,
        description="IT service affected by the incident, if known"
    )


class TriageResult(BaseModel):
    """Structured result produced during incident triage."""

    category: Literal[
        "network",
        "vpn",
        "account",
        "device",
        "software",
        "security",
        "other",
    ] = Field(
        description="Classified category of the incident"
    )
    priority: Literal["low", "medium", "high", "critical"] = Field(
        description="Assigned incident priority"
    )
    summary: str = Field(
        min_length=1,
        description="Clear summary of the reported problem"
    )
    requires_human: bool = Field(
        description="Whether the incident requires human intervention"
    )
    recommended_action: str = Field(
        min_length=1,
        description="Recommended next troubleshooting or escalation step"
    )
    confidence: float = Field(
        ge=0.0,
        le=1.0,
        description="Confidence in the triage result, from 0 to 1"
    )
