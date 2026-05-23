import asyncio

from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.ai.service import AIAnalysisService
from app.modules.azure.service import AzureDiscoveryService
from app.modules.incidents.repository import IncidentRepository
from app.modules.incidents.schemas import IncidentDTO
from app.modules.incidents.service import IncidentService
from app.modules.kubernetes.service import KubernetesInvestigationService
from app.modules.streaming.sse import sse_event
from app.shared.database import get_session

router = APIRouter()
service = IncidentService()
repo = IncidentRepository()


@router.get("", response_model=list[IncidentDTO])
async def incidents(session: AsyncSession = Depends(get_session)) -> list[IncidentDTO]:
    await AzureDiscoveryService().discover_clusters(session)
    existing = await repo.list_recent(session)
    return [IncidentDTO.model_validate(incident, from_attributes=True) for incident in existing]


@router.get("/dashboard")
async def dashboard(session: AsyncSession = Depends(get_session)) -> dict:
    await AzureDiscoveryService().discover_clusters(session)
    return await service.dashboard(session)


@router.post("/analyze/{cluster_id}")
async def analyze(cluster_id: str, session: AsyncSession = Depends(get_session)) -> dict:
    incident, analysis = await service.analyze_cluster(session, cluster_id)
    return {"incident_id": incident.id, "analysis": analysis.model_dump()}


@router.get("/analyze/stream")
async def analyze_stream(cluster_id: str, session: AsyncSession = Depends(get_session)) -> StreamingResponse:
    async def event_generator():
        progress = [
            "Connecting to Azure...",
            "Fetching AKS clusters...",
            "Analyzing Kubernetes events...",
            "Detecting deployment failures...",
            "Generating AI remediation...",
            "Preparing incident timeline...",
        ]
        for message in progress:
            yield sse_event({"type": "progress", "message": message})
            await asyncio.sleep(0.35)

        failures = await KubernetesInvestigationService().collect_failures(cluster_id)
        ai = AIAnalysisService()
        analysis = await ai.analyze(failures)
        for chunk in f"{analysis.summary}\n{analysis.root_cause}\n".split(" "):
            yield sse_event({"type": "analysis_delta", "message": chunk + " "})
            await asyncio.sleep(0.08)
        await service.analyze_cluster(session, cluster_id)
        yield sse_event({"type": "analysis_complete", "analysis": analysis.model_dump()})

    return StreamingResponse(event_generator(), media_type="text/event-stream")
