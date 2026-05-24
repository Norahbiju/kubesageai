from datetime import datetime, timedelta, timezone

from cryptography.fernet import Fernet, InvalidToken
from fastapi import Depends, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.database import get_session
from app.core.errors import KubeSageError
from app.models.entities import User

bearer_scheme = HTTPBearer(auto_error=False)


def create_session_token(user_id: str) -> str:
    expires_at = datetime.now(timezone.utc) + timedelta(minutes=settings.session_minutes)
    return jwt.encode({"sub": user_id, "exp": expires_at}, settings.jwt_secret, algorithm=settings.jwt_algorithm)


def encrypt_secret(value: str) -> str:
    return Fernet(settings.encryption_key.encode()).encrypt(value.encode()).decode()


def decrypt_secret(value: str) -> str:
    try:
        return Fernet(settings.encryption_key.encode()).decrypt(value.encode()).decode()
    except InvalidToken as exc:
        raise KubeSageError("Stored Azure token cannot be decrypted", 500, "token_decryption_failed") from exc


async def current_user(
    request: Request,
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    session: AsyncSession = Depends(get_session),
) -> User:
    token = credentials.credentials if credentials else request.cookies.get(settings.session_cookie_name)
    if not token:
        raise KubeSageError("Authentication required", 401, "auth_required")
    try:
        payload = jwt.decode(token, settings.jwt_secret, algorithms=[settings.jwt_algorithm])
    except JWTError as exc:
        raise KubeSageError("Invalid or expired session", 401, "invalid_session") from exc
    user_id = payload.get("sub")
    result = await session.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if user is None:
        raise KubeSageError("User not found", 401, "user_not_found")
    return user
