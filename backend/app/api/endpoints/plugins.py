from fastapi import APIRouter, Depends
from app.models.models import Plugin
from app.db.session import get_db
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

router = APIRouter()

@router.get("/")
async def list_plugins(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Plugin))
    plugins = result.scalars().all()
    return plugins

@router.post("/{plugin_id}/toggle")
async def toggle_plugin(plugin_id: str, enabled: bool, db: AsyncSession = Depends(get_db)):
    # Logic to load/unload plugin from plugin_runtime
    return {"status": "updated", "plugin_id": plugin_id, "enabled": enabled}
