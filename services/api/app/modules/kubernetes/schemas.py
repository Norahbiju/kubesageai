from datetime import datetime

from pydantic import BaseModel


class KubernetesFailure(BaseModel):
    pod_name: str
    namespace: str
    deployment: str | None = None
    service: str | None = None
    reason: str
    message: str
    timestamp: datetime
    restart_count: int = 0
    logs: list[str] = []
