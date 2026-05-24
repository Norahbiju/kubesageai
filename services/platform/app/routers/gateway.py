import asyncio
import json
from urllib.parse import urlencode

from fastapi import APIRouter, Depends, Request, Response
from fastapi.responses import RedirectResponse, StreamingResponse
from redis.asyncio import Redis
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.database import get_session
from app.core.errors import KubeSageError
from app.core.security import current_user
from app.models.entities import AuditLog, Cluster, Incident, RemediationAction, User
from app.schemas.dto import ApproveRemediationRequest
from app.services.ai_analysis import ai_service
from app.services.audit import audit, list_audit_logs
from app.services.auth import auth_service
from app.services.azure_integration import azure_service
from app.services.events import events
from app.services.kubernetes_integration import kubernetes_service
from app.services.remediation import remediation_service

router = APIRouter()
STATE_COOKIE = "kubesage_oauth_state"


@router.get("/auth/login")
async def login() -> RedirectResponse:
    state = auth_service.create_state()
    response = RedirectResponse(auth_service.login_url(state))
    response.set_cookie(STATE_COOKIE, state, max_age=600, httponly=True, samesite="lax")
    return response


@router.get("/auth/callback")
async def callback(
    request: Request,
    code: str | None = None,
    state: str | None = None,
    error: str | None = None,
    error_description: str | None = None,
    session: AsyncSession = Depends(get_session),
) -> RedirectResponse:
    if error:
        return RedirectResponse(f"{settings.frontend_url}/login?{urlencode({'error': error_description or error})}")
    if not code:
        raise KubeSageError("Azure callback did not include an authorization code", 400, "missing_auth_code")
    expected = request.cookies.get(STATE_COOKIE)
    if not expected or not state or expected != state:
        raise KubeSageError("Invalid Azure OAuth state", 400, "invalid_oauth_state")
    user, token = await auth_service.exchange_code(session, code)
    await audit(session, user_id=user.id, action="auth.login", resource_type="user", resource_id=user.id, details={}, request=request)
    response = RedirectResponse(f"{settings.frontend_url}/dashboard")
    response.delete_cookie(STATE_COOKIE)
    response.set_cookie(settings.session_cookie_name, token, max_age=settings.session_minutes * 60, httponly=True, samesite="lax")
    return response


@router.post("/auth/logout")
async def logout(response: Response) -> dict[str, str]:
    response.delete_cookie(settings.session_cookie_name)
    return {"status": "ok"}


@router.get("/auth/me")
async def me(user: User = Depends(current_user)) -> dict:
    return {"id": user.id, "email": user.email, "display_name": user.display_name, "tenant_id": user.tenant_id}


@router.get("/azure/subscriptions")
async def subscriptions(
    request: Request,
    user: User = Depends(current_user),
    session: AsyncSession = Depends(get_session),
) -> list[dict]:
    await events.publish(user.id, "azure.connection.started", {})
    items = await azure_service.list_subscriptions(session, user)
    await events.publish(user.id, "azure.subscriptions.loaded", {"count": len(items)})
    await audit(session, user_id=user.id, action="azure.subscriptions.list", resource_type="azure", resource_id=user.tenant_id, details={"count": len(items)}, request=request)
    return [item.model_dump() for item in items]


@router.get("/azure/subscriptions/{subscription_id}/clusters")
async def aks_clusters(
    subscription_id: str,
    request: Request,
    user: User = Depends(current_user),
    session: AsyncSession = Depends(get_session),
) -> list[dict]:
    items = await azure_service.list_aks_clusters(session, user, subscription_id)
    await events.publish(user.id, "azure.clusters.loaded", {"subscription_id": subscription_id, "count": len(items)})
    await audit(session, user_id=user.id, action="azure.aks.list", resource_type="subscription", resource_id=subscription_id, details={"count": len(items)}, request=request)
    return [item.model_dump() for item in items]


@router.get("/clusters")
async def clusters(user: User = Depends(current_user), session: AsyncSession = Depends(get_session)) -> list[dict]:
    result = await session.execute(select(Cluster).where(Cluster.user_id == user.id).order_by(Cluster.cluster_name))
    return [azure_service.to_dto(item).model_dump() for item in result.scalars().all()]


@router.get("/clusters/{cluster_id}")
async def cluster(cluster_id: str, user: User = Depends(current_user), session: AsyncSession = Depends(get_session)) -> dict:
    result = await session.execute(select(Cluster).where(Cluster.id == cluster_id, Cluster.user_id == user.id))
    item = result.scalar_one_or_none()
    if item is None:
        raise KubeSageError("Cluster not found", 404, "cluster_not_found")
    return azure_service.to_dto(item).model_dump()


