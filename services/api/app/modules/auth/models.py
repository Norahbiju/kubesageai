from sqlalchemy import ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.shared.database import Base
from app.shared.models import TimestampMixin, UUIDPrimaryKeyMixin


class AzureConnection(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "azure_connections"

    user_id: Mapped[str] = mapped_column(ForeignKey("users.id"))
    tenant_id: Mapped[str] = mapped_column(String(100))
    access_token_hint: Mapped[str] = mapped_column(Text, default="")
    status: Mapped[str] = mapped_column(String(40), default="connected")

    user: Mapped["User"] = relationship(back_populates="azure_connections")
