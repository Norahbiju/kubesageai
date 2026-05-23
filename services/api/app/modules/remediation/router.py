from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.remediation.schemas import RemediationApprovalRequest, RemediationResult
from app.modules.remediation.service import RemediationService
from app.shared.database import get_session

router = APIRouter()
service = RemediationService()


@router.post("/approve", response_model=RemediationResult)
async def approve(request: RemediationApprovalRequest, session: AsyncSession = Depends(get_session)) -> RemediationResult:
    return await service.approve_and_execute(session, request)
