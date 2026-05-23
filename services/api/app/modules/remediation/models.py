from sqlalchemy import ForeignKey, JSON, String
from sqlalchemy.orm import Mapped, mapped_column

from app.shared.database import Base
from app.shared.models import TimestampMixin, UUIDPrimaryKeyMixin


class RemediationAction(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "remediation_actions"

    incident_id: Mapped[str] = mapped_column(ForeignKey("incidents.id"))
    action_type: Mapped[str] = mapped_column(String(80))
    parameters: Mapped[dict] = mapped_column(JSON, default=dict)
    status: Mapped[str] = mapped_column(String(40), default="approved")
    result: Mapped[str] = mapped_column(String(500), default="")


class AuditLog(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "audit_logs"

    actor_user_id: Mapped[str] = mapped_column(String(80), default="demo-user")
    action: Mapped[str] = mapped_column(String(120))
    target: Mapped[str] = mapped_column(String(180))
    metadata_json: Mapped[dict] = mapped_column(JSON, default=dict)
