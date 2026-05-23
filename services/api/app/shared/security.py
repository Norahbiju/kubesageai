from datetime import datetime, timedelta, timezone

from fastapi import Depends, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import jwt
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.users.models import User
from app.shared.config import settings
from app.shared.database import get_session
from app.shared.errors import KubeSageError

bearer_scheme = HTTPBearer(auto_error=False)


def create_access_token(subject: str) -> str:
    expires_at = datetime.now(timezone.utc) + timedelta(minutes=settings.session_minutes)
    return jwt.encode({"sub": subject, "exp": expires_at}, settings.jwt_secret, algorithm=settings.jwt_algorithm)


async def get_current_user(
    request: Request,
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    session: AsyncSession = Depends(get_session),
) -> User:
    token = credentials.credentials if credentials else request.cookies.get("kubesage_session")
    if not token:
        raise KubeSageError("Missing bearer token", 401)
    try:
        payload = jwt.decode(token, settings.jwt_secret, algorithms=[settings.jwt_algorithm])
    except Exception as exc:
        raise KubeSageError("Invalid or expired bearer token", 401) from exc
    user_id = payload.get("sub")
    user = await session.get(User, user_id)
    if user is None:
        raise KubeSageError("User not found", 401)
    return user
