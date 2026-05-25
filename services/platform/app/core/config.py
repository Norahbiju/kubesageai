from functools import lru_cache
from typing import Literal

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


ServiceName = Literal[
    "api-gateway",
    "auth-service",
    "azure-service",
    "cluster-service",
    "incident-service",
    "ai-analysis-service",
    "remediation-service",
    "notification-stream-service",
    "audit-service",
]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    service_name: ServiceName = "api-gateway"
    app_env: str = "development"
    log_level: str = "INFO"

    postgres_db: str = "kubesage"
    postgres_user: str = "kubesage"
    postgres_password: str = ""
    database_url: str = "postgresql+asyncpg://kubesage:kubesage@postgres:5432/kubesage"
    redis_url: str = "redis://redis:6379/0"

    frontend_url: str = "http://localhost:3000"
    backend_url: str = "http://localhost:8000"
    cors_origins: list[str] = Field(default_factory=lambda: ["http://localhost:3000"])

    azure_tenant_id: str = "organizations"
    azure_authority: str = "https://login.microsoftonline.com/organizations"
    azure_client_id: str
    azure_client_secret: str
    azure_redirect_uri: str
    azure_scopes: str = "openid profile email offline_access https://management.azure.com/user_impersonation"

    openai_api_key: str
    openai_model: str = "gpt-4.1-mini"

    jwt_secret: str
    jwt_algorithm: str = "HS256"
    session_cookie_name: str = "kubesage_session"
    session_minutes: int = 480
    encryption_key: str

    app_name: str = "KubeSage AI"
    app_base_url: str = "http://localhost:3000"
    api_base_url: str = "http://localhost:8000"

    @field_validator("cors_origins", mode="before")
    @classmethod
    def parse_cors(cls, value: object) -> object:
        if isinstance(value, str):
            text = value.strip()
            if text.startswith("["):
                import json

                return json.loads(text)
            return [item.strip() for item in text.split(",") if item.strip()]
        return value

    def validate_runtime(self) -> None:
        required = {
            "AZURE_CLIENT_ID": self.azure_client_id,
            "AZURE_REDIRECT_URI": self.azure_redirect_uri,
            "JWT_SECRET": self.jwt_secret,
            "ENCRYPTION_KEY": self.encryption_key,
            "DATABASE_URL": self.database_url,
            "REDIS_URL": self.redis_url,
        }
        if self.app_env not in {"local", "development", "test"}:
            required.update(
                {
                    "AZURE_CLIENT_SECRET": self.azure_client_secret,
                    "OPENAI_API_KEY": self.openai_api_key,
                }
            )
        missing = [key for key, value in required.items() if not value]
        if missing:
            raise RuntimeError(f"Missing required environment variables: {', '.join(missing)}")


@lru_cache
def get_settings() -> Settings:
    settings = Settings()  # type: ignore[call-arg]
    settings.validate_runtime()
    return settings


settings = get_settings()
