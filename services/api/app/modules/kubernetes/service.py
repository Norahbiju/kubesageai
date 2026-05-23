import asyncio
import logging
from datetime import datetime, timezone

import yaml
from azure.mgmt.containerservice import ContainerServiceClient
from kubernetes import client, config

from app.modules.azure.models import Cluster
from app.modules.azure.service import AzureDiscoveryService
from app.modules.kubernetes.schemas import KubernetesFailure
from app.shared.config import settings

logger = logging.getLogger("kubesage.kubernetes")


class KubernetesInvestigationService:
    async def collect_failures(self, cluster: Cluster) -> list[KubernetesFailure]:
        if not settings.demo_mode and settings.azure_client_id and settings.azure_client_secret:
            return await asyncio.to_thread(self._collect_real_failures, cluster)
        return self._demo_failures()

    def _collect_real_failures(self, cluster: Cluster) -> list[KubernetesFailure]:
        logger.info("collecting_kubernetes_failures cluster=%s subscription=%s", cluster.name, cluster.subscription_id)
        credential = AzureDiscoveryService().credential()
        aks_client = ContainerServiceClient(credential, cluster.subscription_id)
        credentials = aks_client.managed_clusters.list_cluster_user_credentials(cluster.resource_group, cluster.name)
        if not credentials.kubeconfigs:
            return []

        kubeconfig_raw = credentials.kubeconfigs[0].value
        kubeconfig_text = kubeconfig_raw.decode("utf-8") if isinstance(kubeconfig_raw, bytes) else kubeconfig_raw
        kubeconfig_dict = yaml.safe_load(kubeconfig_text)
        api_client = config.new_client_from_config_dict(kubeconfig_dict)

        core = client.CoreV1Api(api_client)
        apps = client.AppsV1Api(api_client)
        networking = client.NetworkingV1Api(api_client)
        failures: list[KubernetesFailure] = []
        now = datetime.now(timezone.utc)

        pods = core.list_pod_for_all_namespaces(watch=False, timeout_seconds=20)
        events = core.list_event_for_all_namespaces(watch=False, timeout_seconds=20)
        event_lookup = {(event.involved_object.namespace, event.involved_object.name): event for event in events.items}

        for pod in pods.items:
            namespace = pod.metadata.namespace or "default"
            pod_name = pod.metadata.name or "unknown-pod"
            owner = pod.metadata.owner_references[0].name if pod.metadata.owner_references else None
            service = None
            reason = None
            message = ""
            restart_count = 0

            for status in pod.status.container_statuses or []:
                restart_count += status.restart_count or 0
                waiting = status.state.waiting if status.state else None
                terminated = status.last_state.terminated if status.last_state else None
                if waiting and waiting.reason in {"CrashLoopBackOff", "ImagePullBackOff", "ErrImagePull", "CreateContainerConfigError", "CreateContainerError"}:
                    reason = waiting.reason
                    message = waiting.message or reason
                elif terminated and terminated.reason in {"OOMKilled", "Error"}:
                    reason = terminated.reason
                    message = terminated.message or terminated.reason

            event = event_lookup.get((namespace, pod_name))
            if event and event.reason in {"Failed", "BackOff", "FailedScheduling", "Unhealthy"}:
                reason = reason or event.reason
                message = message or event.message or event.reason

            if reason or restart_count > 3 or pod.status.phase == "Failed":
                logs: list[str] = []
                try:
                    logs_text = core.read_namespaced_pod_log(
                        name=pod_name,
                        namespace=namespace,
                        tail_lines=80,
                        timestamps=True,
                        _request_timeout=10,
                    )
                    logs = logs_text.splitlines()[-80:]
                except Exception as exc:
                    logs = [f"log retrieval failed: {exc}"]

                failures.append(
                    KubernetesFailure(
                        pod_name=pod_name,
                        namespace=namespace,
                        deployment=owner,
                        service=service,
                        reason=reason or pod.status.phase or "PodFailure",
                        message=message or "Pod is not healthy",
                        timestamp=pod.status.start_time or now,
                        restart_count=restart_count,
                        logs=logs,
                    )
                )

        for deployment in apps.list_deployment_for_all_namespaces(timeout_seconds=20).items:
            desired = deployment.spec.replicas or 0
            available = deployment.status.available_replicas or 0
            if desired > available:
                failures.append(
                    KubernetesFailure(
                        pod_name=deployment.metadata.name or "deployment",
                        namespace=deployment.metadata.namespace or "default",
                        deployment=deployment.metadata.name,
                        service=deployment.metadata.name,
                        reason="FailedDeployment",
                        message=f"Deployment has {available}/{desired} replicas available",
                        timestamp=now,
                    )
                )

        for ingress in networking.list_ingress_for_all_namespaces(timeout_seconds=20).items:
            if not ingress.status.load_balancer.ingress:
                failures.append(
                    KubernetesFailure(
                        pod_name=ingress.metadata.name or "ingress",
                        namespace=ingress.metadata.namespace or "default",
                        service=ingress.metadata.name,
                        reason="IngressFailure",
                        message="Ingress has no load balancer address assigned",
                        timestamp=now,
                    )
                )

        return failures

    def _demo_failures(self) -> list[KubernetesFailure]:
        now = datetime.now(timezone.utc)
        return [
            KubernetesFailure(
                pod_name="checkout-api-7b8f8f4c8d-9k2mz",
                namespace="payments",
                deployment="checkout-api",
                service="checkout",
                reason="CrashLoopBackOff",
                message="Back-off restarting failed container after config validation error",
                timestamp=now,
                restart_count=18,
                logs=["ConfigError: missing AZURE_CLIENT_SECRET", "Application startup aborted"],
            ),
            KubernetesFailure(
                pod_name="catalog-worker-5d4758f7c-2hvmd",
                namespace="catalog",
                deployment="catalog-worker",
                service="catalog",
                reason="ImagePullBackOff",
                message="Failed to pull image registry.azurecr.io/catalog-worker:2026.05.23",
                timestamp=now,
                restart_count=0,
                logs=["manifest unknown", "image pull failed"],
            ),
            KubernetesFailure(
                pod_name="ingress-nginx-controller-6fd9c",
                namespace="ingress-nginx",
                deployment="ingress-nginx-controller",
                service="ingress",
                reason="IngressFailure",
                message="Readiness probe failed and upstream endpoints unavailable",
                timestamp=now,
                restart_count=3,
                logs=["upstream checkout has no active endpoints", "DNS lookup timeout for kube-dns"],
            ),
        ]
