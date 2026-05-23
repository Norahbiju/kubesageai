from fastapi import APIRouter, Depends
from fastapi.responses import RedirectResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.auth.schemas import SessionResponse
from app.modules.auth.service import AuthService
from app.shared.config import settings
from app.shared.database import get_session

router = APIRouter()
service = AuthService()


@router.get("/azure/login")
async def azure_login() -> RedirectResponse:
    return RedirectResponse(service.azure_login_url())


@router.get("/azure/callback", response_model=SessionResponse)
async def azure_callback(code: str = "demo", session: AsyncSession = Depends(get_session)) -> RedirectResponse:
    token = await service.exchange_code(session, code)
    return RedirectResponse(f"{settings.frontend_url}/dashboard?token={token}")
