from typing import Dict, List, Any, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.models import DBConnection, ConnectionHealthLog, ConnectionMetric
from app.services.connection_manager import ConnectionManager
from app.core.metrics import CONNECTION_HEALTH, CONNECTION_LATENCY
from loguru import logger
import asyncio
import datetime
import time

class HealthService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.manager = ConnectionManager()

    async def check_all_connections(self):
        """
        Background task to verify health of all registered connections.
        """
        result = await self.db.execute(select(DBConnection))
        connections = result.scalars().all()
        
        for conn in connections:
            start_time = time.time()
            is_healthy = await self.manager.test_connection(conn)
            latency = time.time() - start_time
            
            # Update metrics
            CONNECTION_HEALTH.labels(
                connection_id=str(conn.id),
                name=conn.name,
                type=conn.type
            ).inc(1 if is_healthy else 0)
            
            CONNECTION_LATENCY.labels(
                connection_id=str(conn.id),
                name=conn.name,
                type=conn.type
            ).observe(latency)
            
            # Log to database
            health_log = ConnectionHealthLog(
                connection_id=conn.id,
                status="healthy" if is_healthy else "unhealthy",
                latency_ms=latency * 1000,
                error_message=None if is_healthy else "Connection failed"
            )
            self.db.add(health_log)
        
        await self.db.commit()
        logger.info(f"Completed health check for {len(connections)} connections")
