from typing import Any, Dict, List, Optional
import json
import uuid
import traceback
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse, JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.db.session import get_db
from app.models.models import DBConnection
from app.services.connection_manager import ConnectionManager
from app.connectors.connector_factory import ConnectorFactory
from pydantic import BaseModel, Field
from loguru import logger

router = APIRouter()


class ConnectionCreate(BaseModel):
    name: str
    db_type: str
    host: str
    port: Optional[int] = None
    database: Optional[str] = None
    username: Optional[str] = ""
    password: Optional[str] = ""
    ssl_mode: str = "prefer"
    schema_name: Optional[str] = None
    warehouse: Optional[str] = None
    role: Optional[str] = None
    auth_type: Optional[str] = None
    service_name: Optional[str] = None
    sid: Optional[str] = None
    authenticator: Optional[str] = None
    metadata_limit: int = Field(default=1000, ge=1, le=10000)
    charset: Optional[str] = None
    ssl_ca: Optional[str] = None
    advanced_settings: Dict[str, Any] = Field(default_factory=dict)


class QueryRequest(BaseModel):
    query: str
    params: Dict[str, Any] = Field(default_factory=dict)
    max_rows: int = Field(default=1000, ge=1, le=100000)
    timeout_seconds: int = Field(default=60, ge=1, le=600)


# ═══════════════════════════════════════════════════════════════
# LIST all connections
# ═══════════════════════════════════════════════════════════════
@router.get("/")
async def list_connections(db: AsyncSession = Depends(get_db)):
    try:
        result = await db.execute(select(DBConnection))
        connections = result.scalars().all()

        # Manual dict projection — avoids MissingGreenlet from lazy relationships
        data = []
        for c in connections:
            data.append({
                "id": c.id,
                "name": c.name,
                "db_type": c.db_type,
                "host": c.host,
                "port": c.port,
                "database": c.database,
                "is_active": c.is_active,
                "status": c.status,
            })

        return {"success": True, "data": data, "error": None}
    except Exception as e:
        trace_id = str(uuid.uuid4())
        logger.error(f"[{trace_id}] list_connections failed: {str(e)}")
        return JSONResponse(
            status_code=500,
            content={
                "success": False, "data": None,
                "error": {"code": "DB_QUERY_ERROR", "message": str(e), "trace_id": trace_id}
            }
        )


# ═══════════════════════════════════════════════════════════════
# CREATE a connection
# ═══════════════════════════════════════════════════════════════
@router.post("/")
async def create_connection(data: ConnectionCreate, db: AsyncSession = Depends(get_db)):
    try:
        connection = await ConnectionManager.create_connection(db, data.model_dump())
        return {
            "success": True,
            "data": {
                "id": connection.id,
                "name": connection.name,
                "db_type": connection.db_type,
                "host": connection.host,
                "port": connection.port,
                "database": connection.database,
                "is_active": connection.is_active,
                "status": connection.status,
            },
            "error": None,
        }
    except Exception as e:
        trace_id = str(uuid.uuid4())
        logger.error(f"[{trace_id}] create_connection failed: {str(e)}")
        logger.error(traceback.format_exc())
        return JSONResponse(
            status_code=500,
            content={
                "success": False, "data": None,
                "error": {"code": "CONNECTION_CREATE_FAILED", "message": str(e), "trace_id": trace_id}
            }
        )


# ═══════════════════════════════════════════════════════════════
# TEST a connection (no DB session needed)
# ═══════════════════════════════════════════════════════════════
@router.post("/test")
async def test_connection(data: ConnectionCreate):
    trace_id = str(uuid.uuid4())
    try:
        result = await ConnectionManager.test_connection(data.model_dump())
        if not result.success:
            return {
                "success": False, "data": None,
                "error": {
                    "code": "CONNECTION_TEST_FAILED",
                    "message": result.message,
                    "trace_id": trace_id,
                    "details": result.diagnostics,
                }
            }
        return {
            "success": True,
            "data": {
                "latency_ms": result.latency_ms,
                "version": result.server_version,
                "diagnostics": result.diagnostics,
            },
            "error": None,
        }
    except Exception as e:
        logger.error(f"[{trace_id}] test_connection crashed: {str(e)}")
        logger.error(traceback.format_exc())
        return JSONResponse(
            status_code=500,
            content={
                "success": False, "data": None,
                "error": {"code": "RUNTIME_CRASH", "message": str(e), "trace_id": trace_id}
            }
        )


