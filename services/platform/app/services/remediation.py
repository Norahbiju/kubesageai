from datetime import datetime, timezone

from kubernetes import client
from kubernetes.client.rest import ApiException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import KubeSageError
from app.models.entities import Cluster, Incident, RemediationAction, User
from app.schemas.dto import ApproveRemediationRequest
from app.services.kubernetes_integration import kubernetes_service

ALLOWED_ACTIONS = {
    "restart_deployment",
    "rollback_deployment",
    "delete_failed_pod",
    "scale_deployment",
    "restart_ingress_controller",
}


class RemediationService:
    async def approve(
        self, session: AsyncSession, user: User, incident_id: str, action_id: str, request: ApproveRemediationRequest
    ) -> RemediationAction:
        action = await self._load_action(session, user, incident_id, action_id)
        if request.action_type not in ALLOWED_ACTIONS:
            raise KubeSageError("Remediation action is not allowed", 400, "remediation_not_allowed")
        action.action_type = request.action_type
        action.action_payload_json = request.action_payload
        action.approval_status = "approved"
        action.approved_at = datetime.now(timezone.utc)
        await session.commit()
        await session.refresh(action)
        return action

    async def execute(self, session: AsyncSession, user: User, incident_id: str, action_id: str) -> RemediationAction:
        action = await self._load_action(session, user, incident_id, action_id)
        if action.approval_status != "approved":
            raise KubeSageError("Remediation must be approved before execution", 409, "remediation_not_approved")
        incident = await session.get(Incident, incident_id)
        cluster = await session.get(Cluster, incident.cluster_id) if incident else None
        if incident is None or cluster is None or incident.user_id != user.id:
            raise KubeSageError("Incident or cluster not found", 404, "incident_not_found")
        api_client = await kubernetes_service.api_client(session, user, cluster)
        try:
            result = await self._execute_with_sdk(api_client, action.action_type, action.action_payload_json)
        except ApiException as exc:
            action.execution_status = "failed"
            action.execution_result = str(exc)
            await session.commit()
            raise KubeSageError("Kubernetes remediation failed", 502, "remediation_failed") from exc
        action.execution_status = "succeeded"
        action.execution_result = result
        action.executed_at = datetime.now(timezone.utc)
        await session.commit()
        await session.refresh(action)
        return action

    async def _load_action(self, session: AsyncSession, user: User, incident_id: str, action_id: str) -> RemediationAction:
        result = await session.execute(
            select(RemediationAction).where(
                RemediationAction.id == action_id,
                RemediationAction.incident_id == incident_id,
                RemediationAction.user_id == user.id,
            )
        )
        action = result.scalar_one_or_none()
        if action is None:
            raise KubeSageError("Remediation action not found", 404, "remediation_not_found")
        return action

    async def _execute_with_sdk(self, api_client, action_type: str, payload: dict) -> str:
        namespace = payload.get("namespace")
        if not namespace:
            raise KubeSageError("Remediation payload must include namespace", 400, "invalid_remediation_payload")
        apps = client.AppsV1Api(api_client)
        core = client.CoreV1Api(api_client)
        if action_type == "restart_deployment":
            name = payload.get("deployment")
            if not name:
                raise KubeSageError("restart_deployment requires deployment", 400, "invalid_remediation_payload")
            patch = {"spec": {"template": {"metadata": {"annotations": {"kubesage.ai/restarted-at": datetime.now(timezone.utc).isoformat()}}}}}
            apps.patch_namespaced_deployment(name=name, namespace=namespace, body=patch)
            return f"Restarted deployment {namespace}/{name}"
        if action_type == "delete_failed_pod":
            pod = payload.get("pod")
            if not pod:
                raise KubeSageError("delete_failed_pod requires pod", 400, "invalid_remediation_payload")
            core.delete_namespaced_pod(name=pod, namespace=namespace)
            return f"Deleted pod {namespace}/{pod}"
        if action_type == "scale_deployment":
            name = payload.get("deployment")
            replicas = payload.get("replicas")
            if not name or not isinstance(replicas, int) or replicas < 0 or replicas > 100:
                raise KubeSageError("scale_deployment requires deployment and replicas 0-100", 400, "invalid_remediation_payload")
            apps.patch_namespaced_deployment_scale(name=name, namespace=namespace, body={"spec": {"replicas": replicas}})
            return f"Scaled deployment {namespace}/{name} to {replicas}"
        if action_type == "restart_ingress_controller":
            name = payload.get("deployment", "ingress-nginx-controller")
            patch = {"spec": {"template": {"metadata": {"annotations": {"kubesage.ai/restarted-at": datetime.now(timezone.utc).isoformat()}}}}}
            apps.patch_namespaced_deployment(name=name, namespace=namespace, body=patch)
            return f"Restarted ingress controller deployment {namespace}/{name}"
        if action_type == "rollback_deployment":
            name = payload.get("deployment")
            containers = payload.get("containers")
            if not name or not isinstance(containers, list) or not containers:
                raise KubeSageError(
                    "rollback_deployment requires deployment and explicit container image payload",
                    400,
                    "invalid_remediation_payload",
                )
            current = apps.read_namespaced_deployment(name=name, namespace=namespace)
            known = {container.name for container in current.spec.template.spec.containers}
            patched = []
            for item in containers:
                container_name = item.get("name") if isinstance(item, dict) else None
                image = item.get("image") if isinstance(item, dict) else None
                if not container_name or container_name not in known or not isinstance(image, str) or any(ch.isspace() for ch in image):
                    raise KubeSageError("rollback_deployment container payload is not safe", 400, "invalid_remediation_payload")
                patched.append({"name": container_name, "image": image})
            apps.patch_namespaced_deployment(
                name=name,
                namespace=namespace,
                body={"spec": {"template": {"spec": {"containers": patched}}}},
            )
            return f"Rolled back deployment {namespace}/{name} using approved container image payload"
        raise KubeSageError("Unsupported remediation action", 400, "remediation_not_allowed")


remediation_service = RemediationService()
