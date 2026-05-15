from fastapi import APIRouter, Depends, HTTPException
from typing import List, Optional
from app.models.models import NotebookSession
from app.db.session import get_db
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.notebook.kernel import NotebookKernel

router = APIRouter()

@router.get("/", response_model=List[dict])
async def list_notebooks(db: AsyncSession = Depends(get_db)):
    stmt = select(NotebookSession)
    result = await db.execute(stmt)
    notebooks = result.scalars().all()
    return [{"id": n.id, "name": n.name, "updated_at": n.updated_at} for n in notebooks]

@router.post("/execute/{notebook_id}")
async def execute_cell(
    notebook_id: str, 
    cell_id: str, 
    code: str, 
    cell_type: str = "python",
    connection_id: Optional[str] = None,
    db: AsyncSession = Depends(get_db)
):
    kernel = NotebookKernel(db)
    result = await kernel.execute(code, cell_type=cell_type, connection_id=connection_id)
    return {"status": "success", "result": result}

@router.get("/runtime/status")
async def runtime_status():
    return {
        "status": "ready", 
        "engine": "QueryBridge-Enterprise-Kernel",
        "capabilities": ["python", "sql", "ai_grounding"]
    }
