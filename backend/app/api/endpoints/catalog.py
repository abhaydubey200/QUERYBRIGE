from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.db.session import get_db
from app.catalog.catalog_service import CatalogService
from app.profiling.table_profiler import TableProfiler
from app.profiling.data_quality_scorer import DataQualityScorer
from app.relationships.relationship_engine import RelationshipEngine
from app.governance.pii.pii_detector import PIIDetector
from app.models.catalog_models import (
    CatalogTable, MetadataAsset, MetadataTag, MetadataQualityScore, MetadataClassification
)
from typing import List, Optional, Dict, Any
from pydantic import BaseModel
import datetime

router = APIRouter()

# ============ REQUEST/RESPONSE MODELS ============

class RefreshRequest(BaseModel):
    connection_id: str

class UpdateTableMetadataRequest(BaseModel):
    description: Optional[str] = None
    owner: Optional[str] = None
    steward: Optional[str] = None
    contact_email: Optional[str] = None
    business_owner: Optional[str] = None
    sla_freshness_hours: Optional[int] = None

class TagRequest(BaseModel):
    tag_type: str  # domain, product, sensitivity, owner_team, etc.
    tag_value: str

class ClassificationRequest(BaseModel):
    sensitivity_level: str  # public, internal, confidential, restricted
    contains_pii: bool
    masking_enabled: Optional[bool] = False
    access_restricted: Optional[bool] = False
    allowed_roles: Optional[List[str]] = None

# ============ EXISTING ENDPOINTS ============

@router.post("/refresh")
async def refresh_catalog(request: RefreshRequest, background_tasks: BackgroundTasks, db: AsyncSession = Depends(get_db)):
    """Trigger full catalog refresh for a connection"""
    service = CatalogService(db)
    background_tasks.add_task(service.refresh_catalog, request.connection_id)
    return {"message": "Catalog refresh started in background"}

@router.get("/tables/{connection_id}")
async def get_tables(connection_id: str, schema: Optional[str] = None, db: AsyncSession = Depends(get_db)):
    """List all tables in a connection"""
    service = CatalogService(db)
    return await service.get_tables(connection_id, schema)

@router.get("/table/{table_id}")
async def get_table_details(table_id: str, db: AsyncSession = Depends(get_db)):
    """Get full details for a table including columns, relationships, quality scores"""
    service = CatalogService(db)
    details = await service.get_table_details(table_id)
    if not details:
        raise HTTPException(status_code=404, detail="Table not found")
    return details

@router.post("/profile/{table_id}")
async def profile_table(table_id: str, background_tasks: BackgroundTasks, db: AsyncSession = Depends(get_db)):
    """Start profiling job for a table"""
    profiler = TableProfiler(db)
    background_tasks.add_task(profiler.profile_table, table_id)
    return {"message": "Profiling job started in background"}

@router.post("/discover-relationships/{connection_id}")
async def discover_relationships(connection_id: str, background_tasks: BackgroundTasks, db: AsyncSession = Depends(get_db)):
    """Discover relationships between tables"""
    engine = RelationshipEngine(db)
    background_tasks.add_task(engine.discover_relationships, connection_id)
    return {"message": "Relationship discovery started in background"}

@router.get("/search")
async def search_catalog(query: str, connection_id: Optional[str] = None, db: AsyncSession = Depends(get_db)):
    """Search catalog for tables and columns"""
    service = CatalogService(db)
    return await service.search_catalog(query, connection_id)

# ============ NEW METADATA MANAGEMENT ENDPOINTS ============

@router.patch("/table/{table_id}/metadata")
async def update_table_metadata(
    table_id: str, 
    request: UpdateTableMetadataRequest,
    db: AsyncSession = Depends(get_db)
):
    """Update table metadata (owner, steward, SLA, description)"""
    # Get table
    stmt = select(CatalogTable).where(CatalogTable.id == table_id)
    result = await db.execute(stmt)
    table = result.scalar_one_or_none()
    
    if not table:
        raise HTTPException(status_code=404, detail="Table not found")
    
    # Update table description
    if request.description is not None:
        table.description = request.description
    
    # Get or create asset record
    stmt = select(MetadataAsset).where(MetadataAsset.table_id == table_id)
    result = await db.execute(stmt)
    asset = result.scalar_one_or_none()
    
    if not asset:
        asset = MetadataAsset(table_id=table_id)
        db.add(asset)
    
    # Update asset fields
    if request.owner is not None:
        asset.owner = request.owner
    if request.steward is not None:
        asset.steward = request.steward
    if request.contact_email is not None:
        asset.contact_email = request.contact_email
    if request.business_owner is not None:
        asset.business_owner = request.business_owner
    if request.sla_freshness_hours is not None:
        asset.sla_freshness_hours = request.sla_freshness_hours
    
    asset.updated_at = datetime.datetime.utcnow()
    
    await db.commit()
    return {"status": "success", "message": "Table metadata updated"}

