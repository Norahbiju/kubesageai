from typing import Literal

from pydantic import BaseModel, Field

SafeAction = Literal[
    "rollout_restart_deployment",
    "rollout_undo_deployment",
    "delete_failed_pod",
    "scale_deployment",
    "restart_ingress_controller",
]


class RemediationApprovalRequest(BaseModel):
    incident_id: str
    action_type: SafeAction
    parameters: dict = Field(default_factory=dict)


class RemediationResult(BaseModel):
    action_id: str
    status: str
    result: str
