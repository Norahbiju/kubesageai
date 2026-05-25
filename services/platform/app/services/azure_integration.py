from datetime import datetime, timedelta, timezone
from urllib.parse import quote

import httpx
from azure.core.credentials import AccessToken, TokenCredential
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.errors import KubeSageError
from app.core.security import decrypt_secret, encrypt_secret
from app.models.entities import AzureConnection, Cluster, Subscription, User
from app.schemas.dto import ClusterDTO, SubscriptionDTO

ARM_BASE_URL = "https://management.azure.com"
SUBSCRIPTIONS_API_VERSION = "2020-01-01"
AKS_API_VERSION = "2024-02-01"
TOKEN_REFRESH_SKEW = timedelta(minutes=5)


class UserTokenCredential(TokenCredential):
    def __init__(self, access_token: str, expires_on: datetime) -> None:
        self.access_token = access_token
        self.expires_on = expires_on

    def get_token(self, *scopes: str, **kwargs) -> AccessToken:
        return AccessToken(self.access_token, int(self.expires_on.timestamp()))


class AzureIntegrationService:
    async def credential_for_user(self, session: AsyncSession, user: User) -> UserTokenCredential:
        connection = await self.connection_for_user(session, user)
        return UserTokenCredential(decrypt_secret(connection.encrypted_access_token), connection.expires_at)

    async def connection_for_user(self, session: AsyncSession, user: User) -> AzureConnection:
        result = await session.execute(
            select(AzureConnection)
            .where(AzureConnection.user_id == user.id)
            .order_by(AzureConnection.updated_at.desc())
            .limit(1)
        )
        connection = result.scalar_one_or_none()
        if connection is None:
            raise KubeSageError("Azure login is required.", 401, "azure_login_required")
        if connection.expires_at <= datetime.now(timezone.utc) + TOKEN_REFRESH_SKEW:
            connection = await self.refresh_connection(session, connection)
        return connection

    async def refresh_connection(self, session: AsyncSession, connection: AzureConnection) -> AzureConnection:
        refresh_token = decrypt_secret(connection.encrypted_refresh_token)
        if not refresh_token:
            raise KubeSageError("Azure session expired. Please login again.", 401, "azure_session_expired")

        token_endpoint = f"{settings.azure_authority.rstrip('/')}/oauth2/v2.0/token"
        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.post(
                token_endpoint,
                data={
                    "client_id": settings.azure_client_id,
                    "client_secret": settings.azure_client_secret,
                    "grant_type": "refresh_token",
                    "refresh_token": refresh_token,
                    "scope": settings.azure_scopes,
                },
            )
        if response.status_code >= 400:
            raise KubeSageError("Azure session expired. Please login again.", 401, "azure_session_expired")

        payload = response.json()
        connection.encrypted_access_token = encrypt_secret(payload["access_token"])
        if payload.get("refresh_token"):
            connection.encrypted_refresh_token = encrypt_secret(payload["refresh_token"])
        connection.expires_at = datetime.now(timezone.utc) + timedelta(seconds=int(payload.get("expires_in", 3600)))
        await session.commit()
        await session.refresh(connection)
        return connection

    async def arm_get(self, session: AsyncSession, user: User, path: str, params: dict[str, str]) -> dict:
        connection = await self.connection_for_user(session, user)
        token = decrypt_secret(connection.encrypted_access_token)
        async with httpx.AsyncClient(timeout=45) as client:
            response = await client.get(
                f"{ARM_BASE_URL}{path}",
                params=params,
                headers={"Authorization": f"Bearer {token}"},
            )
        if response.status_code == 401:
            connection = await self.refresh_connection(session, connection)
            token = decrypt_secret(connection.encrypted_access_token)
            async with httpx.AsyncClient(timeout=45) as client:
                response = await client.get(
                    f"{ARM_BASE_URL}{path}",
                    params=params,
                    headers={"Authorization": f"Bearer {token}"},
                )
        if response.status_code >= 400:
            self._raise_azure_error(response, path)
        return response.json()

    async def list_subscriptions(self, session: AsyncSession, user: User) -> list[SubscriptionDTO]:
        payload = await self.arm_get(
            session,
            user,
            "/subscriptions",
            {"api-version": SUBSCRIPTIONS_API_VERSION},
        )
        subscriptions = []
        for item in payload.get("value", []):
            subscription_id = item.get("subscriptionId", "")
            if not subscription_id:
                continue
            dto = SubscriptionDTO(
                subscription_id=subscription_id,
                display_name=item.get("displayName") or subscription_id,
                state=str(item.get("state") or "Unknown"),
                tenant_id=item.get("tenantId") or user.tenant_id,
            )
            await self._upsert_subscription(session, user, dto)
            subscriptions.append(dto)
        return subscriptions

    async def list_aks_clusters(self, session: AsyncSession, user: User, subscription_id: str) -> list[ClusterDTO]:
        await self.ensure_subscription_access(session, user, subscription_id)
        payload = await self.arm_get(
            session,
            user,
            f"/subscriptions/{quote(subscription_id)}/providers/Microsoft.ContainerService/managedClusters",
            {"api-version": AKS_API_VERSION},
        )
        clusters = []
        for item in payload.get("value", []):
            cluster = await self._upsert_cluster(session, user, subscription_id, item)
            clusters.append(self.to_dto(cluster))
        return clusters

    async def list_all_aks_clusters(self, session: AsyncSession, user: User) -> list[ClusterDTO]:
        clusters: list[ClusterDTO] = []
        for subscription in await self.list_subscriptions(session, user):
            clusters.extend(await self.list_aks_clusters(session, user, subscription.subscription_id))
        return clusters

    async def ensure_subscription_access(self, session: AsyncSession, user: User, subscription_id: str) -> None:
        subscriptions = await self.list_subscriptions(session, user)
        if subscription_id not in {item.subscription_id for item in subscriptions}:
            raise KubeSageError("Your Azure account does not have permission to list subscriptions.", 403, "subscription_access_denied")

    async def verify_cluster_access(self, session: AsyncSession, user: User, cluster_resource_id: str) -> Cluster:
        await self.list_all_aks_clusters(session, user)
        result = await session.execute(
            select(Cluster).where(Cluster.user_id == user.id, Cluster.cluster_resource_id == cluster_resource_id)
        )
        cluster = result.scalar_one_or_none()
        if cluster is None:
            raise KubeSageError("You do not have permission to access this AKS cluster.", 403, "cluster_access_denied")
        return cluster

    async def connectivity_check(self, session: AsyncSession, user: User) -> dict:
        subscriptions = await self.list_subscriptions(session, user)
        return {
            "authenticated": True,
            "azure_connected": True,
            "subscription_count": len(subscriptions),
            "tenant_id": user.tenant_id,
        }

    async def _upsert_subscription(self, session: AsyncSession, user: User, dto: SubscriptionDTO) -> Subscription:
        result = await session.execute(
            select(Subscription).where(Subscription.user_id == user.id, Subscription.subscription_id == dto.subscription_id)
        )
        subscription = result.scalar_one_or_none()
        values = {
            "display_name": dto.display_name,
            "tenant_id": dto.tenant_id or user.tenant_id,
            "state": dto.state,
        }
        if subscription is None:
            subscription = Subscription(user_id=user.id, subscription_id=dto.subscription_id, **values)
            session.add(subscription)
        else:
            for key, value in values.items():
                setattr(subscription, key, value)
        await session.commit()
        await session.refresh(subscription)
        return subscription

    async def _upsert_cluster(self, session: AsyncSession, user: User, subscription_id: str, item: dict) -> Cluster:
        resource_id = item.get("id", "")
        if not resource_id:
            raise KubeSageError("Azure returned an AKS cluster without a resource ID.", 502, "invalid_azure_cluster")
        resource_group = resource_id.split("/resourceGroups/")[1].split("/")[0]
        properties = item.get("properties") or {}
        values = {
            "subscription_id": subscription_id,
            "resource_group": resource_group,
            "cluster_name": item.get("name") or "",
            "location": item.get("location") or "",
            "kubernetes_version": properties.get("kubernetesVersion") or properties.get("currentKubernetesVersion") or "",
            "cluster_resource_id": resource_id,
            "status": properties.get("provisioningState") or "Unknown",
            "fqdn": properties.get("fqdn") or "",
        }
        result = await session.execute(
            select(Cluster).where(Cluster.user_id == user.id, Cluster.cluster_resource_id == resource_id)
        )
        cluster = result.scalar_one_or_none()
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
            fqdn=cluster.fqdn,
        )

    def _raise_azure_error(self, response: httpx.Response, path: str) -> None:
        try:
            error = response.json().get("error", {})
            message = error.get("message") or response.text
            code = error.get("code") or "azure_request_failed"
        except Exception:
            message = response.text
            code = "azure_request_failed"
        if "/subscriptions" == path:
            raise KubeSageError("Your Azure account does not have permission to list subscriptions.", 403, "azure_subscription_list_failed")
        if "managedClusters" in path:
            raise KubeSageError(
                f"Unable to list AKS clusters. Azure returned {response.status_code}: {message}",
                403,
                "aks_cluster_list_failed",
            )
        raise KubeSageError(f"Azure Resource Manager request failed: {message}", response.status_code, code)


azure_service = AzureIntegrationService()
