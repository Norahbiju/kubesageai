from datetime import datetime, timezone

import yaml
from azure.mgmt.containerservice import ContainerServiceClient
from kubernetes import client, config
from kubernetes.client import ApiClient
from kubernetes.client.rest import ApiException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import KubeSageError
from app.models.entities import Cluster, Incident, IncidentSignal, User
from app.schemas.dto import IncidentDTO, SignalDTO
from app.services.azure_integration import azure_service

ISSUE_REASONS = {
    "CrashLoopBackOff",
    "ImagePullBackOff",
    "ErrImagePull",
    "OOMKilled",
    "CreateContainerConfigError",
    "CreateContainerError",
    "RunContainerError",
    "FailedScheduling",
    "Unhealthy",
    "BackOff",
}


class KubernetesIntegrationService:
    async def api_client(self, session: AsyncSession, user: User, cluster: Cluster) -> ApiClient:
        credential = await azure_service.credential_for_user(session, user)
        aks = ContainerServiceClient(credential, cluster.subscription_id)
        try:
            credentials = aks.managed_clusters.list_cluster_user_credentials(cluster.resource_group, cluster.cluster_name)
        except Exception as exc:
            raise KubeSageError("AKS credential access denied for this cluster", 403, "aks_credentials_denied") from exc
        if not credentials.kubeconfigs:
            raise KubeSageError("AKS did not return Kubernetes credentials", 403, "aks_credentials_missing")
        raw = credentials.kubeconfigs[0].value
        text = raw.decode("utf-8") if isinstance(raw, bytes) else raw
        return config.new_client_from_config_dict(yaml.safe_load(text))

    async def scan_cluster(self, session: AsyncSession, user: User, cluster_id: str) -> list[Incident]:
        result = await session.execute(select(Cluster).where(Cluster.id == cluster_id, Cluster.user_id == user.id))
        cluster = result.scalar_one_or_none()
        if cluster is None:
            raise KubeSageError("Cluster not found", 404, "cluster_not_found")
        api_client = await self.api_client(session, user, cluster)
        core = client.CoreV1Api(api_client)
        apps = client.AppsV1Api(api_client)
        networking = client.NetworkingV1Api(api_client)
        incidents: list[Incident] = []

        try:
            pods = core.list_pod_for_all_namespaces(watch=False, timeout_seconds=30).items
            events = core.list_event_for_all_namespaces(watch=False, timeout_seconds=30).items
            deployments = apps.list_deployment_for_all_namespaces(timeout_seconds=30).items
            services = core.list_service_for_all_namespaces(timeout_seconds=30).items
            ingresses = networking.list_ingress_for_all_namespaces(timeout_seconds=30).items
            secrets = core.list_secret_for_all_namespaces(timeout_seconds=30).items
        except ApiException as exc:
            raise KubeSageError("Kubernetes API scan failed or was denied", 403, "kubernetes_scan_failed") from exc

        event_lookup: dict[tuple[str | None, str | None], list] = {}
        for event in events:
            event_lookup.setdefault((event.involved_object.namespace, event.involved_object.name), []).append(event)
        for pod in pods:
            detected = self._detect_pod_issue(core, pod, event_lookup)
            if detected:
                incident = await self._create_incident(session, user, cluster, detected)
                incidents.append(incident)

        for deployment in deployments:
            desired = deployment.spec.replicas or 0
            available = deployment.status.available_replicas or 0
            if desired > available:
                incident = await self._create_incident(
                    session,
                    user,
                    cluster,
                    SignalDTO(
                        signal_type="deployment_unavailable",
                        source=deployment.metadata.name or "",
                        message=f"Deployment has {available}/{desired} available replicas",
                        raw_payload_json={"desired": desired, "available": available},
                        timestamp=datetime.now(timezone.utc),
                    ),
                    namespace=deployment.metadata.namespace or "default",
                    workload_name=deployment.metadata.name or "deployment",
                    workload_type="Deployment",
                    issue_type="deployment_unavailable",
                    severity="high",
                )
                incidents.append(incident)

        service_selectors = {(svc.metadata.namespace, svc.metadata.name): svc.spec.selector for svc in services}
        secret_names = {(secret.metadata.namespace, secret.metadata.name) for secret in secrets}
        pods_by_namespace = {}
        for pod in pods:
            pods_by_namespace.setdefault(pod.metadata.namespace, []).append(pod)
        for service in services:
            selector = service.spec.selector or {}
            if not selector or service.spec.type == "ExternalName":
                continue
            namespace = service.metadata.namespace or "default"
            matched = [
                pod for pod in pods_by_namespace.get(namespace, []) if all((pod.metadata.labels or {}).get(k) == v for k, v in selector.items())
            ]
            if not matched:
                incidents.append(
                    await self._create_incident(
                        session,
                        user,
                        cluster,
                        SignalDTO(
                            signal_type="service_selector_mismatch",
                            source=service.metadata.name or "",
                            message="Service selector does not match any pods",
                            raw_payload_json={"service": service.metadata.name, "selector": selector},
                            timestamp=datetime.now(timezone.utc),
                        ),
                        namespace=namespace,
                        workload_name=service.metadata.name or "service",
                        workload_type="Service",
                        issue_type="service_selector_mismatch",
                        severity="medium",
                    )
                )
        for ingress in ingresses:
            namespace = ingress.metadata.namespace or "default"
            for tls in ingress.spec.tls or []:
                if tls.secret_name and (namespace, tls.secret_name) not in secret_names:
                    incidents.append(
                        await self._create_incident(
                            session,
                            user,
                            cluster,
                            SignalDTO(
                                signal_type="ingress_tls_secret_missing",
                                source=ingress.metadata.name or "",
                                message=f"Ingress references missing TLS secret {tls.secret_name}",
                                raw_payload_json={"secret": tls.secret_name},
                                timestamp=datetime.now(timezone.utc),
                            ),
                            namespace=namespace,
                            workload_name=ingress.metadata.name or "ingress",
                            workload_type="Ingress",
                            issue_type="ingress_tls_secret_missing",
                            severity="high",
                        )
                    )
            for rule in ingress.spec.rules or []:
                for path in (rule.http.paths if rule.http else []):
                    service_name = path.backend.service.name if path.backend and path.backend.service else ""
                    if service_name and (namespace, service_name) not in service_selectors:
                        incidents.append(
                            await self._create_incident(
                                session,
                                user,
                                cluster,
                                SignalDTO(
                                    signal_type="ingress_backend_missing",
                                    source=ingress.metadata.name or "",
                                    message=f"Ingress references missing service {service_name}",
                                    raw_payload_json={"service": service_name},
                                    timestamp=datetime.now(timezone.utc),
                                ),
                                namespace=namespace,
                                workload_name=ingress.metadata.name or "ingress",
                                workload_type="Ingress",
                                issue_type="ingress_backend_missing",
                                severity="high",
                            )
                        )
        return incidents

    def _detect_pod_issue(self, core: client.CoreV1Api, pod, event_lookup: dict) -> SignalDTO | None:
        namespace = pod.metadata.namespace or "default"
        pod_name = pod.metadata.name or "pod"
        restart_count = 0
        reason = ""
        message = ""
        container_name = ""
        for status in pod.status.container_statuses or []:
            restart_count += status.restart_count or 0
            waiting = status.state.waiting if status.state else None
            terminated = status.last_state.terminated if status.last_state else None
            if waiting and waiting.reason in ISSUE_REASONS:
                container_name = status.name
                reason = waiting.reason
                message = waiting.message or waiting.reason
            if terminated and terminated.reason in ISSUE_REASONS:
                container_name = status.name
                reason = terminated.reason
                message = terminated.message or terminated.reason
        for event in event_lookup.get((namespace, pod_name), []):
            if event.reason in ISSUE_REASONS or event.reason in {"FailedScheduling"}:
                reason = reason or event.reason
                message = message or event.message or event.reason
        if pod.metadata.deletion_timestamp:
            reason = reason or "StuckTerminating"
            message = message or "Pod has a deletion timestamp and is still present"
        logs = ""
        try:
            logs = core.read_namespaced_pod_log(name=pod_name, namespace=namespace, tail_lines=80, _request_timeout=10)
        except Exception as exc:
            logs = f"log retrieval unavailable: {exc}"
        lowered = logs.lower()
        if not reason and ("no such host" in lowered or "temporary failure in name resolution" in lowered):
            reason = "DNSResolutionError"
            message = "Pod logs include DNS resolution failures"
        if not reason and ("readiness probe failed" in lowered or "liveness probe failed" in lowered):
            reason = "ProbeFailed"
            message = "Pod logs include failed readiness or liveness probes"
        if not reason and restart_count < 5 and pod.status.phase not in {"Failed", "Pending"}:
            return None
        return SignalDTO(
            signal_type="pod_failure",
            source=pod_name,
            message=message or f"Pod phase={pod.status.phase} restart_count={restart_count}",
            raw_payload_json={
                "namespace": namespace,
                "pod": pod_name,
                "container": container_name,
                "reason": reason or pod.status.phase,
                "restart_count": restart_count,
                "logs_snippet": logs[-4000:],
            },
            timestamp=datetime.now(timezone.utc),
        )

    async def _create_incident(
        self,
        session: AsyncSession,
        user: User,
        cluster: Cluster,
        signal: SignalDTO,
        namespace: str | None = None,
        workload_name: str | None = None,
        workload_type: str = "Pod",
        issue_type: str | None = None,
        severity: str = "medium",
    ) -> Incident:
        raw = signal.raw_payload_json
        incident = Incident(
            user_id=user.id,
            cluster_id=cluster.id,
            namespace=namespace or raw.get("namespace") or "default",
            workload_name=workload_name or raw.get("pod") or signal.source,
            workload_type=workload_type,
            issue_type=issue_type or raw.get("reason") or signal.signal_type,
            severity=severity if raw.get("reason") not in {"CrashLoopBackOff", "OOMKilled"} else "high",
            status="detected",
        )
        session.add(incident)
        await session.flush()
        session.add(IncidentSignal(incident_id=incident.id, **signal.model_dump()))
        await session.commit()
        await session.refresh(incident)
        return incident

    def to_dto(self, incident: Incident) -> IncidentDTO:
        return IncidentDTO(
            id=incident.id,
            cluster_id=incident.cluster_id,
            namespace=incident.namespace,
            workload_name=incident.workload_name,
            workload_type=incident.workload_type,
            issue_type=incident.issue_type,
            severity=incident.severity,
            status=incident.status,
            detected_at=incident.detected_at,
        )


kubernetes_service = KubernetesIntegrationService()
