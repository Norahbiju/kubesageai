from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.azure.models import Cluster
from app.shared.config import settings


class AzureDiscoveryService:
    async def discover_clusters(self, session: AsyncSession) -> list[Cluster]:
        if settings.demo_mode:
            return await self._ensure_demo_clusters(session)
        return await self._ensure_demo_clusters(session)

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
