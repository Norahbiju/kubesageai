from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.modules.ai.router import router as ai_router
from app.modules.auth.router import router as auth_router
from app.modules.azure.router import router as azure_router
from app.modules.incidents.router import router as incidents_router
from app.modules.remediation.router import router as remediation_router
from app.shared.config import settings
from app.shared.database import create_schema
from app.shared.errors import register_error_handlers


@asynccontextmanager
async def lifespan(_: FastAPI):
    await create_schema()
    yield


app = FastAPI(title="KubeSage AI API", version="0.1.0", lifespan=lifespan)

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
