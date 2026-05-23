from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.shared.database import Base
from app.shared.models import TimestampMixin, UUIDPrimaryKeyMixin


class User(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "users"

    email: Mapped[str] = mapped_column(String(320), unique=True, index=True)
    display_name: Mapped[str] = mapped_column(String(160))
    azure_subject: Mapped[str] = mapped_column(String(180), unique=True, index=True)

    azure_connections: Mapped[list["AzureConnection"]] = relationship(back_populates="user")
    incidents: Mapped[list["Incident"]] = relationship(back_populates="user")
