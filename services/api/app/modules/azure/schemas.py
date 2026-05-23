from pydantic import BaseModel


class ClusterDTO(BaseModel):
    id: str
    name: str
    resource_group: str
    subscription_id: str
    location: str
    kubernetes_version: str
    status: str
    failing_workloads: int
