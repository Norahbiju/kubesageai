from fastapi import Request
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.entities import AuditLog


async def audit(
    session: AsyncSession,
    *,
    user_id: str | None,
    action: str,
    resource_type: str,
    resource_id: str,
    details: dict,
    request: Request | None = None,
) -> AuditLog:
    entry = AuditLog(
        user_id=user_id,
        action=action,
        resource_type=resource_type,
        resource_id=resource_id,
        details_json=details,
        ip_address=request.client.host if request and request.client else "",
    )
    session.add(entry)
    await session.commit()
    await session.refresh(entry)
    return entry


async def list_audit_logs(session: AsyncSession, user_id: str) -> list[AuditLog]:
    result = await session.execute(
        select(AuditLog).where(AuditLog.user_id == user_id).order_by(AuditLog.created_at.desc()).limit(200)
    )
    return list(result.scalars().all())
