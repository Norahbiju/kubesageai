from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_env: str = "development"
    database_url: str = "sqlite+aiosqlite:///./kubesage.db"
    frontend_url: str = "http://localhost:3000"
    backend_url: str = "http://localhost:8000"
    cors_origins: list[str] = Field(default_factory=lambda: ["http://localhost:3000"])

    jwt_secret: str = "dev-only-change-me"
    nextauth_secret: str = ""
    jwt_algorithm: str = "HS256"
    session_minutes: int = 480

    azure_client_id: str = ""
    azure_client_secret: str = ""
    azure_tenant_id: str = "common"
    azure_redirect_uri: str = "http://localhost:8000/api/auth/azure/callback"
    azure_subscription_ids: list[str] = Field(default_factory=list)

    openai_api_key: str = ""
    openai_model: str = "gpt-4.1-mini"
    demo_mode: bool = True

    def validate_startup(self) -> list[str]:
        warnings: list[str] = []
        if not self.demo_mode:
            missing = [
                name
                for name, value in {
                    "AZURE_CLIENT_ID": self.azure_client_id,
                    "AZURE_CLIENT_SECRET": self.azure_client_secret,
                    "AZURE_TENANT_ID": self.azure_tenant_id,
                    "AZURE_REDIRECT_URI": self.azure_redirect_uri,
                }.items()
                if not value or value == "common"
            ]
            if missing:
                warnings.append(f"Real Azure auth is enabled but missing/invalid variables: {', '.join(missing)}")
        if not self.openai_api_key:
            warnings.append("OPENAI_API_KEY is not configured; analysis will use deterministic fallback output.")
        if self.jwt_secret in {"dev-only-change-me", "change-me-for-local-compose", "replace-with-a-long-random-string"}:
            warnings.append("JWT_SECRET is using a development value.")
        return warnings


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
