from fastapi import APIRouter
from app.runtime_health.service_health import get_deep_health

router = APIRouter()

@router.get("/")
async def health_check():
    return {"status": "healthy"}

@router.get("/deep")
async def deep_health():
    return await get_deep_health()
