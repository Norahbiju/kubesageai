from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

from app.shared.config import settings


class Base(DeclarativeBase):
    pass


engine = create_async_engine(settings.database_url, echo=False)
SessionLocal = async_sessionmaker(engine, expire_on_commit=False)


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    async with SessionLocal() as session:
        yield session


async def create_schema() -> None:
    from app.modules.auth import models as _auth_models
    from app.modules.azure import models as _azure_models
    from app.modules.incidents import models as _incident_models
    from app.modules.remediation import models as _remediation_models
    from app.modules.users import models as _user_models

    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)
