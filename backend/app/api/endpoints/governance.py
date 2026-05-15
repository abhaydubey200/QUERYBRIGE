from fastapi import APIRouter, Depends, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import get_db
from app.governance.pii.pii_detector import PIIDetector

router = APIRouter()

@router.post("/scan-pii/{connection_id}")
async def scan_pii(connection_id: str, background_tasks: BackgroundTasks, db: AsyncSession = Depends(get_db)):
    # In a real app, we'd get all columns for the connection and scan
    from sqlalchemy import select
    from app.models.catalog_models import CatalogTable, CatalogColumn
    
    stmt = select(CatalogColumn).join(CatalogTable).where(CatalogTable.connection_id == connection_id)
    result = await db.execute(stmt)
    columns = result.scalars().all()
    
    detector = PIIDetector(db)
    for col in columns:
        background_tasks.add_task(detector.scan_column, col.id)
        
    return {"message": f"PII scan started for {len(columns)} columns"}

@router.get("/sensitive-data")
async def get_sensitive_data(db: AsyncSession = Depends(get_db)):
    from app.models.catalog_models import CatalogColumn
    from sqlalchemy import select
    
    stmt = select(CatalogColumn).where(CatalogColumn.pii_tag.isnot(None))
    result = await db.execute(stmt)
    return result.scalars().all()
