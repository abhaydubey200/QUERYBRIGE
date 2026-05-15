import logging

logger = logging.getLogger(__name__)

class SystemDataSeeder:
    @staticmethod
    async def seed():
        logger.info("Seeding enterprise roles, workspace templates, and semantic models...")
        from app.db.bootstrap.seed_roles import RoleSeeder
        from app.db.bootstrap.seed_permissions import PermissionSeeder
        await RoleSeeder.seed()
        await PermissionSeeder.seed()
