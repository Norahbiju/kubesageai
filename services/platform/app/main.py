from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.core.database import init_database
from app.core.errors import register_error_handlers
from app.core.logging import configure_logging, request_logging_middleware
from app.routers.gateway import router as gateway_router
from app.routers.health import router as health_router

configure_logging()


@asynccontextmanager
async def lifespan(_: FastAPI):
    if settings.service_name in {"api-gateway", "auth-service", "azure-service", "cluster-service", "incident-service", "ai-analysis-service", "remediation-service", "audit-service"}:
        await init_database()
    yield


app = FastAPI(title=f"KubeSage AI {settings.service_name}", version="1.0.0", lifespan=lifespan)
app.middleware("http")(request_logging_middleware)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

register_error_handlers(app)
app.include_router(health_router)

if settings.service_name == "api-gateway":
    app.include_router(gateway_router)
