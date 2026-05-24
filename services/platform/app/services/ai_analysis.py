import json

from openai import AsyncOpenAI
from pydantic import ValidationError
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.errors import KubeSageError
from app.models.entities import AIAnalysis, Incident, IncidentSignal, RemediationAction, User
from app.schemas.dto import AIAnalysisResult


SYSTEM_PROMPT = """
You are KubeSage AI, an expert Azure AKS and Kubernetes SRE.
Analyze only the structured incident context provided.
Return only valid JSON matching the requested schema.
Do not invent resources, commands, or permissions.
All remediation suggestions must require approval and use one of:
restart_deployment, rollback_deployment, delete_failed_pod, scale_deployment, restart_ingress_controller.
Do not suggest arbitrary shell commands or kubectl command strings.
"""


class AIAnalysisService:
    def __init__(self) -> None:
        self.client = AsyncOpenAI(api_key=settings.openai_api_key, timeout=60, max_retries=2)

    async def analyze_incident(self, session: AsyncSession, user: User, incident_id: str) -> AIAnalysisResult:
        incident = await session.get(Incident, incident_id)
        if incident is None or incident.user_id != user.id:
            raise KubeSageError("Incident not found", 404, "incident_not_found")
        signals = (
            await session.execute(select(IncidentSignal).where(IncidentSignal.incident_id == incident_id))
        ).scalars().all()
        context = {
            "incident": {
                "namespace": incident.namespace,
                "workload_name": incident.workload_name,
                "workload_type": incident.workload_type,
                "issue_type": incident.issue_type,
                "severity_hint": incident.severity,
                "detected_at": incident.detected_at.isoformat(),
            },
            "signals": [
                {
                    "signal_type": signal.signal_type,
                    "source": signal.source,
                    "message": signal.message,
                    "raw_payload_json": signal.raw_payload_json,
                    "timestamp": signal.timestamp.isoformat(),
                }
                for signal in signals
            ],
        }
        result = await self._call_openai(context)
        analysis = AIAnalysis(
            incident_id=incident.id,
            summary=result.summary,
            root_cause=result.root_cause,
            severity=result.severity,
            confidence_score=result.confidence_score,
            affected_services_json=result.affected_services,
            remediation_json=[item.model_dump() for item in result.remediation],
            timeline_json=[item.model_dump() for item in result.timeline],
            model_used=settings.openai_model,
        )
        session.add(analysis)
        for suggestion in result.remediation:
            action = RemediationAction(
                incident_id=incident.id,
                user_id=user.id,
                action_type=suggestion.action_type,
                action_payload_json=suggestion.action_payload,
            )
            session.add(action)
            await session.flush()
            suggestion.action_id = action.id
        incident.status = "analysis_completed"
        await session.commit()
        return result

    async def _call_openai(self, context: dict) -> AIAnalysisResult:
        content = await self._completion(context)
        try:
            return AIAnalysisResult.model_validate_json(content)
        except ValidationError:
            correction = await self._completion(
                {
                    "invalid_json": content,
                    "instruction": "Return corrected JSON only matching the schema. No markdown.",
                    "original_context": context,
                }
            )
            try:
                return AIAnalysisResult.model_validate_json(correction)
            except ValidationError as exc:
                raise KubeSageError("OpenAI returned invalid structured analysis", 502, "invalid_ai_response") from exc

    async def _completion(self, payload: dict) -> str:
        try:
            response = await self.client.chat.completions.create(
                model=settings.openai_model,
                response_format={"type": "json_object"},
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": json.dumps(payload, default=str)},
                ],
            )
            return response.choices[0].message.content or "{}"
        except Exception as exc:
            raise KubeSageError("OpenAI analysis request failed", 502, "openai_request_failed") from exc


ai_service = AIAnalysisService()
