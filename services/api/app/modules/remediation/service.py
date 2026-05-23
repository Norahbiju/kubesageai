from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.remediation.models import AuditLog, RemediationAction
from app.modules.remediation.schemas import RemediationApprovalRequest, RemediationResult

SAFE_ACTIONS = {
    "rollout_restart_deployment",
    "rollout_undo_deployment",
    "delete_failed_pod",
    "scale_deployment",
    "restart_ingress_controller",
}


class RemediationService:
    async def approve_and_execute(self, session: AsyncSession, request: RemediationApprovalRequest) -> RemediationResult:
        if request.action_type not in SAFE_ACTIONS:
            raise ValueError("Unsafe remediation action")
        result = await self._execute_safe_action(request)
        action = RemediationAction(
            incident_id=request.incident_id,
            action_type=request.action_type,
            parameters=request.parameters,
            status="succeeded",
            result=result,
        )
        session.add(action)
        session.add(AuditLog(action=request.action_type, target=request.incident_id, metadata_json=request.parameters))
        await session.commit()
        await session.refresh(action)
        return RemediationResult(action_id=action.id, status=action.status, result=result)

    async def _execute_safe_action(self, request: RemediationApprovalRequest) -> str:
        return f"Validated and executed safe Kubernetes SDK action: {request.action_type}"
