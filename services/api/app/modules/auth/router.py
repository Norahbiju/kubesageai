from fastapi import APIRouter, Depends
from fastapi.responses import RedirectResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.auth.service import AuthService
from app.shared.config import settings
from app.shared.database import get_session
from app.shared.security import get_current_user
from app.modules.users.models import User

router = APIRouter()
service = AuthService()


@router.get("/azure/login")
async def azure_login() -> RedirectResponse:
    return RedirectResponse(service.azure_login_url())


@router.get("/demo/login")
async def demo_login() -> RedirectResponse:
    return RedirectResponse(f"{settings.azure_redirect_uri}?code=demo")


@router.get("/azure/callback")
async def azure_callback(code: str = "demo", session: AsyncSession = Depends(get_session)) -> RedirectResponse:
    token = await service.exchange_code(session, code)
    return RedirectResponse(f"{settings.frontend_url}/dashboard?token={token}")


@router.get("/me")
async def me(user: User = Depends(get_current_user)) -> dict[str, str]:
    return {"id": user.id, "email": user.email, "display_name": user.display_name}