@router.post("/clusters/{cluster_id}/scan")
async def scan_cluster(
    cluster_id: str,
    request: Request,
    user: User = Depends(current_user),
    session: AsyncSession = Depends(get_session),
) -> dict:
    await events.publish(user.id, "cluster.scan.started", {"cluster_id": cluster_id})
    incidents = await kubernetes_service.scan_cluster(session, user, cluster_id)
    for incident in incidents:
        await events.publish(user.id, "cluster.issue.detected", kubernetes_service.to_dto(incident).model_dump())
    await events.publish(user.id, "incident.created", {"count": len(incidents)})
    await audit(session, user_id=user.id, action="cluster.scan", resource_type="cluster", resource_id=cluster_id, details={"incidents": len(incidents)}, request=request)
    return {"incidents": [kubernetes_service.to_dto(item).model_dump() for item in incidents]}


@router.get("/incidents")
async def incidents(user: User = Depends(current_user), session: AsyncSession = Depends(get_session)) -> list[dict]:
    result = await session.execute(select(Incident).where(Incident.user_id == user.id).order_by(Incident.detected_at.desc()))
    return [kubernetes_service.to_dto(item).model_dump() for item in result.scalars().all()]


@router.get("/incidents/{incident_id}")
async def incident(incident_id: str, user: User = Depends(current_user), session: AsyncSession = Depends(get_session)) -> dict:
    item = await session.get(Incident, incident_id)
    if item is None or item.user_id != user.id:
        raise KubeSageError("Incident not found", 404, "incident_not_found")
    return kubernetes_service.to_dto(item).model_dump()


@router.post("/incidents/{incident_id}/analyze")
async def analyze_incident(
    incident_id: str,
    request: Request,
    user: User = Depends(current_user),
    session: AsyncSession = Depends(get_session),
) -> dict:
    await events.publish(user.id, "ai.analysis.started", {"incident_id": incident_id})
    result = await ai_service.analyze_incident(session, user, incident_id)
    await events.publish(user.id, "ai.analysis.completed", result.model_dump())
    await events.publish(user.id, "remediation.approval.required", {"incident_id": incident_id})
    await audit(session, user_id=user.id, action="ai.analysis.completed", resource_type="incident", resource_id=incident_id, details={"model": settings.openai_model}, request=request)
    return result.model_dump()


@router.post("/incidents/{incident_id}/remediations/{action_id}/approve")
async def approve_remediation(
    incident_id: str,
    action_id: str,
    payload: ApproveRemediationRequest,
    request: Request,
    user: User = Depends(current_user),
    session: AsyncSession = Depends(get_session),
) -> dict:
    action = await remediation_service.approve(session, user, incident_id, action_id, payload)
    await audit(session, user_id=user.id, action="remediation.approved", resource_type="remediation_action", resource_id=action.id, details=payload.model_dump(), request=request)
    return {"id": action.id, "approval_status": action.approval_status}


@router.post("/incidents/{incident_id}/remediations/{action_id}/execute")
async def execute_remediation(
    incident_id: str,
    action_id: str,
    request: Request,
    user: User = Depends(current_user),
    session: AsyncSession = Depends(get_session),
) -> dict:
    await events.publish(user.id, "remediation.started", {"incident_id": incident_id, "action_id": action_id})
    action = await remediation_service.execute(session, user, incident_id, action_id)
    await events.publish(user.id, "remediation.completed", {"action_id": action.id, "status": action.execution_status})
    await audit(session, user_id=user.id, action="remediation.executed", resource_type="remediation_action", resource_id=action.id, details={"result": action.execution_result}, request=request)
    return {"id": action.id, "execution_status": action.execution_status, "execution_result": action.execution_result}


@router.get("/stream/events")
async def stream_events(user: User = Depends(current_user)) -> StreamingResponse:
    redis = Redis.from_url(settings.redis_url, decode_responses=True)

    async def generator():
        pubsub = redis.pubsub()
        await pubsub.subscribe(f"events:{user.id}")
        try:
            while True:
                message = await pubsub.get_message(ignore_subscribe_messages=True, timeout=15)
                if message:
                    yield f"data: {message['data']}\n\n"
                else:
                    yield "event: heartbeat\ndata: {}\n\n"
                await asyncio.sleep(0.1)
        finally:
            await pubsub.unsubscribe(f"events:{user.id}")
            await pubsub.close()

    return StreamingResponse(generator(), media_type="text/event-stream")


@router.get("/audit-logs")
async def audit_logs(user: User = Depends(current_user), session: AsyncSession = Depends(get_session)) -> list[dict]:
    return [
        {
            "id": item.id,
            "user_id": item.user_id,
            "action": item.action,
            "resource_type": item.resource_type,
            "resource_id": item.resource_id,
            "details_json": item.details_json,
            "ip_address": item.ip_address,
            "created_at": item.created_at.isoformat(),
        }
        for item in await list_audit_logs(session, user.id)
    ]
