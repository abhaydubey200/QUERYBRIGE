
import asyncio
import logging
import os
import subprocess
import time
from typing import Any, Dict
from app.connectors.connector_factory import ConnectorFactory
from app.connectors.base_connector import ConnectionConfig

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("resilience_validation")

async def test_db_resilience(db_service: str, config: Dict[str, Any]):
    logger.info(f"🛡️ Testing resilience for {db_service}...")
    conn_config = ConnectionConfig(**config)
    connector = ConnectorFactory.get_connector(conn_config)
    
    # 1. Verify it's up
    res = await connector.test_connection()
    if not res.success:
        logger.error(f"❌ {db_service} is not up. Cannot run resilience test.")
        return False
        
    logger.info(f"✅ {db_service} is healthy. Simulating crash...")
    
    # 2. Kill the container
    subprocess.run(["docker", "stop", f"querybridge_{db_service}"], check=True)
    logger.info(f"🔥 {db_service} stopped. Verifying failure handling...")
    
    res = await connector.test_connection()
    if res.success:
        logger.error(f"❌ {db_service} still reports success after stop!")
        return False
    logger.info(f"✅ {db_service} correctly failed: {res.message}")
    
    # 3. Restart the container
    logger.info(f"🔄 Restarting {db_service}...")
    subprocess.run(["docker", "start", f"querybridge_{db_service}"], check=True)
    
    # 4. Wait for it to be ready and test reconnection
    max_retries = 10
    for i in range(max_retries):
        logger.info(f"⏳ Waiting for {db_service} recovery (Attempt {i+1}/{max_retries})...")
        await asyncio.sleep(5)
        res = await connector.test_connection()
        if res.success:
            logger.info(f"✅ {db_service} RECOVERED SUCCESSFULLY.")
            return True
            
    logger.error(f"❌ {db_service} FAILED TO RECOVER in time.")
    return False

async def main():
    pg_config = {
        "type": "postgres",
        "host": "localhost",
        "port": 5432,
        "username": "admin",
        "password": "password123",
        "database": "querybridge"
    }
    
    result = await test_db_resilience("db", pg_config) # 'db' is the container name prefix in setup_infra
    
    logger.info("\n" + "="*50)
    logger.info("RESILIENCE & FAILURE RECOVERY REPORT")
    logger.info("="*50)
    logger.info(f"Database Recovery : {'SUCCESS' if result else 'FAILURE'}")
    logger.info(f"Status            : {'CERTIFIED' if result else 'ACTION REQUIRED'}")
    logger.info("="*50)

if __name__ == "__main__":
    asyncio.run(main())
