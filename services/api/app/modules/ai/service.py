import json
from collections.abc import AsyncGenerator

from openai import AsyncOpenAI

from app.modules.incidents.schemas import AnalysisDTO
from app.modules.kubernetes.schemas import KubernetesFailure
from app.shared.config import settings


class AIAnalysisService:
    def __init__(self) -> None:
        self.client = AsyncOpenAI(api_key=settings.openai_api_key) if settings.openai_api_key else None

    async def analyze(self, failures: list[KubernetesFailure]) -> AnalysisDTO:
        if not self.client:
            return self._demo_analysis(failures)

        response = await self.client.chat.completions.create(
            model=settings.openai_model,
            response_format={"type": "json_object"},
            messages=[
                {"role": "system", "content": "You are KubeSage AI. Return strict JSON with summary, root_cause, severity, confidence_score, affected_services, remediation, timeline, recommended_action."},
                {"role": "user", "content": json.dumps([failure.model_dump(mode="json") for failure in failures])},
            ],
        )
        content = response.choices[0].message.content or "{}"
        return AnalysisDTO.model_validate_json(content)

    async def stream_analysis(self, failures: list[KubernetesFailure]) -> AsyncGenerator[str, None]:
        analysis = await self.analyze(failures)
        text = f"Summary: {analysis.summary}\nRoot cause: {analysis.root_cause}\nRecommended action: {analysis.recommended_action}\n"
        for token in text.split(" "):
            yield token + " "
        yield json.dumps(analysis.model_dump())

    def _demo_analysis(self, failures: list[KubernetesFailure]) -> AnalysisDTO:
        reasons = {failure.reason for failure in failures}
        affected = sorted({failure.service or failure.deployment or failure.pod_name for failure in failures})
        severity = "high" if "CrashLoopBackOff" in reasons or "IngressFailure" in reasons else "medium"
        return AnalysisDTO(
            summary="Multiple AKS workloads are failing, with checkout unavailable due to container startup failure and ingress degradation.",
            root_cause="The strongest signal is a CrashLoopBackOff in checkout-api caused by missing runtime configuration, compounded by an image pull failure in catalog-worker and ingress readiness failures.",
            severity=severity,
            confidence_score=88,
            affected_services=affected,
            remediation=[
                "rollout_restart_deployment for checkout-api after validating secret configuration",
                "rollout_undo_deployment for catalog-worker if the pushed image tag is invalid",
                "restart_ingress_controller if readiness failures persist after endpoints recover",
            ],
            timeline=[
                "Container startup validation failed in payments/checkout-api",
                "Pod restart count exceeded safe operating threshold",
                "Ingress reported unavailable upstream endpoints",
                "Catalog worker image pull failed for the latest release tag",
            ],
            recommended_action="rollout_restart_deployment",
        )
