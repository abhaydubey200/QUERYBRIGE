import asyncio
import ssl
import time
from typing import Any, AsyncGenerator, Dict, List, Optional
import asyncpg
from app.connectors.base_connector import BaseConnector, ConnectionConfig, ConnectionResult, TableMetadata
from loguru import logger

class PostgresConnector(BaseConnector):
    def __init__(self, config: ConnectionConfig):
        super().__init__(config)
        self.pool: Optional[asyncpg.Pool] = None

    async def connect(self) -> None:
        if self.pool:
            return

        async with self._connect_lock:
            if self.pool:
                return

            try:
                ssl_ctx = self._get_ssl_context()
                self.pool = await asyncpg.create_pool(
                    user=self.config.username,
                    password=self.config.password,
                    database=self.config.database,
                    host=self.config.host,
                    port=self.config.port,
                    min_size=1,
                    max_size=self.config.pool_size,
                    command_timeout=self.config.timeout,
                    max_inactive_connection_lifetime=self.config.timeout,
                    ssl=ssl_ctx
                )
                logger.info(f"Postgres pool initialized for {self.config.host}:{self.config.port} [SSL: {self.config.ssl_mode}]")
            except Exception as e:
                logger.error(f"Failed to initialize Postgres pool: {str(e)}")
                raise

    def _get_ssl_context(self) -> Any:
        if self.config.ssl_mode == "disable":
            return None
        if self.config.ssl_mode == "prefer":
            return None # asyncpg handles 'prefer' via connection attempt

        ctx = ssl.create_default_context()
        ca_file = self.extra("ssl_ca") or self.extra("ssl_ca_file") or self.extra("ca_cert_path")
        ca_data = self.extra("ssl_ca_data") or self.extra("ca_cert")
        if ca_file or ca_data:
            ctx.load_verify_locations(cafile=ca_file, cadata=ca_data)

        if self.config.ssl_mode == "require":
            ctx.check_hostname = False
            ctx.verify_mode = ssl.CERT_NONE
        elif self.config.ssl_mode == "verify-ca":
            ctx.check_hostname = False
            ctx.verify_mode = ssl.CERT_REQUIRED
        elif self.config.ssl_mode == "verify-full":
            ctx.check_hostname = True
            ctx.verify_mode = ssl.CERT_REQUIRED
        return ctx

    async def disconnect(self) -> None:
        if self.pool:
            await self.pool.close()
            self.pool = None
            logger.info("Postgres pool closed")

    async def test_connection(self) -> ConnectionResult:
        start_time = time.perf_counter()
        conn = None
        try:
            ssl_ctx = self._get_ssl_context()
            conn = await asyncpg.connect(
                user=self.config.username,
                password=self.config.password,
                database=self.config.database,
                host=self.config.host,
                port=self.config.port,
                timeout=self.config.timeout,
                ssl=ssl_ctx
            )
            version = await conn.fetchval("SELECT version()")
            
            latency = (time.perf_counter() - start_time) * 1000
            return ConnectionResult(
                success=True,
                message="Connected successfully",
                latency_ms=round(latency, 2),
                server_version=version,
                diagnostics={
                    "dns_resolution": "Success", 
                    "tcp_port": "Open",
                    "ssl_active": ssl_ctx is not None
                }
            )
        except Exception as e:
            latency = (time.perf_counter() - start_time) * 1000
            logger.warning(f"Postgres test failed: {str(e)}")
            return ConnectionResult(
                success=False,
                message=str(e),
                latency_ms=round(latency, 2),
                diagnostics={"error_type": type(e).__name__}
            )
        finally:
            if conn:
                await conn.close()

    async def stream_query(self, query: str, params: Optional[Dict[str, Any]] = None) -> AsyncGenerator[Dict[str, Any], None]:
        if not self.pool:
            await self.connect()
        
        async with self.pool.acquire() as conn:
            async with conn.transaction():
                # asyncpg cursor uses positional arguments $1, $2, etc.
                # If params is a dict, we might need to map them or pass as args
                if params:
                    # Basic mapping for now, should be improved for complex queries
                    args = list(params.values())
                    async for record in conn.cursor(query, *args):
                        yield dict(record)
                else:
                    async for record in conn.cursor(query):
                        yield dict(record)

    async def get_schemas(self) -> List[str]:
        if not self.pool: await self.connect()
        async with self.pool.acquire() as conn:
            rows = await conn.fetch("""
                SELECT schema_name 
                FROM information_schema.schemata 
                WHERE schema_name NOT IN ('information_schema', 'pg_catalog')
            """)
            return [row['schema_name'] for row in rows]

    async def get_tables(self, schema: Optional[str] = None) -> List[TableMetadata]:
        if not self.pool: await self.connect()
        schema = schema or self.config.schema_name or 'public'
        async with self.pool.acquire() as conn:
            rows = await conn.fetch("""
                SELECT table_name, table_type
                FROM information_schema.tables 
                WHERE table_schema = $1
                ORDER BY table_type, table_name
                LIMIT $2
            """, schema, self.config.metadata_limit)
            
            tables = []
            for row in rows:
                tables.append(TableMetadata(
                    name=row['table_name'],
                    schema=schema,
                    type='view' if row['table_type'] == 'VIEW' else 'table'
                ))
            return tables

    async def get_columns(self, table_name: str, schema: Optional[str] = None) -> List[Dict[str, Any]]:
        if not self.pool: await self.connect()
        schema = schema or self.config.schema_name or 'public'
        async with self.pool.acquire() as conn:
            rows = await conn.fetch("""
                SELECT column_name, data_type, is_nullable, column_default
                FROM information_schema.columns
                WHERE table_schema = $1 AND table_name = $2
                ORDER BY ordinal_position
            """, schema, table_name)
            return [dict(row) for row in rows]

    async def get_server_info(self) -> Dict[str, Any]:
        if not self.pool: await self.connect()
        async with self.pool.acquire() as conn:
            version = await conn.fetchval("SELECT version()")
            settings = await conn.fetch("SELECT name, setting FROM pg_settings WHERE name IN ('max_connections', 'shared_buffers')")
            return {
                "version": version,
                "settings": {row['name']: row['setting'] for row in settings}
            }

    async def validate_credentials(self) -> bool:
        if not self.pool: await self.connect()
        try:
            async with self.pool.acquire() as conn:
                # Check if we can at least select from pg_catalog
                await conn.execute("SELECT 1 FROM pg_catalog.pg_class LIMIT 1")
                return True
        except Exception:
            return False

    def get_capabilities(self) -> Dict[str, bool]:
        return {
            "streaming": True,
            "metadata_discovery": True,
            "ssl": True,
            "async": True
        }
