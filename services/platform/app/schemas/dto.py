from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field


Severity = Literal["low", "medium", "high", "critical"]


class UserDTO(BaseModel):
    id: str
    email: str
    display_name: str
    tenant_id: str


class SubscriptionDTO(BaseModel):
    subscription_id: str
    display_name: str
    state: str
    tenant_id: str = ""


class ClusterDTO(BaseModel):
    id: str
    subscription_id: str
    resource_group: str
    cluster_name: str
    location: str
    kubernetes_version: str
    cluster_resource_id: str
    status: str
    fqdn: str = ""


class SignalDTO(BaseModel):
    signal_type: str
    source: str
    message: str
    raw_payload_json: dict = Field(default_factory=dict)
    timestamp: datetime


class IncidentDTO(BaseModel):
    id: str
    cluster_id: str
    namespace: str
    workload_name: str
    workload_type: str
    issue_type: str
    severity: str
    status: str
    detected_at: datetime


class TimelineItem(BaseModel):
    time: str
    event: str


class RemediationSuggestion(BaseModel):
    action_id: str | None = None
    title: str
    description: str
    risk: Literal["low", "medium", "high"]
    action_type: Literal[
        "restart_deployment",
        "rollback_deployment",
        "delete_failed_pod",
        "scale_deployment",
        "restart_ingress_controller",
    ]
    requires_approval: bool = True
    command_preview: str
    action_payload: dict = Field(default_factory=dict)


class AIAnalysisResult(BaseModel):
    summary: str
    root_cause: str
    severity: Severity
    confidence_score: float = Field(ge=0, le=100)
    affected_services: list[str]
    timeline: list[TimelineItem]
    remediation: list[RemediationSuggestion]
    explanation: str
    next_steps: list[str]


class ScanResult(BaseModel):
    cluster: ClusterDTO
    incidents: list[IncidentDTO]


class ApproveRemediationRequest(BaseModel):
    action_type: Literal[
        "restart_deployment",
        "rollback_deployment",
        "delete_failed_pod",
        "scale_deployment",
        "restart_ingress_controller",
    ]
    action_payload: dict


class AuditLogDTO(BaseModel):
    id: str
    user_id: str | None
    action: str
    resource_type: str
    resource_id: str
    details_json: dict
    ip_address: str
    created_at: datetime
