from typing import Literal

from pydantic import BaseModel, Field


IncidentCategory = Literal[
    "network",
    "account",
    "device",
    "vpn",
    "security",
    "other",
]

IncidentPriority = Literal[
    "low",
    "medium",
    "high",
    "critical",
]


class IncidentReport(BaseModel):
    incident_id: str = Field(min_length=1, max_length=50)
    description: str = Field(min_length=5, max_length=2000)
    category: IncidentCategory = "other"
    priority: IncidentPriority = "medium"
    affected_user: str = "unknown"


class TriageResult(BaseModel):
    incident_id: str
    category: IncidentCategory
    priority: IncidentPriority
    summary: str
    requires_human: bool
    recommended_action: str
    confidence: float = Field(ge=0, le=1)


class DiagnosticResult(BaseModel):
    incident_id: str
    category: IncidentCategory
    checks: list[str] = Field(default_factory=list)
    findings: list[str] = Field(default_factory=list)
    recommended_next_step: str
    automated_changes_performed: bool = False


class TroubleshootingResult(BaseModel):
    incident_id: str
    status: Literal[
        "recommendations_ready",
        "escalation_required",
        "safety_review_required",
    ]
    steps: list[str] = Field(min_length=1)
    requires_human: bool
    resolution_applied: bool = False
    diagnostic_information: dict = Field(default_factory=dict)
    safety_reason: str | None = None
    message: str = (
        "Recommendations only. No changes were made to IT systems."
    )


class ResolutionPlan(BaseModel):
    incident_id: str
    explanation: str
    steps: list[str] = Field(min_length=1)
    evidence: list[str] = Field(default_factory=list)
    requires_human_approval: bool = True


class EvaluationResult(BaseModel):
    approved: bool
    feedback: str
    missing_evidence: list[str] = Field(default_factory=list)
