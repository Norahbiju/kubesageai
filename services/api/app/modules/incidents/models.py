from sqlalchemy import Float, ForeignKey, JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.shared.database import Base
from app.shared.models import TimestampMixin, UUIDPrimaryKeyMixin


class Incident(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "incidents"

    user_id: Mapped[str] = mapped_column(ForeignKey("users.id"), default="demo-user")
    cluster_id: Mapped[str] = mapped_column(ForeignKey("clusters.id"))
    title: Mapped[str] = mapped_column(String(200))
    cluster_name: Mapped[str] = mapped_column(String(160))
    severity: Mapped[str] = mapped_column(String(40), default="medium")
    status: Mapped[str] = mapped_column(String(40), default="analyzed")
    confidence_score: Mapped[float] = mapped_column(Float, default=0)
    raw_signals: Mapped[dict] = mapped_column(JSON, default=dict)

    user: Mapped["User"] = relationship(back_populates="incidents")
    analyses: Mapped[list["Analysis"]] = relationship(back_populates="incident")


class Analysis(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "analyses"

    incident_id: Mapped[str] = mapped_column(ForeignKey("incidents.id"))
    summary: Mapped[str] = mapped_column(Text)
    root_cause: Mapped[str] = mapped_column(Text)
    severity: Mapped[str] = mapped_column(String(40))
    confidence_score: Mapped[float] = mapped_column(Float)
    affected_services: Mapped[list[str]] = mapped_column(JSON, default=list)
    remediation: Mapped[list[str]] = mapped_column(JSON, default=list)
    timeline: Mapped[list[str]] = mapped_column(JSON, default=list)
    recommended_action: Mapped[str] = mapped_column(String(120))

    incident: Mapped[Incident] = relationship(back_populates="analyses")
