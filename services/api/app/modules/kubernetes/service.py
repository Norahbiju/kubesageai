from datetime import datetime, timezone

from app.modules.kubernetes.schemas import KubernetesFailure


class KubernetesInvestigationService:
    async def collect_failures(self, cluster_id: str) -> list[KubernetesFailure]:
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
