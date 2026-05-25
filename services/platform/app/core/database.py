from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy import text

from app.core.config import settings


class Base(DeclarativeBase):
    pass


engine = create_async_engine(settings.database_url, pool_pre_ping=True)
SessionLocal = async_sessionmaker(engine, expire_on_commit=False)


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    async with SessionLocal() as session:
        yield session


async def init_database() -> None:
    from app.models import entities  # noqa: F401

    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)
        await connection.execute(text("ALTER TABLE users DROP CONSTRAINT IF EXISTS users_azure_object_id_key"))
        await connection.execute(text("CREATE UNIQUE INDEX IF NOT EXISTS ix_users_tenant_object_unique ON users (tenant_id, azure_object_id)"))
        await connection.execute(text("ALTER TABLE clusters ADD COLUMN IF NOT EXISTS fqdn TEXT DEFAULT ''"))
        await connection.execute(text("ALTER TABLE ai_analyses ADD COLUMN IF NOT EXISTS user_id VARCHAR(36)"))