@router.get("/table/{table_id}/quality")
async def get_table_quality(table_id: str, db: AsyncSession = Depends(get_db)):
    """Get quality scores for a table"""
    stmt = select(MetadataQualityScore).where(MetadataQualityScore.table_id == table_id)
    result = await db.execute(stmt)
    quality_score = result.scalar_one_or_none()
    
    if not quality_score:
        return {"status": "not_scored", "table_id": table_id}
    
    return {
        "table_id": table_id,
        "overall_quality_score": quality_score.overall_quality_score,
        "freshness_score": quality_score.freshness_score,
        "completeness_score": quality_score.completeness_score,
        "uniqueness_score": quality_score.uniqueness_score,
        "accuracy_score": quality_score.accuracy_score,
        "consistency_score": quality_score.consistency_score,
        "timeliness_score": quality_score.timeliness_score,
        "freshness_hours": quality_score.freshness_hours,
        "completeness_percent": quality_score.completeness_percent,
        "last_scored_at": quality_score.last_scored_at
    }

@router.post("/table/{table_id}/tag")
async def add_table_tag(
    table_id: str,
    request: TagRequest,
    db: AsyncSession = Depends(get_db)
):
    """Apply a tag to a table"""
    stmt = select(CatalogTable).where(CatalogTable.id == table_id)
    result = await db.execute(stmt)
    table = result.scalar_one_or_none()
    
    if not table:
        raise HTTPException(status_code=404, detail="Table not found")
    
    # Create tag
    tag = MetadataTag(
        table_id=table_id,
        tag_type=request.tag_type,
        tag_value=request.tag_value,
        created_by="api"
    )
    db.add(tag)
    await db.commit()
    
    return {"status": "success", "tag_id": tag.id, "message": "Tag applied"}

@router.get("/table/{table_id}/tags")
async def get_table_tags(table_id: str, db: AsyncSession = Depends(get_db)):
    """Get all tags for a table"""
    stmt = select(MetadataTag).where(MetadataTag.table_id == table_id)
    result = await db.execute(stmt)
    tags = result.scalars().all()
    
    return {
        "table_id": table_id,
        "tags": [
            {
                "id": tag.id,
                "type": tag.tag_type,
                "value": tag.tag_value,
                "created_by": tag.created_by,
                "created_at": tag.created_at
            }
            for tag in tags
        ]
    }

@router.post("/table/{table_id}/classify")
async def classify_table(
    table_id: str,
    request: ClassificationRequest,
    db: AsyncSession = Depends(get_db)
):
    """Classify a table for governance"""
    stmt = select(CatalogTable).where(CatalogTable.id == table_id)
    result = await db.execute(stmt)
    table = result.scalar_one_or_none()
    
    if not table:
        raise HTTPException(status_code=404, detail="Table not found")
    
    # Get or create classification
    stmt = select(MetadataClassification).where(MetadataClassification.table_id == table_id)
    result = await db.execute(stmt)
    classification = result.scalar_one_or_none()
    
    if not classification:
        classification = MetadataClassification(table_id=table_id)
        db.add(classification)
    
    # Update classification
    classification.sensitivity_level = request.sensitivity_level
    classification.contains_pii = request.contains_pii
    classification.masking_enabled = request.masking_enabled or False
    classification.access_restricted = request.access_restricted or False
    classification.allowed_roles = request.allowed_roles or []
    classification.classified_by = "api_manual"
    classification.auto_detected = False
    
    await db.commit()
    
    return {"status": "success", "message": "Table classified"}

@router.post("/scan-pii/{connection_id}")
async def scan_connection_for_pii(
    connection_id: str,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db)
):
    """Scan entire connection for PII"""
    pii_detector = PIIDetector(db)
    background_tasks.add_task(pii_detector.scan_connection, connection_id)
    return {"status": "started", "message": "PII scan started in background"}

@router.post("/score-quality/{connection_id}")
async def score_connection_quality(
    connection_id: str,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db)
):
    """Score data quality for entire connection"""
    scorer = DataQualityScorer(db)
    background_tasks.add_task(scorer.refresh_all_scores, connection_id)
    return {"status": "started", "message": "Quality scoring started in background"}

