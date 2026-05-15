import asyncio
import json
from typing import Dict, Any, Optional
from fastapi import APIRouter, Depends, WebSocket, WebSocketDisconnect
from sqlalchemy.ext.asyncio import AsyncSession
from loguru import logger
from app.db.session import get_db
from app.services.connection_manager import ConnectionManager as RuntimeConnectionManager
from app.governance.pii.pii_detector import PIIDetector

router = APIRouter()

class WebSocketManager:
    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}
        self.active_streams: Dict[str, asyncio.Task] = {}

    async def connect(self, client_id: str, websocket: WebSocket):
        await websocket.accept()
        self.active_connections[client_id] = websocket

    async def disconnect(self, client_id: str):
        self.active_connections.pop(client_id, None)
        task = self.active_streams.pop(client_id, None)
        if task and not task.done():
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                pass

    async def send_personal_message(self, client_id: str, message: Dict):
        websocket = self.active_connections.get(client_id)
        if websocket:
            try:
                await websocket.send_json(message)
            except Exception as e:
                logger.error(f"Failed to send WS message to {client_id}: {str(e)}")
                await self.disconnect(client_id)

manager = WebSocketManager()

@router.websocket("/{client_id}")
async def websocket_endpoint(websocket: WebSocket, client_id: str):
    await manager.connect(client_id, websocket)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        await manager.disconnect(client_id)

@router.websocket("/query/{connection_id}/{client_id}")
async def query_stream_endpoint(
    websocket: WebSocket,
    connection_id: str,
    client_id: str,
    db: AsyncSession = Depends(get_db),
):
    await manager.connect(client_id, websocket)
    detector = PIIDetector(db)

    async def stream_rows(payload: Dict):
        row_count = 0
        batch = []
        batch_size = 50 # Adaptive chunking
        
        try:
            await manager.send_personal_message(client_id, {"type": "stream_started", "connection_id": connection_id})
            
            async for row in RuntimeConnectionManager.stream_query(
                db,
                connection_id,
                payload.get("query", ""),
                payload.get("params") or {},
                int(payload.get("max_rows", 50000)),
                int(payload.get("timeout_seconds", 300)),
            ):
                row_count += 1
                
                # Apply Runtime Masking/Governance if enabled
                if payload.get("apply_masking", True):
                    # Simple masking logic: if key looks sensitive, redact
                    masked_row = {k: ("****" if detector.is_sensitive_key(k) else v) for k, v in row.items()}
                    batch.append(masked_row)
                else:
                    batch.append(row)

                if len(batch) >= batch_size:
                    await manager.send_personal_message(client_id, {"type": "batch", "rows": batch})
                    batch = []
                    # Basic backpressure: yield to event loop
                    await asyncio.sleep(0.01)
                    
                    # Scale batch size based on speed if needed
                    if row_count > 1000: batch_size = 500

            if batch:
                await manager.send_personal_message(client_id, {"type": "batch", "rows": batch})
                
            await manager.send_personal_message(client_id, {"type": "stream_completed", "rows": row_count})
        except asyncio.CancelledError:
            await manager.send_personal_message(client_id, {"type": "stream_cancelled", "rows": row_count})
        except Exception as e:
            logger.error(f"Stream error: {str(e)}")
            await manager.send_personal_message(client_id, {"type": "stream_error", "error": str(e)})

    try:
        while True:
            payload = await websocket.receive_json()
            action = payload.get("action", "query")
            existing = manager.active_streams.get(client_id)

            if action == "cancel":
                if existing and not existing.done():
                    existing.cancel()
                continue

            if action == "query":
                if existing and not existing.done():
                    existing.cancel()
                manager.active_streams[client_id] = asyncio.create_task(stream_rows(payload))
    except WebSocketDisconnect:
        await manager.disconnect(client_id)
