from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.incidents.models import Analysis, Incident
from app.modules.incidents.schemas import AnalysisDTO


class IncidentRepository:
    async def list_recent(self, session: AsyncSession) -> list[Incident]:
        result = await session.execute(select(Incident).order_by(desc(Incident.created_at)).limit(20))
        return list(result.scalars().all())

    async def create_with_analysis(
        self,
        session: AsyncSession,
        cluster_id: str,
        cluster_name: str,
        signals: dict,
        analysis: AnalysisDTO,
    ) -> Incident:
        incident = Incident(
            cluster_id=cluster_id,
            cluster_name=cluster_name,
            title=f"{analysis.severity.title()} incident in {cluster_name}",
            severity=analysis.severity,
            confidence_score=analysis.confidence_score,
            raw_signals=signals,
        )
        session.add(incident)
        await session.flush()
        session.add(Analysis(incident_id=incident.id, **analysis.model_dump()))
        await session.commit()
        await session.refresh(incident)
        return incident
