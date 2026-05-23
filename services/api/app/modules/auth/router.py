import secrets
from urllib.parse import urlencode

from fastapi import APIRouter, Depends, Request
from fastapi.responses import RedirectResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.auth.service import AuthService
from app.shared.config import settings
from app.shared.database import get_session
from app.shared.errors import KubeSageError
from app.shared.security import get_current_user
from app.modules.users.models import User

router = APIRouter()
service = AuthService()
STATE_COOKIE = "kubesage_oauth_state"
SESSION_COOKIE = "kubesage_session"


@router.get("/azure/login")
async def azure_login() -> RedirectResponse:
    state = secrets.token_urlsafe(32)
    response = RedirectResponse(service.azure_login_url(state))
    response.set_cookie(
        STATE_COOKIE,
        state,
        max_age=600,
        httponly=True,
        secure=settings.public_https,
        samesite="lax",
    )
    return response


@router.get("/demo/login")
async def demo_login() -> RedirectResponse:
    return RedirectResponse(f"{settings.azure_redirect_uri}?code=demo")


@router.get("/azure/callback")
async def azure_callback(
    request: Request,
    code: str | None = None,
    state: str | None = None,
    error: str | None = None,
    error_description: str | None = None,
    session: AsyncSession = Depends(get_session),
) -> RedirectResponse:
    if error:
        message = error_description or error
        return RedirectResponse(f"{settings.frontend_url}/login?{urlencode({'error': message})}")
    if not code:
        raise KubeSageError("Azure callback did not include an authorization code", 400)
    if not settings.demo_mode:
        expected_state = request.cookies.get(STATE_COOKIE)
        if not expected_state or not state or not secrets.compare_digest(expected_state, state):
            raise KubeSageError("Invalid Azure login state", 400)

    token = await service.exchange_code(session, code)
    response = RedirectResponse(f"{settings.frontend_url}/dashboard")
    response.delete_cookie(STATE_COOKIE)
    response.set_cookie(
        SESSION_COOKIE,
        token,
        max_age=settings.session_minutes * 60,
        httponly=True,
        secure=settings.public_https,
        samesite="lax",
    )
    return response


@router.get("/me")
async def me(user: User = Depends(get_current_user)) -> dict[str, str]:
    return {"id": user.id, "email": user.email, "display_name": user.display_name}
