from fastapi import APIRouter
from redis.asyncio import Redis
from sqlalchemy import text

from app.core.config import settings
from app.core.database import engine

router = APIRouter()


@router.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok", "service": settings.service_name}


@router.get("/health/database")
async def database_health() -> dict[str, str]:
    async with engine.connect() as connection:
        await connection.execute(text("select 1"))
    return {"status": "ok"}


@router.get("/health/redis")
async def redis_health() -> dict[str, str]:
    redis = Redis.from_url(settings.redis_url)
    await redis.ping()
    return {"status": "ok"}


@router.get("/health/openai")
async def openai_health() -> dict[str, str]:
    return {"status": "configured" if settings.openai_api_key else "missing"}


@router.get("/health/azure")
async def azure_health() -> dict[str, str]:
    return {"status": "configured" if settings.azure_client_id and settings.azure_client_secret else "missing"}
