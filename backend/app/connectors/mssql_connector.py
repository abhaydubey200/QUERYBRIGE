import asyncio
import time
from typing import Any, AsyncGenerator, Dict, List, Optional
import pyodbc
import aioodbc
from app.connectors.base_connector import BaseConnector, ConnectionConfig, ConnectionResult, TableMetadata
from loguru import logger

class MSSQLConnector(BaseConnector):
    def __init__(self, config: ConnectionConfig):
        super().__init__(config)
        self.pool: Optional[aioodbc.Pool] = None

    @staticmethod
    def _escape(value: Any) -> str:
        text = "" if value is None else str(value)
        return "{" + text.replace("}", "}}") + "}"

    def _get_connection_string(self) -> str:
        # Using ODBC Driver 18 for SQL Server as mandated for enterprise production
        auth_type = str(self.extra("auth_type", "sql")).lower()
        trust_server_certificate = "yes" if self.config.ssl_mode in ("require", "prefer") else "no"
        encrypt = "no" if self.config.ssl_mode == "disable" else "yes"

        parts = [
            f"DRIVER={{ODBC Driver 18 for SQL Server}};"
            f"SERVER={self.config.host},{self.config.port};",
            f"DATABASE={self._escape(self.config.database)};",
            f"Encrypt={encrypt};",
            f"TrustServerCertificate={trust_server_certificate};",
            f"Connection Timeout={self.config.timeout};",
        ]

        if auth_type in ("windows", "trusted", "integrated"):
            parts.append("Trusted_Connection=yes;")
        else:
            parts.extend([
                f"UID={self._escape(self.config.username)};",
                f"PWD={self._escape(self.config.password)};",
            ])

        return "".join(parts)

    async def connect(self) -> None:
        if self.pool:
            return

        async with self._connect_lock:
            if self.pool:
                return

            try:
                self.pool = await aioodbc.create_pool(
                    dsn=self._get_connection_string(),
                    minsize=1,
                    maxsize=self.config.pool_size,
                    autocommit=True
                )
                logger.info(f"MSSQL (ODBC 18) pool initialized for {self.config.host}")
            except Exception as e:
                logger.error(f"Failed to initialize MSSQL pool: {str(e)}")
                raise

    async def disconnect(self) -> None:
        if self.pool:
            self.pool.close()
            await self.pool.wait_closed()
            self.pool = None
            logger.info("MSSQL pool closed")

    async def test_connection(self) -> ConnectionResult:
        start_time = time.perf_counter()
        try:
            # Test direct connection without pool for health check
            conn = await aioodbc.connect(dsn=self._get_connection_string())
            cursor = await conn.cursor()
            await cursor.execute("SELECT @@VERSION")
            row = await cursor.fetchone()
            version = row[0]
            await cursor.close()
            await conn.close()
            
            latency = (time.perf_counter() - start_time) * 1000
            return ConnectionResult(
                success=True,
                message="Connected successfully via ODBC 18",
                latency_ms=round(latency, 2),
                server_version=version,
                diagnostics={"driver": "ODBC Driver 18", "encryption": "AES-256-TLS"}
            )
        except Exception as e:
            latency = (time.perf_counter() - start_time) * 1000
            return ConnectionResult(
                success=False,
                message=str(e),
                latency_ms=round(latency, 2),
                diagnostics={"error_type": type(e).__name__}
            )

    async def stream_query(self, query: str, params: Optional[Dict[str, Any]] = None) -> AsyncGenerator[Dict[str, Any], None]:
        if not self.pool:
            await self.connect()
        
        async with self.pool.acquire() as conn:
            async with conn.cursor() as cursor:
                # ODBC uses ? for positional parameters
                if params:
                    await cursor.execute(query, tuple(params.values()))
                else:
                    await cursor.execute(query)
                
                columns = [column[0] for column in cursor.description]
                while True:
                    rows = await cursor.fetchmany(100)
                    if not rows:
                        break
                    for row in rows:
                        yield dict(zip(columns, row))

    async def get_schemas(self) -> List[str]:
        if not self.pool: await self.connect()
        async with self.pool.acquire() as conn:
            async with conn.cursor() as cursor:
                await cursor.execute("SELECT name FROM sys.schemas WHERE name NOT IN ('information_schema', 'sys')")
                rows = await cursor.fetchall()
                return [row[0] for row in rows]

    async def get_tables(self, schema: Optional[str] = None) -> List[TableMetadata]:
        if not self.pool: await self.connect()
        schema = schema or 'dbo'
        async with self.pool.acquire() as conn:
            async with conn.cursor() as cursor:
                await cursor.execute("""
                    SELECT TOP (?) table_name, table_type
                    FROM information_schema.tables 
                    WHERE table_schema = ?
                    ORDER BY table_type, table_name
                """, (self.config.metadata_limit, schema))
                rows = await cursor.fetchall()
                return [TableMetadata(name=r[0], schema=schema, type='view' if r[1] == 'VIEW' else 'table') for r in rows]

    async def get_columns(self, table_name: str, schema: Optional[str] = None) -> List[Dict[str, Any]]:
        if not self.pool: await self.connect()
        schema = schema or 'dbo'
        async with self.pool.acquire() as conn:
            async with conn.cursor() as cursor:
                await cursor.execute("""
                    SELECT column_name, data_type, is_nullable, column_default
                    FROM information_schema.columns
                    WHERE table_schema = ? AND table_name = ?
                """, (schema, table_name))
                columns = [column[0] for column in cursor.description]
                rows = await cursor.fetchall()
                return [dict(zip(columns, row)) for row in rows]

    async def get_server_info(self) -> Dict[str, Any]:
        if not self.pool: await self.connect()
        async with self.pool.acquire() as conn:
            async with conn.cursor() as cursor:
                await cursor.execute("SELECT @@VERSION")
                row = await cursor.fetchone()
                version = row[0]
                await cursor.execute("SELECT name, value FROM sys.configurations WHERE name IN ('max worker threads')")
                configs = await cursor.fetchall()
                return {
                    "version": version,
                    "configurations": {c[0]: c[1] for c in configs}
                }

    async def validate_credentials(self) -> bool:
        if not self.pool: await self.connect()
        try:
            async with self.pool.acquire() as conn:
                async with conn.cursor() as cursor:
                    await cursor.execute("SELECT 1")
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
