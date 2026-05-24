import secrets
from datetime import datetime, timedelta, timezone
from urllib.parse import urlencode

import httpx
from jose import JWTError, jwt
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.errors import KubeSageError
from app.core.security import create_session_token, encrypt_secret
from app.models.entities import AzureConnection, User

AUTHORITY = "https://login.microsoftonline.com"


class AuthService:
    def create_state(self) -> str:
        return secrets.token_urlsafe(32)

    def login_url(self, state: str) -> str:
        if settings.demo_mode:
            return f"{settings.backend_url}/auth/callback?code=demo&state={state}"
        query = urlencode(
            {
                "client_id": settings.azure_client_id,
                "response_type": "code",
                "redirect_uri": settings.azure_redirect_uri,
                "response_mode": "query",
                "scope": "openid profile email offline_access https://management.azure.com/user_impersonation",
                "state": state,
                "prompt": "select_account",
            }
        )
        return f"{AUTHORITY}/{settings.azure_tenant_id}/oauth2/v2.0/authorize?{query}"

    async def exchange_code(self, session: AsyncSession, code: str) -> tuple[User, str]:
        if settings.demo_mode and code == "demo":
            user = await self._upsert_user(
                session,
                {
                    "oid": "demo-local-user",
                    "preferred_username": "demo@kubesage.local",
                    "name": "Demo Operator",
                    "tid": "demo-tenant",
                },
                {"access_token": "demo-access-token", "refresh_token": "demo-refresh-token", "expires_in": 3600},
            )
            return user, create_session_token(user.id)

        token_endpoint = f"{AUTHORITY}/{settings.azure_tenant_id}/oauth2/v2.0/token"
        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.post(
                token_endpoint,
                data={
                    "client_id": settings.azure_client_id,
                    "client_secret": settings.azure_client_secret,
                    "code": code,
                    "grant_type": "authorization_code",
                    "redirect_uri": settings.azure_redirect_uri,
                    "scope": "openid profile email offline_access https://management.azure.com/user_impersonation",
                },
            )
        if response.status_code >= 400:
            raise KubeSageError("Azure login failed during token exchange", 401, "azure_token_exchange_failed")
        payload = response.json()
        claims = await self._validate_id_token(payload.get("id_token", ""))
        user = await self._upsert_user(session, claims, payload)
        return user, create_session_token(user.id)

    async def _validate_id_token(self, id_token: str) -> dict:
        try:
            unverified = jwt.get_unverified_claims(id_token)
        except JWTError as exc:
            raise KubeSageError("Azure ID token could not be parsed", 401, "invalid_id_token") from exc

        tenant_id = unverified.get("tid") or settings.azure_tenant_id
        metadata_url = f"{AUTHORITY}/{tenant_id}/v2.0/.well-known/openid-configuration"
        async with httpx.AsyncClient(timeout=20) as client:
            metadata = (await client.get(metadata_url)).json()
            jwks = (await client.get(metadata["jwks_uri"])).json()
        try:
            claims = jwt.decode(
                id_token,
                jwks,
                algorithms=["RS256"],
                audience=settings.azure_client_id,
                options={"verify_at_hash": False},
            )
        except JWTError as exc:
            raise KubeSageError("Azure ID token signature validation failed", 401, "invalid_id_token") from exc
        if claims.get("tid") not in {settings.azure_tenant_id, "common", "organizations"} and settings.azure_tenant_id not in {
            "common",
            "organizations",
        }:
            raise KubeSageError("Azure tenant mismatch", 401, "invalid_tenant")
        return claims

    async def _upsert_user(self, session: AsyncSession, claims: dict, token_payload: dict) -> User:
        object_id = claims.get("oid") or claims.get("sub")
        if not object_id:
            raise KubeSageError("Azure token did not include a user identifier", 401, "missing_azure_subject")
        email = claims.get("preferred_username") or claims.get("email") or ""
        name = claims.get("name") or email
        tenant_id = claims.get("tid") or settings.azure_tenant_id

        result = await session.execute(select(User).where(User.azure_object_id == object_id))
        user = result.scalar_one_or_none()
        if user is None:
            user = User(azure_object_id=object_id, email=email, display_name=name, tenant_id=tenant_id)
            session.add(user)
            await session.flush()
        else:
            user.email = email
            user.display_name = name
            user.tenant_id = tenant_id

        expires_in = int(token_payload.get("expires_in", 3600))
        connection = AzureConnection(
            user_id=user.id,
            tenant_id=tenant_id,
            subscription_id="",
            encrypted_access_token=encrypt_secret(token_payload["access_token"]),
            encrypted_refresh_token=encrypt_secret(token_payload.get("refresh_token", "")),
            expires_at=datetime.now(timezone.utc) + timedelta(seconds=expires_in),
        )
        session.add(connection)
        await session.commit()
        await session.refresh(user)
        return user


auth_service = AuthService()
