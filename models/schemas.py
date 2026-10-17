from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class StrictOutputModel(BaseModel):
    # Closed objects make generated JSON schemas easier for providers to validate.
    model_config = ConfigDict(extra="forbid")


class TriageResult(StrictOutputModel):
    category: Literal["account", "network", "device", "security", "unknown"]
    severity: Literal["low", "medium", "high", "critical"]
    summary: str
    affected_system: str
    needs_human_review: bool


class InvestigationPlan(StrictOutputModel):
    specialists: list[Literal["account", "network", "device"]]
    reason: str


class GuardrailDecision(StrictOutputModel):
    allowed: bool
    reason: str


class IncidentReport(StrictOutputModel):
    severity: Literal["low", "medium", "high", "critical"]
    route: Literal["normal investigation", "human review"]
    human_review: bool
    summary: str
    findings: list[str]
    recommendations: list[str]
    safety_note: str
    audit_log: list[str]
﻿ 
