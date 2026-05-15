import asyncio
from threading import RLock
from typing import Dict, Type

from loguru import logger
from app.connectors.base_connector import BaseConnector, ConnectionConfig
from app.connectors.postgres_connector import PostgresConnector
from app.connectors.mysql_connector import MySQLConnector
from app.connectors.mssql_connector import MSSQLConnector
from app.connectors.oracle_connector import OracleConnector
from app.connectors.snowflake_connector import SnowflakeConnector
from app.connectors.file_connector import FileConnector

class ConnectorFactory:
    _connectors: Dict[str, Type[BaseConnector]] = {
        "postgres": PostgresConnector,
        "postgresql": PostgresConnector,
        "mysql": MySQLConnector,
        "mssql": MSSQLConnector,
        "sqlserver": MSSQLConnector,
        "oracle": OracleConnector,
        "snowflake": SnowflakeConnector,
        "csv": FileConnector,
        "excel": FileConnector,
        "file": FileConnector
    }
    
    # Cache for active connector instances to reuse internal pools
    _instance_cache: Dict[str, BaseConnector] = {}
    _cache_signatures: Dict[str, str] = {}
    _cache_lock = RLock()

    @classmethod
    def get_connector(cls, config: ConnectionConfig) -> BaseConnector:
        # Use connection ID if available, otherwise fallback to a hash of the config
        cache_key = config.id or f"{config.type}:{config.host}:{config.port}:{config.database}:{config.username}"
        signature = config.cache_signature()

        with cls._cache_lock:
            cached = cls._instance_cache.get(cache_key)
            if cached and cls._cache_signatures.get(cache_key) == signature:
                return cached

            if cached:
                logger.warning(f"Connector config changed for {cache_key}; replacing cached instance")
                cls._schedule_disconnect(cached)
                cls._instance_cache.pop(cache_key, None)
                cls._cache_signatures.pop(cache_key, None)
            
            connector_class = cls._connectors.get(config.type.lower())
            if not connector_class:
                raise ValueError(f"Unsupported connector type: {config.type}")

            instance = connector_class(config)
            if config.id:
                cls._instance_cache[cache_key] = instance
                cls._cache_signatures[cache_key] = signature
            return instance

    @classmethod
    def _schedule_disconnect(cls, connector: BaseConnector) -> None:
        try:
            loop = asyncio.get_running_loop()
            loop.create_task(connector.disconnect())
        except RuntimeError:
            logger.debug("No running event loop available for connector eviction cleanup")

    @classmethod
    async def cleanup(cls):
        """Shutdown all active connector pools during application shutdown."""
        with cls._cache_lock:
            cached_connectors = list(cls._instance_cache.items())
            cls._instance_cache.clear()
            cls._cache_signatures.clear()

        for conn_id, connector in cached_connectors:
            try:
                await connector.disconnect()
            except Exception as e:
                logger.error(f"Failed to cleanup connector {conn_id}: {str(e)}")

    @classmethod
    async def remove(cls, conn_id: str):
        """Remove a single cached connector and close its pool."""
        with cls._cache_lock:
            connector = cls._instance_cache.pop(conn_id, None)
            cls._cache_signatures.pop(conn_id, None)

        if connector:
            await connector.disconnect()

    @classmethod
    def register_connector(cls, type_name: str, connector_class: Type[BaseConnector]):
        cls._connectors[type_name.lower()] = connector_class
