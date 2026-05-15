from fastapi import APIRouter, Depends, HTTPException
from typing import List
from app.models.models import SemanticMetric
from app.db.session import get_db
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.services.ai_service import AIService

router = APIRouter()

@router.get("/metrics", response_model=List[dict])
async def list_metrics(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(SemanticMetric))
    metrics = result.scalars().all()
    return [{"id": m.id, "name": m.name, "formula": m.formula, "description": m.description} for m in metrics]

@router.post("/resolve")
async def resolve_semantic_query(
    query: str, 
    connection_id: str,
    db: AsyncSession = Depends(get_db)
):
    from app.semantic.semantic_resolver import SemanticResolver
    # Initialize services with proper async sessions
    ai_service = AIService(db) 
    resolver = SemanticResolver(db, ai_service)
    
    result = await resolver.resolve_query(query, connection_id)
    return result

@router.get("/health")
async def semantic_health():
    return {"status": "healthy", "layer": "semantic", "engine": "activated"}
