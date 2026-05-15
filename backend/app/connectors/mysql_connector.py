import asyncio
import ssl
import time
from typing import Any, AsyncGenerator, Dict, List, Optional
import aiomysql
from app.connectors.base_connector import BaseConnector, ConnectionConfig, ConnectionResult, TableMetadata
from loguru import logger

class MySQLConnector(BaseConnector):
    def __init__(self, config: ConnectionConfig):
        super().__init__(config)
        self.pool: Optional[aiomysql.Pool] = None

    async def connect(self) -> None:
        if self.pool:
            return

        async with self._connect_lock:
            if self.pool:
                return

            try:
                ssl_ctx = self._get_ssl_context()
                self.pool = await aiomysql.create_pool(
                    host=self.config.host,
                    port=self.config.port,
                    user=self.config.username,
                    password=self.config.password,
                    db=self.config.database,
                    minsize=1,
                    maxsize=self.config.pool_size,
                    autocommit=True,
                    connect_timeout=self.config.timeout,
                    charset=self.extra("charset", "utf8mb4"),
                    ssl=ssl_ctx
                )
                logger.info(f"MySQL pool initialized for {self.config.host}:{self.config.port} [SSL: {self.config.ssl_mode}]")
            except Exception as e:
                logger.error(f"Failed to initialize MySQL pool: {str(e)}")
                raise

    def _get_ssl_context(self) -> Any:
        if self.config.ssl_mode == "disable":
            return None
        if self.config.ssl_mode == "prefer":
            return None

        ca_file = self.extra("ssl_ca") or self.extra("ssl_ca_file") or self.extra("ca_cert_path")
        ca_data = self.extra("ssl_ca_data") or self.extra("ca_cert")
        ctx = ssl.create_default_context(cafile=ca_file)
        if ca_data:
            ctx.load_verify_locations(cadata=ca_data)

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
            self.pool.close()
            await self.pool.wait_closed()
            self.pool = None
            logger.info("MySQL pool closed")

    async def test_connection(self) -> ConnectionResult:
        start_time = time.perf_counter()
        conn = None
        try:
            ssl_ctx = self._get_ssl_context()
            conn = await aiomysql.connect(
                host=self.config.host,
                port=self.config.port,
                user=self.config.username,
                password=self.config.password,
                db=self.config.database,
                connect_timeout=self.config.timeout,
                charset=self.extra("charset", "utf8mb4"),
                ssl=ssl_ctx
            )
            async with conn.cursor() as cur:
                await cur.execute("SELECT VERSION()")
                version = await cur.fetchone()
            
            latency = (time.perf_counter() - start_time) * 1000
            return ConnectionResult(
                success=True,
                message="Connected successfully",
                latency_ms=round(latency, 2),
                server_version=version[0] if version else "Unknown",
                diagnostics={
                    "dns_resolution": "Success", 
                    "tcp_port": "Open",
                    "ssl_active": ssl_ctx is not None
                }
            )
        except Exception as e:
            latency = (time.perf_counter() - start_time) * 1000
            logger.warning(f"MySQL test failed: {str(e)}")
            return ConnectionResult(
                success=False,
                message=str(e),
                latency_ms=round(latency, 2),
                diagnostics={"error_type": type(e).__name__}
            )
        finally:
            if conn:
                conn.close()

    async def stream_query(self, query: str, params: Optional[Dict[str, Any]] = None) -> AsyncGenerator[Dict[str, Any], None]:
        if not self.pool: await self.connect()
        async with self.pool.acquire() as conn:
            async with conn.cursor(aiomysql.DictCursor) as cur:
                # aiomysql execute takes params as a sequence or mapping
                await cur.execute(query, params)
                async for row in cur:
                    yield row

    async def get_schemas(self) -> List[str]:
        if not self.pool: await self.connect()
        async with self.pool.acquire() as conn:
            async with conn.cursor() as cur:
                await cur.execute("SHOW DATABASES")
                rows = await cur.fetchall()
                return [row[0] for row in rows if row[0] not in ('information_schema', 'mysql', 'performance_schema', 'sys')]

    async def get_tables(self, schema: Optional[str] = None) -> List[TableMetadata]:
        if not self.pool: await self.connect()
        db = schema or self.config.database
        async with self.pool.acquire() as conn:
            async with conn.cursor() as cur:
                await cur.execute("""
                    SELECT table_name, table_type
                    FROM information_schema.tables
                    WHERE table_schema = %s
                    ORDER BY table_type, table_name
                    LIMIT %s
                """, (db, self.config.metadata_limit))
                rows = await cur.fetchall()
                
                tables = []
                for row in rows:
                    tables.append(TableMetadata(
                        name=row[0],
                        schema=db,
                        type='view' if row[1] == 'VIEW' else 'table'
                    ))
                return tables

    async def get_columns(self, table_name: str, schema: Optional[str] = None) -> List[Dict[str, Any]]:
        if not self.pool: await self.connect()
        db = schema or self.config.database
        async with self.pool.acquire() as conn:
            async with conn.cursor(aiomysql.DictCursor) as cur:
                await cur.execute("""
                    SELECT column_name, column_type AS data_type, is_nullable, column_default
                    FROM information_schema.columns
                    WHERE table_schema = %s AND table_name = %s
                    ORDER BY ordinal_position
                """, (db, table_name))
                rows = await cur.fetchall()
                return [dict(row) for row in rows]

    async def get_server_info(self) -> Dict[str, Any]:
        if not self.pool: await self.connect()
        async with self.pool.acquire() as conn:
            async with conn.cursor() as cur:
                await cur.execute("SELECT VERSION()")
                version = await cur.fetchone()
                await cur.execute("SHOW VARIABLES LIKE 'max_connections'")
                max_conn = await cur.fetchone()
                return {
                    "version": version[0] if version else "Unknown",
                    "max_connections": max_conn[1] if max_conn else "Unknown"
                }

    async def validate_credentials(self) -> bool:
        if not self.pool: await self.connect()
        try:
            async with self.pool.acquire() as conn:
                async with conn.cursor() as cur:
                    # Check if we can see databases
                    await cur.execute("SHOW DATABASES")
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
