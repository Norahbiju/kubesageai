import asyncio
import logging

from azure.identity import ClientSecretCredential
from azure.mgmt.containerservice import ContainerServiceClient
from azure.mgmt.resource import SubscriptionClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.azure.models import Cluster
from app.shared.config import settings
from app.shared.errors import KubeSageError

logger = logging.getLogger("kubesage.azure")


class AzureDiscoveryService:
    async def discover_clusters(self, session: AsyncSession) -> list[Cluster]:
        if settings.demo_mode:
            return await self._ensure_demo_clusters(session)
        if not settings.azure_client_id or not settings.azure_client_secret or not settings.azure_tenant_id:
            raise KubeSageError("Azure credentials are not configured. Set AZURE_CLIENT_ID, AZURE_CLIENT_SECRET, and AZURE_TENANT_ID.", 500)
        return await self._discover_real_clusters(session)

    def credential(self) -> ClientSecretCredential:
        return ClientSecretCredential(
            tenant_id=settings.azure_tenant_id,
            client_id=settings.azure_client_id,
            client_secret=settings.azure_client_secret,
        )

    def subscription_ids(self) -> list[str]:
        credential = self.credential()
        if settings.azure_subscription_ids:
            return settings.azure_subscription_ids
        client = SubscriptionClient(credential)
        return [subscription.subscription_id for subscription in client.subscriptions.list()]

    async def _upsert_real_clusters(self, session: AsyncSession, discovered: list[dict]) -> list[Cluster]:
        clusters: list[Cluster] = []
        for item in discovered:
            result = await session.execute(
                select(Cluster).where(
                    Cluster.subscription_id == item["subscription_id"],
                    Cluster.resource_group == item["resource_group"],
                    Cluster.name == item["name"],
                )
            )
            cluster = result.scalar_one_or_none()
            if cluster is None:
                cluster = Cluster(**item)
                session.add(cluster)
                await session.flush()
            else:
                cluster.location = item["location"]
                cluster.kubernetes_version = item["kubernetes_version"]
                cluster.status = item["status"]
            clusters.append(cluster)
        await session.commit()
        return clusters

    async def _discover_real_clusters(self, session: AsyncSession) -> list[Cluster]:
        def discover() -> list[dict]:
            credential = self.credential()
            subscription_ids = self.subscription_ids()
            discovered: list[dict] = []
            for subscription_id in subscription_ids:
                logger.info("discovering_aks subscription_id=%s", subscription_id)
                client = ContainerServiceClient(credential, subscription_id)
                for managed_cluster in client.managed_clusters.list():
                    resource_group = managed_cluster.id.split("/resourceGroups/")[1].split("/")[0]
                    power_state = getattr(getattr(managed_cluster, "power_state", None), "code", None)
                    discovered.append(
                        {
                            "name": managed_cluster.name,
                            "resource_group": resource_group,
                            "subscription_id": subscription_id,
                            "location": managed_cluster.location or "unknown",
                            "kubernetes_version": managed_cluster.kubernetes_version or "unknown",
                            "status": power_state or managed_cluster.provisioning_state or "Unknown",
                            "failing_workloads": 0,
                        }
                    )
            return discovered

        discovered = await asyncio.to_thread(discover)
        return await self._upsert_real_clusters(session, discovered)

    async def _ensure_demo_clusters(self, session: AsyncSession) -> list[Cluster]:
        result = await session.execute(select(Cluster))
        clusters = list(result.scalars().all())
        if clusters:
            return clusters
        seed = [
            Cluster(name="aks-prod-eastus-01", resource_group="rg-platform-prod", subscription_id="sub-prod-001", location="eastus", kubernetes_version="1.30.5", failing_workloads=4),
            Cluster(name="aks-payments-westus-02", resource_group="rg-payments", subscription_id="sub-prod-001", location="westus2", kubernetes_version="1.29.8", failing_workloads=2),
            Cluster(name="aks-dev-tools", resource_group="rg-internal-dev", subscription_id="sub-dev-042", location="centralus", kubernetes_version="1.30.3", failing_workloads=1),
        ]
        session.add_all(seed)
        await session.commit()
        return seed
