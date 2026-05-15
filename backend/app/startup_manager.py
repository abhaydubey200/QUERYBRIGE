import asyncio
import logging
from app.dependency_bootstrapper import DependencyBootstrapper
from app.runtime_health_manager import RuntimeHealthManager

logger = logging.getLogger(__name__)

class StartupManager:
    @staticmethod
    async def boot():
        logger.info("Initializing QueryBridge Enterprise Runtime...")
        
        health_manager = RuntimeHealthManager()
        if not await health_manager.check_dependencies():
            logger.critical("Dependency validation failed. Halting startup.")
            raise RuntimeError("Dependencies unavailable")
        
        bootstrapper = DependencyBootstrapper()
        await bootstrapper.initialize_all()
        logger.info("Startup complete. QueryBridge is fully operational.")
