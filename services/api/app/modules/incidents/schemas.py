from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field

Severity = Literal["low", "medium", "high", "critical"]


class AnalysisDTO(BaseModel):
    summary: str
    root_cause: str
    severity: Severity
    confidence_score: float = Field(ge=0, le=100)
    affected_services: list[str]
    remediation: list[str]
    timeline: list[str]
    recommended_action: str


class IncidentDTO(BaseModel):
    id: str
    title: str
    cluster_name: str
    severity: Severity
    status: str
    created_at: datetime
    confidence_score: float
