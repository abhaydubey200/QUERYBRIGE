import asyncio
from loguru import logger
from typing import List
from app.models.models import DBConnection
from app.db.session import SessionLocal
from sqlalchemy import select
from app.services.connection_manager import ConnectionManager

class ConnectionSupervisor:
    """
    Background worker to monitor database connection health and update statuses.
    """
    def __init__(self, interval: int = 300):
        self.interval = interval  # Default to 5 minutes for production stability

    async def start_monitoring(self):
        logger.info(f"Starting Connection Heartbeat Supervisor (Interval: {self.interval}s)...")
        while True:
            try:
                async with SessionLocal() as db:
                    result = await db.execute(select(DBConnection).where(DBConnection.is_active == True))
                    connections = result.scalars().all()
                    
                    for conn in connections:
                        try:
                            # Perform actual health check via the driver
                            logger.info(f"Supervisor: Validating health for {conn.name} [{conn.id}]")
                            status_report = await ConnectionManager.run_health_check(db, conn.id)
                            
                            if status_report["success"]:
                                logger.debug(f"Heartbeat OK: {conn.name} (Latency: {status_report['latency_ms']:.2f}ms)")
                            else:
                                logger.warning(f"Heartbeat FAILED: {conn.name} - Status: {status_report['status']}")
                        except Exception as conn_err:
                            logger.error(f"Failed to check connection {conn.id}: {str(conn_err)}")
                            
                await asyncio.sleep(self.interval)
            except Exception as e:
                logger.error(f"Supervisor Critical Error: {str(e)}")
                await asyncio.sleep(30) # Back off on critical failure

connection_supervisor = ConnectionSupervisor()
