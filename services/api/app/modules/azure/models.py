from sqlalchemy import ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.shared.database import Base
from app.shared.models import TimestampMixin, UUIDPrimaryKeyMixin


class Cluster(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "clusters"

    user_id: Mapped[str] = mapped_column(ForeignKey("users.id"), default="demo-user")
    name: Mapped[str] = mapped_column(String(160))
    resource_group: Mapped[str] = mapped_column(String(160))
    subscription_id: Mapped[str] = mapped_column(String(120), index=True)
    location: Mapped[str] = mapped_column(String(80))
    kubernetes_version: Mapped[str] = mapped_column(String(40))
    status: Mapped[str] = mapped_column(String(40), default="Running")
    failing_workloads: Mapped[int] = mapped_column(Integer, default=0)
