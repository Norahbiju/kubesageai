import uuid
from datetime import datetime, timezone

from sqlalchemy import DateTime, Float, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


def now_utc() -> datetime:
    return datetime.now(timezone.utc)


def new_id() -> str:
    return str(uuid.uuid4())


class TimestampMixin:
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now_utc)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now_utc, onupdate=now_utc)


class User(Base, TimestampMixin):
    __tablename__ = "users"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    azure_object_id: Mapped[str] = mapped_column(String(180), unique=True, index=True)
    email: Mapped[str] = mapped_column(String(320), index=True)
    display_name: Mapped[str] = mapped_column(String(240))
    tenant_id: Mapped[str] = mapped_column(String(120), index=True)


class AzureConnection(Base, TimestampMixin):
    __tablename__ = "azure_connections"
    __table_args__ = (UniqueConstraint("user_id", "tenant_id", "subscription_id", name="uq_user_tenant_subscription"),)

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id"), index=True)
    tenant_id: Mapped[str] = mapped_column(String(120), index=True)
    subscription_id: Mapped[str] = mapped_column(String(120), index=True, default="")
    encrypted_access_token: Mapped[str] = mapped_column(Text)
    encrypted_refresh_token: Mapped[str] = mapped_column(Text)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))


class Cluster(Base, TimestampMixin):
    __tablename__ = "clusters"
    __table_args__ = (UniqueConstraint("user_id", "cluster_resource_id", name="uq_user_cluster_resource"),)

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id"), index=True)
    subscription_id: Mapped[str] = mapped_column(String(120), index=True)
    resource_group: Mapped[str] = mapped_column(String(240), index=True)
    cluster_name: Mapped[str] = mapped_column(String(240), index=True)
    location: Mapped[str] = mapped_column(String(120))
    kubernetes_version: Mapped[str] = mapped_column(String(80))
    cluster_resource_id: Mapped[str] = mapped_column(Text, index=True)
    status: Mapped[str] = mapped_column(String(80))


class Incident(Base, TimestampMixin):
    __tablename__ = "incidents"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id"), index=True)
    cluster_id: Mapped[str] = mapped_column(ForeignKey("clusters.id"), index=True)
    namespace: Mapped[str] = mapped_column(String(240), index=True)
    workload_name: Mapped[str] = mapped_column(String(240), index=True)
    workload_type: Mapped[str] = mapped_column(String(80))
    issue_type: Mapped[str] = mapped_column(String(120), index=True)
    severity: Mapped[str] = mapped_column(String(40), index=True)
    status: Mapped[str] = mapped_column(String(60), default="detected")
    detected_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now_utc)


class IncidentSignal(Base):
    __tablename__ = "incident_signals"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    incident_id: Mapped[str] = mapped_column(ForeignKey("incidents.id"), index=True)
    signal_type: Mapped[str] = mapped_column(String(120))
    source: Mapped[str] = mapped_column(String(240))
    message: Mapped[str] = mapped_column(Text)
    raw_payload_json: Mapped[dict] = mapped_column(JSONB, default=dict)
    timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now_utc)


class AIAnalysis(Base):
    __tablename__ = "ai_analyses"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    incident_id: Mapped[str] = mapped_column(ForeignKey("incidents.id"), index=True)
    summary: Mapped[str] = mapped_column(Text)
    root_cause: Mapped[str] = mapped_column(Text)
    severity: Mapped[str] = mapped_column(String(40))
    confidence_score: Mapped[float] = mapped_column(Float)
    affected_services_json: Mapped[list] = mapped_column(JSONB, default=list)
    remediation_json: Mapped[list] = mapped_column(JSONB, default=list)
    timeline_json: Mapped[list] = mapped_column(JSONB, default=list)
    model_used: Mapped[str] = mapped_column(String(120))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now_utc)


class RemediationAction(Base):
    __tablename__ = "remediation_actions"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    incident_id: Mapped[str] = mapped_column(ForeignKey("incidents.id"), index=True)
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id"), index=True)
    action_type: Mapped[str] = mapped_column(String(120))
    action_payload_json: Mapped[dict] = mapped_column(JSONB, default=dict)
    approval_status: Mapped[str] = mapped_column(String(60), default="pending")
    execution_status: Mapped[str] = mapped_column(String(60), default="not_started")
    execution_result: Mapped[str] = mapped_column(Text, default="")
    approved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    executed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now_utc)


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    user_id: Mapped[str | None] = mapped_column(ForeignKey("users.id"), nullable=True, index=True)
    action: Mapped[str] = mapped_column(String(180), index=True)
    resource_type: Mapped[str] = mapped_column(String(120), index=True)
    resource_id: Mapped[str] = mapped_column(String(240), index=True)
    details_json: Mapped[dict] = mapped_column(JSONB, default=dict)
    ip_address: Mapped[str] = mapped_column(String(80), default="")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now_utc)
