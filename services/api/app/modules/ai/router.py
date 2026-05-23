from fastapi import APIRouter

router = APIRouter()


@router.get("/models")
async def models() -> dict[str, list[str]]:
    return {"models": ["gpt-4.1-mini", "gpt-4.1"]}
