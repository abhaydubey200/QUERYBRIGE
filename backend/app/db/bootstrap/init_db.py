import logging
import asyncio

logger = logging.getLogger(__name__)

class DatabaseInitializer:
    @staticmethod
    async def run():
        logger.info("Running automated schema creation and Alembic migrations...")
        from alembic.config import Config
        from alembic import command
        import os
        
        # Initialize Alembic config
        alembic_cfg = Config("alembic.ini")
        
        # Run migrations to head
        logger.info("Upgrading database schema to latest version...")
        command.upgrade(alembic_cfg, "head")
        logger.info("Schema upgrade complete.")

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(DatabaseInitializer.run())
