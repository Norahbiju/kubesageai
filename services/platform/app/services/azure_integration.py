from datetime import datetime, timezone

from azure.core.credentials import AccessToken, TokenCredential
from azure.mgmt.containerservice import ContainerServiceClient
from azure.mgmt.resource import SubscriptionClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.errors import KubeSageError
from app.core.security import decrypt_secret
from app.models.entities import AzureConnection, Cluster, User
from app.schemas.dto import ClusterDTO, SubscriptionDTO


class UserTokenCredential(TokenCredential):
    def __init__(self, access_token: str, expires_on: datetime) -> None:
        self.access_token = access_token
        self.expires_on = expires_on

    def get_token(self, *scopes: str, **kwargs) -> AccessToken:
        return AccessToken(self.access_token, int(self.expires_on.timestamp()))


class AzureIntegrationService:
    async def credential_for_user(self, session: AsyncSession, user: User) -> UserTokenCredential:
        result = await session.execute(
            select(AzureConnection)
            .where(AzureConnection.user_id == user.id)
            .order_by(AzureConnection.created_at.desc())
            .limit(1)
        )
        connection = result.scalar_one_or_none()
        if connection is None:
            raise KubeSageError("Azure account is not connected", 401, "azure_not_connected")
        if connection.expires_at <= datetime.now(timezone.utc):
            raise KubeSageError("Azure token expired; login again", 401, "azure_token_expired")
        return UserTokenCredential(decrypt_secret(connection.encrypted_access_token), connection.expires_at)

    async def list_subscriptions(self, session: AsyncSession, user: User) -> list[SubscriptionDTO]:
        if settings.demo_mode:
            return [
                SubscriptionDTO(
                    subscription_id="demo-subscription",
                    display_name="Demo Azure Subscription",
                    state="Enabled",
                )
            ]
        credential = await self.credential_for_user(session, user)
        try:
            client = SubscriptionClient(credential)
            return [
                SubscriptionDTO(
                    subscription_id=item.subscription_id,
                    display_name=item.display_name or item.subscription_id,
                    state=str(item.state),
                )
                for item in client.subscriptions.list()
            ]
        except Exception as exc:
            raise KubeSageError(
                "Unable to list Azure subscriptions. Confirm the signed-in user has subscription read access.",
                403,
                "azure_subscription_list_failed",
            ) from exc

    async def list_aks_clusters(self, session: AsyncSession, user: User, subscription_id: str) -> list[ClusterDTO]:
        if settings.demo_mode:
            cluster = await self._upsert_demo_cluster(session, user, subscription_id)
            return [self.to_dto(cluster)]
        credential = await self.credential_for_user(session, user)
        try:
            client = ContainerServiceClient(credential, subscription_id)
            clusters = []
            for item in client.managed_clusters.list():
                resource_group = item.id.split("/resourceGroups/")[1].split("/")[0]
                cluster = await self._upsert_cluster(session, user, subscription_id, resource_group, item)
                clusters.append(self.to_dto(cluster))
            return clusters
        except Exception as exc:
            raise KubeSageError(
                "Unable to list AKS clusters. Confirm Azure RBAC allows Microsoft.ContainerService read access.",
                403,
                "aks_cluster_list_failed",
            ) from exc

    async def _upsert_cluster(self, session: AsyncSession, user: User, subscription_id: str, resource_group: str, item) -> Cluster:
        result = await session.execute(
            select(Cluster).where(Cluster.user_id == user.id, Cluster.cluster_resource_id == item.id)
        )
        cluster = result.scalar_one_or_none()
        power_state = getattr(getattr(item, "power_state", None), "code", None)
        values = {
            "subscription_id": subscription_id,
            "resource_group": resource_group,
            "cluster_name": item.name,
            "location": item.location or "",
            "kubernetes_version": item.kubernetes_version or "",
            "cluster_resource_id": item.id,
            "status": power_state or item.provisioning_state or "Unknown",
        }
        if cluster is None:
            cluster = Cluster(user_id=user.id, **values)
            session.add(cluster)
        else:
            for key, value in values.items():
                setattr(cluster, key, value)
        await session.commit()
        await session.refresh(cluster)
        return cluster

    async def _upsert_demo_cluster(self, session: AsyncSession, user: User, subscription_id: str) -> Cluster:
        resource_id = f"/subscriptions/{subscription_id}/resourceGroups/demo-rg/providers/Microsoft.ContainerService/managedClusters/demo-aks"
        result = await session.execute(select(Cluster).where(Cluster.user_id == user.id, Cluster.cluster_resource_id == resource_id))
        cluster = result.scalar_one_or_none()
        values = {
            "subscription_id": subscription_id,
            "resource_group": "demo-rg",
            "cluster_name": "demo-aks",
            "location": "eastus",
            "kubernetes_version": "1.30.0",
            "cluster_resource_id": resource_id,
            "status": "Running",
        }
        if cluster is None:
            cluster = Cluster(user_id=user.id, **values)
            session.add(cluster)
        else:
            for key, value in values.items():
                setattr(cluster, key, value)
        await session.commit()
        await session.refresh(cluster)
        return cluster

    def to_dto(self, cluster: Cluster) -> ClusterDTO:
        return ClusterDTO(
            id=cluster.id,
            subscription_id=cluster.subscription_id,
            resource_group=cluster.resource_group,
            cluster_name=cluster.cluster_name,
            location=cluster.location,
            kubernetes_version=cluster.kubernetes_version,
            cluster_resource_id=cluster.cluster_resource_id,
            status=cluster.status,
        )


azure_service = AzureIntegrationService()
