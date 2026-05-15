import logging

logger = logging.getLogger(__name__)

class RoleSeeder:
    @staticmethod
    async def seed():
        logger.info("Seeding Enterprise Roles: Admin, Analyst, Executive...")
        pass
