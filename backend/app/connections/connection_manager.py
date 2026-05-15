from typing import Dict, List, Optional, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete
from app.models.models import DBConnection, AuditLog
from app.security.encryption_service import EncryptionService
from app.connectors.connector_factory import ConnectorFactory
from app.core.metrics import metrics_manager
from loguru import logger
import datetime
import uuid

class ConnectionManager:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.encryption = EncryptionService()

    async def create_connection(self, data: Dict[str, Any], user_id: str) -> DBConnection:
        """
        Creates a new database connection with encrypted credentials.
        """
        # Encrypt password
        if "password" in data:
            data["password_encrypted"] = self.encryption.encrypt(data.pop("password"))
        
        connection = DBConnection(**data)
        self.db.add(connection)
        
        # Audit log
        audit = AuditLog(
            user_id=user_id,
            action="CREATE_CONNECTION",
            resource_id=connection.id,
            metadata_={"name": connection.name, "type": connection.db_type}
        )
        self.db.add(audit)
        await self.db.flush()
        logger.info(f"Connection created: {connection.id} ({connection.name})")
        return connection

    async def test_connection(self, connection_id: str) -> Dict[str, Any]:
        """
        Tests a connection by attempting to connect and run a simple query.
        """
        result = await self.db.execute(select(DBConnection).where(DBConnection.id == connection_id))
        connection = result.scalar_one_or_none()
        
        if not connection:
            return {"success": False, "error": "Connection not found"}

        # Decrypt password for testing
        password = self.encryption.decrypt(connection.password_encrypted)
        
        config_params = {
            "host": connection.host,
            "port": connection.port,
            "database": connection.database,
            "username": connection.username,
            "password": password,
            "db_type": connection.db_type,
            "pool_size": 1,
            "timeout": 10,
            "ssl_mode": "require"
        }

        try:
            connector = ConnectorFactory.get_connector(connection.db_type, config_params)
            test_result = await connector.test_connection()
            
            # Update status
            connection.status = "online" if test_result.success else "offline"
            connection.last_heartbeat = datetime.datetime.utcnow()
            
            return {
                "success": test_result.success,
                "message": test_result.message,
                "latency_ms": test_result.latency_ms,
                "version": test_result.server_version,
                "diagnostics": test_result.diagnostics
            }
        except Exception as e:
            logger.error(f"Test connection failed for {connection_id}: {str(e)}")
            return {"success": False, "error": str(e)}

    async def get_metadata(self, connection_id: str) -> Dict[str, Any]:
        """
        Discovers database metadata (tables, views, etc.)
        """
        result = await self.db.execute(select(DBConnection).where(DBConnection.id == connection_id))
        connection = result.scalar_one_or_none()
        
        if not connection:
            raise ValueError("Connection not found")

        password = self.encryption.decrypt(connection.password_encrypted)
        config_params = {
            "host": connection.host,
            "port": connection.port,
            "database": connection.database,
            "username": connection.username,
            "password": password,
            "db_type": connection.db_type
        }

        connector = ConnectorFactory.get_connector(connection.db_type, config_params)
        schemas = await connector.get_schemas()
        return {"schemas": schemas}
