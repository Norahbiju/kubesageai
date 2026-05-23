from fastapi import APIRouter

from app.modules.ai.service import AIAnalysisService
from app.shared.config import settings

router = APIRouter()


@router.get("/models")
async def models() -> dict[str, list[str]]:
    return {"models": ["gpt-4.1-mini", "gpt-4.1"]}


@router.get("/health")
async def openai_health() -> dict[str, str]:
    if not settings.openai_api_key:
        return {"status": "not_configured", "model": settings.openai_model}
    service = AIAnalysisService()
    try:
        await service.client.models.retrieve(settings.openai_model)  # type: ignore[union-attr]
    except Exception as exc:
        return {"status": "error", "model": settings.openai_model, "detail": str(exc)}
    return {"status": "ok", "model": settings.openai_model}
