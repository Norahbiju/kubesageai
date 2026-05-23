from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_env: str = "development"
    database_url: str = "sqlite+aiosqlite:///./kubesage.db"
    frontend_url: str = "http://localhost:3000"
    cors_origins: list[str] = Field(default_factory=lambda: ["http://localhost:3000"])

    jwt_secret: str = "dev-only-change-me"
    jwt_algorithm: str = "HS256"
    session_minutes: int = 480

    azure_client_id: str = ""
    azure_client_secret: str = ""
    azure_tenant_id: str = "common"
    azure_redirect_uri: str = "http://localhost:8000/api/auth/azure/callback"

    openai_api_key: str = ""
    openai_model: str = "gpt-4.1-mini"
    demo_mode: bool = True


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
