from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.azure.schemas import ClusterDTO
from app.modules.azure.service import AzureDiscoveryService
from app.shared.database import get_session

router = APIRouter()
service = AzureDiscoveryService()


@router.get("/clusters", response_model=list[ClusterDTO])
async def clusters(session: AsyncSession = Depends(get_session)) -> list[ClusterDTO]:
    discovered = await service.discover_clusters(session)
    return [ClusterDTO.model_validate(cluster, from_attributes=True) for cluster in discovered]
