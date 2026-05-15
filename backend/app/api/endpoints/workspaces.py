from fastapi import APIRouter, Depends
from app.models.models import Workspace
from app.db.session import get_db
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

router = APIRouter()

@router.get("/")
async def list_workspaces(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Workspace))
    workspaces = result.scalars().all()
    return workspaces

@router.get("/{workspace_id}/status")
async def workspace_health(workspace_id: str):
    return {"workspace_id": workspace_id, "isolation": "active", "storage": "healthy"}
