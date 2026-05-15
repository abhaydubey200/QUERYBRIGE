
import asyncio
import psutil
import os
import logging
from app.connectors.connector_factory import ConnectorFactory
from app.connectors.base_connector import ConnectionConfig

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("memory_profile")

def get_memory_usage():
    process = psutil.Process(os.getpid())
    return process.memory_info().rss / 1024 / 1024 # MB

async def profile_streaming_memory():
    logger.info("🧠 Starting Memory Profiling for Large Stream...")
    
    config = {
        "type": "postgres",
        "host": "localhost",
        "port": 5432,
        "username": "admin",
        "password": "password123",
        "database": "querybridge"
    }
    
    conn_config = ConnectionConfig(**config)
    connector = ConnectorFactory.get_connector(conn_config)
    
    initial_mem = get_memory_usage()
    logger.info(f"Baseline Memory: {initial_mem:.2f} MB")
    
    # Simulate a massive stream (using generating query)
    query = "SELECT * FROM generate_series(1, 1000000) s(i)" 
    
    row_count = 0
    max_mem = initial_mem
    
    async for _ in connector.stream_query(query):
        row_count += 1
        if row_count % 100000 == 0:
            current_mem = get_memory_usage()
            max_mem = max(max_mem, current_mem)
            logger.info(f"Processing row {row_count}... Memory: {current_mem:.2f} MB")
            
    final_mem = get_memory_usage()
    logger.info(f"Final Memory: {final_mem:.2f} MB")
    logger.info(f"Peak Memory: {max_mem:.2f} MB")
    logger.info(f"Memory Delta: {final_mem - initial_mem:.2f} MB")
    
    leak_detected = (final_mem - initial_mem) > 10 # 10MB threshold
    
    logger.info("\n" + "="*50)
    logger.info("MEMORY SAFETY & PROFILING REPORT")
    logger.info("="*50)
    logger.info(f"Total Rows Streamed : {row_count}")
    logger.info(f"Peak RAM Usage      : {max_mem:.2f} MB")
    logger.info(f"Memory Stability    : {'STABLE' if not leak_detected else 'POTENTIAL LEAK'}")
    logger.info(f"Status              : {'CERTIFIED' if not leak_detected else 'ACTION REQUIRED'}")
    logger.info("="*50)

if __name__ == "__main__":
    asyncio.run(profile_streaming_memory())
