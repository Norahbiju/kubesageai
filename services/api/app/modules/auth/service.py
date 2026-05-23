from urllib.parse import urlencode

import httpx
from jose import jwt
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.auth.models import AzureConnection
from app.modules.users.models import User
from app.shared.config import settings
from app.shared.errors import KubeSageError
from app.shared.security import create_access_token


class AuthService:
    def azure_login_url(self, state: str) -> str:
        if settings.demo_mode:
            return f"{settings.azure_redirect_uri}?code=demo"
        if not settings.azure_client_id:
            raise KubeSageError("Azure client ID is not configured", 500)

        query = urlencode(
            {
                "client_id": settings.azure_client_id,
                "response_type": "code",
                "redirect_uri": settings.azure_redirect_uri,
                "response_mode": "query",
                "scope": "openid profile email offline_access https://management.azure.com/user_impersonation",
                "state": state,
            }
        )
        return f"https://login.microsoftonline.com/{settings.azure_tenant_id}/oauth2/v2.0/authorize?{query}"

    async def exchange_code(self, session: AsyncSession, code: str) -> str:
        if settings.demo_mode:
            return await self._create_demo_session(session)
        if not settings.azure_client_secret:
            raise KubeSageError("Azure client secret is not configured", 500)

        token_endpoint = f"https://login.microsoftonline.com/{settings.azure_tenant_id}/oauth2/v2.0/token"
        async with httpx.AsyncClient(timeout=20) as client:
            response = await client.post(
                token_endpoint,
                data={
                    "client_id": settings.azure_client_id,
                    "client_secret": settings.azure_client_secret,
                    "code": code,
                    "grant_type": "authorization_code",
                    "redirect_uri": settings.azure_redirect_uri,
                },
            )
            response.raise_for_status()
            token_payload = response.json()
        try:
            claims = jwt.get_unverified_claims(token_payload.get("id_token", ""))
        except Exception:
            claims = {}
        subject = claims.get("oid") or claims.get("sub") or "azure-user"
        email = claims.get("preferred_username") or claims.get("email") or f"{subject}@unknown.local"
        name = claims.get("name") or email
        return await self._upsert_user(session, subject, email, name, token_payload["access_token"])

    async def _create_demo_session(self, session: AsyncSession) -> str:
        return await self._upsert_user(session, "demo-azure-subject", "sre@contoso.com", "Demo SRE", "demo-token")

    async def _upsert_user(self, session: AsyncSession, subject: str, email: str, name: str, access_token: str) -> str:
        result = await session.execute(select(User).where(User.azure_subject == subject))
        user = result.scalar_one_or_none()
        if user is None:
            user = User(email=email, display_name=name, azure_subject=subject)
            session.add(user)
            await session.flush()
            session.add(AzureConnection(user_id=user.id, tenant_id=settings.azure_tenant_id, access_token_hint=access_token[-8:]))
        await session.commit()
        return create_access_token(user.id)