# ═══════════════════════════════════════════════════════════════
# GET metadata for a connection
# ═══════════════════════════════════════════════════════════════
@router.get("/{conn_id}/metadata")
async def get_metadata(conn_id: str, db: AsyncSession = Depends(get_db)):
    try:
        metadata = await ConnectionManager.get_metadata(db, conn_id)
        return {"success": True, "data": metadata, "error": None}
    except Exception as e:
        trace_id = str(uuid.uuid4())
        logger.error(f"[{trace_id}] get_metadata failed: {str(e)}")
        return JSONResponse(
            status_code=500,
            content={
                "success": False, "data": None,
                "error": {"code": "METADATA_FAILED", "message": str(e), "trace_id": trace_id}
            }
        )


# ═══════════════════════════════════════════════════════════════
# Health check for a specific connection
# ═══════════════════════════════════════════════════════════════
@router.get("/{conn_id}/health")
async def get_connection_health(conn_id: str, db: AsyncSession = Depends(get_db)):
    try:
        result = await ConnectionManager.run_health_check(db, conn_id)
        if not result.get("success") and result.get("error") == "Connection not found":
            return JSONResponse(status_code=404, content={"success": False, "data": None, "error": {"code": "NOT_FOUND", "message": "Connection not found"}})
        return {"success": True, "data": result, "error": None}
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"success": False, "data": None, "error": {"code": "HEALTH_CHECK_FAILED", "message": str(e)}}
        )


# ═══════════════════════════════════════════════════════════════
# Execute a query against a connection
# ═══════════════════════════════════════════════════════════════
@router.post("/{conn_id}/query")
async def execute_query(conn_id: str, data: QueryRequest, db: AsyncSession = Depends(get_db)):
    try:
        result = await ConnectionManager.execute_query(db, conn_id, data.query, data.params, data.max_rows, data.timeout_seconds)
        return {"success": True, "data": result, "error": None}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except TimeoutError as e:
        raise HTTPException(status_code=504, detail=str(e))
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"success": False, "data": None, "error": {"code": "QUERY_FAILED", "message": str(e)}}
        )


# ═══════════════════════════════════════════════════════════════
# Stream query results (NDJSON)
# ═══════════════════════════════════════════════════════════════
@router.post("/{conn_id}/stream")
async def stream_query(conn_id: str, data: QueryRequest, db: AsyncSession = Depends(get_db)):
    async def row_stream():
        try:
            async for row in ConnectionManager.stream_query(db, conn_id, data.query, data.params, data.max_rows, data.timeout_seconds):
                yield json.dumps(row, default=str) + "\n"
        except Exception as e:
            yield json.dumps({"success": False, "error": {"code": "STREAM_ERROR", "message": str(e)}}, default=str) + "\n"
    return StreamingResponse(row_stream(), media_type="application/x-ndjson")


# ═══════════════════════════════════════════════════════════════
# DELETE a connection
# ═══════════════════════════════════════════════════════════════
@router.delete("/{conn_id}")
async def delete_connection(conn_id: str, db: AsyncSession = Depends(get_db)):
    try:
        result = await db.execute(select(DBConnection).where(DBConnection.id == conn_id))
        conn = result.scalar_one_or_none()
        if not conn:
            return JSONResponse(status_code=404, content={"success": False, "data": None, "error": {"code": "NOT_FOUND", "message": "Connection not found"}})

        await db.delete(conn)
        await db.commit()

        try:
            await ConnectorFactory.remove(conn_id)
        except Exception:
            pass  # Pool cleanup is best-effort

        return {"success": True, "data": {"message": "Connection deleted"}, "error": None}
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"success": False, "data": None, "error": {"code": "DELETE_FAILED", "message": str(e)}}
        )
