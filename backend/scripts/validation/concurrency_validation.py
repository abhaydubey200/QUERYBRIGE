
import asyncio
import time
import logging
import random
from typing import Any, Dict
from app.connectors.connector_factory import ConnectorFactory
from app.connectors.base_connector import ConnectionConfig

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("concurrency_validation")

async def simulated_user_task(user_id: int, config: Dict[str, Any]):
    try:
        conn_config = ConnectionConfig(**config)
        connector = ConnectorFactory.get_connector(conn_config)
        
        # Test connection
        await connector.test_connection()
        
        # Simulate some work (random delay)
        await asyncio.sleep(random.uniform(0.1, 0.5))
        
        # Run a query
        query = "SELECT 1"
        async for _ in connector.stream_query(query):
            pass
            
        return True
    except Exception as e:
        logger.error(f"User {user_id} failed: {str(e)}")
        return False

async def run_load_test(concurrent_users: int, iterations: int):
    config = {
        "type": "postgres",
        "host": "localhost",
        "port": 5432,
        "username": "admin",
        "password": "password123",
        "database": "querybridge"
    }
    
    logger.info(f"🚀 Starting Load Test: {concurrent_users} users, {iterations} iterations...")
    start_time = time.perf_counter()
    
    tasks = []
    for i in range(concurrent_users):
        for _ in range(iterations):
            tasks.append(simulated_user_task(i, config))
            
    results = await asyncio.gather(*tasks)
    
    end_time = time.perf_counter()
    duration = end_time - start_time
    success_count = sum(1 for r in results if r)
    failure_count = len(results) - success_count
    
    logger.info("\n" + "="*50)
    logger.info("CONCURRENCY & LOAD TEST REPORT")
    logger.info("="*50)
    logger.info(f"Total Requests  : {len(results)}")
    logger.info(f"Successes       : {success_count}")
    logger.info(f"Failures        : {failure_count}")
    logger.info(f"Total Duration  : {duration:.2f}s")
    logger.info(f"Requests / Sec  : {len(results)/duration:.2f}")
    logger.info(f"Status          : {'CERTIFIED' if failure_count == 0 else 'ACTION REQUIRED'}")
    logger.info("="*50)

if __name__ == "__main__":
    asyncio.run(run_load_test(concurrent_users=50, iterations=10))
