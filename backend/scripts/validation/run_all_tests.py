
import asyncio
import logging
import sys
import os

# Add the backend path to sys.path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))

from scripts.validation.real_db_validation import main as run_db_tests
from scripts.validation.concurrency_validation import run_load_test
from scripts.validation.memory_validation import profile_streaming_memory
from scripts.validation.resilience_validation import main as run_resilience_tests

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("master_validation")

async def run_operational_certification():
    logger.info("🎬 Starting Master Operational Certification Suite...")
    
    # 1. Database Validation
    await run_db_tests()
    
    # 2. Concurrency Validation
    await run_load_test(concurrent_users=20, iterations=5)
    
    # 3. Memory Safety Validation
    await profile_streaming_memory()
    
    # 4. Resilience Validation (Note: Requires Docker access)
    try:
        await run_resilience_tests()
    except Exception as e:
        logger.warning(f"Resilience tests skipped or failed: {str(e)}")
        
    logger.info("🏁 Operational Certification Suite Completed.")

if __name__ == "__main__":
    asyncio.run(run_operational_certification())
