from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import asyncio

from app.modules.azure.service import AzureDiscoveryService
from app.modules.ai.router import router as ai_router
from app.modules.auth.router import router as auth_router
from app.modules.azure.router import router as azure_router
from app.modules.incidents.router import router as incidents_router
from app.modules.remediation.router import router as remediation_router
from app.shared.config import settings
from app.shared.database import create_schema
from app.shared.errors import register_error_handlers
from app.shared.logging import configure_logging, request_logging_middleware

configure_logging()


@asynccontextmanager
async def lifespan(_: FastAPI):
    await create_schema()
    import logging

    logger = logging.getLogger("kubesage.startup")
    logger.info("starting app_env=%s demo_mode=%s frontend_url=%s backend_url=%s", settings.app_env, settings.demo_mode, settings.frontend_url, settings.backend_url)
    for warning in settings.validate_startup():
        logger.warning(warning)
    yield


app = FastAPI(title="KubeSage AI API", version="0.1.0", lifespan=lifespan)
app.middleware("http")(request_logging_middleware)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

register_error_handlers(app)
app.include_router(auth_router, prefix="/api/auth", tags=["auth"])
app.include_router(azure_router, prefix="/api/azure", tags=["azure"])
app.include_router(incidents_router, prefix="/api/incidents", tags=["incidents"])
app.include_router(ai_router, prefix="/api/ai", tags=["ai"])
app.include_router(remediation_router, prefix="/api/remediation", tags=["remediation"])


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/health/azure")
async def azure_health() -> dict[str, str | int]:
    if settings.demo_mode:
        return {"status": "demo_mode"}
    try:
        subscriptions = await asyncio.to_thread(AzureDiscoveryService().subscription_ids)
    except Exception as exc:
        return {"status": "error", "detail": str(exc)}
    return {"status": "ok", "subscriptions": len(subscriptions)}


@app.get("/health/openai")
async def openai_health_alias() -> dict[str, str]:
    from app.modules.ai.router import openai_health

    return await openai_health()
