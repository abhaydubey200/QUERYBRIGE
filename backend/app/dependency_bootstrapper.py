import logging
from app.db.bootstrap.init_db import DatabaseInitializer
from app.db.bootstrap.seed_system_data import SystemDataSeeder

logger = logging.getLogger(__name__)

class DependencyBootstrapper:
    async def initialize_all(self):
        logger.info("Bootstrapping dependencies...")
        await DatabaseInitializer.run()
        await SystemDataSeeder.seed()
        # Initialize Redis, AI clients, connectors
        logger.info("Dependencies bootstrapped.")
