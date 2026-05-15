from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.db.session import get_db
from app.models.models import Dashboard
from pydantic import BaseModel
from typing import List, Dict, Any
import uuid

router = APIRouter()

class DashboardCreate(BaseModel):
    name: str
    config: Dict[str, Any]
    is_public: bool = False

class DashboardResponse(BaseModel):
    id: str
    name: str
    config: Dict[str, Any]
    is_public: bool

    class Config:
        from_attributes = True

@router.get("/", response_model=List[DashboardResponse])
async def list_dashboards(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Dashboard))
    return result.scalars().all()

@router.post("/", response_model=DashboardResponse)
async def create_dashboard(data: DashboardCreate, db: AsyncSession = Depends(get_db)):
    new_dash = Dashboard(
        id=str(uuid.uuid4()),
        name=data.name,
        config=data.config,
        is_public=data.is_public
    )
    db.add(new_dash)
    await db.flush()
    return new_dash

@router.get("/{dash_id}", response_model=DashboardResponse)
async def get_dashboard(dash_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Dashboard).where(Dashboard.id == dash_id))
    dash = result.scalar_one_or_none()
    if not dash:
        raise HTTPException(status_code=404, detail="Dashboard not found")
    return dash
