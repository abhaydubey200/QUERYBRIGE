import asyncio
import time
from typing import Any, AsyncGenerator, Dict, List, Optional
import oracledb
from app.connectors.base_connector import BaseConnector, ConnectionConfig, ConnectionResult, TableMetadata
from loguru import logger

class OracleConnector(BaseConnector):
    def __init__(self, config: ConnectionConfig):
        super().__init__(config)
        self.pool: Optional[oracledb.AsyncPool] = None

    def _dsn(self) -> str:
        service_name = self.extra("service_name") or self.config.database
        sid = self.extra("sid")
        if sid:
            return oracledb.makedsn(self.config.host, self.config.port, sid=sid)
        return oracledb.makedsn(self.config.host, self.config.port, service_name=service_name)

    def _connect_kwargs(self) -> Dict[str, Any]:
        kwargs: Dict[str, Any] = {
            "user": self.config.username,
            "password": self.config.password,
            "dsn": self._dsn(),
        }
        if self.extra("wallet_location"):
            kwargs["config_dir"] = self.extra("wallet_location")
            kwargs["wallet_location"] = self.extra("wallet_location")
        if self.extra("wallet_password"):
            kwargs["wallet_password"] = self.extra("wallet_password")
        if self.config.ssl_mode in ("verify-ca", "verify-full"):
            kwargs["ssl_server_dn_match"] = self.config.ssl_mode == "verify-full"
        return kwargs

    async def connect(self) -> None:
        if self.pool:
            return

        async with self._connect_lock:
            if self.pool:
                return

            try:
                # Use python-oracledb Thin mode by default.
                self.pool = await oracledb.create_pool_async(
                    **self._connect_kwargs(),
                    min=1,
                    max=self.config.pool_size,
                    timeout=self.config.timeout
                )
                logger.info(f"Oracle pool initialized for {self.config.host}:{self.config.port}")
            except Exception as e:
                logger.error(f"Failed to initialize Oracle pool: {str(e)}")
                raise

    async def disconnect(self) -> None:
        if self.pool:
            await self.pool.close()
            self.pool = None
            logger.info("Oracle pool closed")

    async def test_connection(self) -> ConnectionResult:
        start_time = time.perf_counter()
        conn = None
        try:
            conn = await oracledb.connect_async(**self._connect_kwargs())
            version = conn.version
            
            latency = (time.perf_counter() - start_time) * 1000
            return ConnectionResult(
                success=True,
                message="Connected successfully",
                latency_ms=round(latency, 2),
                server_version=version,
                diagnostics={"mode": "Thin", "dns_resolution": "Success"}
            )
        except Exception as e:
            latency = (time.perf_counter() - start_time) * 1000
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
        if not self.pool: await self.connect()
        async with self.pool.acquire() as conn:
            async with conn.cursor() as cur:
                # Oracle uses :name for named parameters, which matches the dict keys
                await cur.execute(query, params or {})
                columns = [col[0] for col in cur.description]
                while True:
                    rows = await cur.fetchmany(100)
                    if not rows: break
                    for row in rows:
                        yield dict(zip(columns, row))

    async def get_schemas(self) -> List[str]:
        if not self.pool: await self.connect()
        async with self.pool.acquire() as conn:
            async with conn.cursor() as cur:
                # Exclude system schemas for enterprise clarity
                await cur.execute("""
                    SELECT username FROM all_users 
                    WHERE username NOT IN (
                        'SYS', 'SYSTEM', 'OUTLN', 'DBSNMP', 'APPQOSSYS', 'CTXSYS', 
                        'ORDSYS', 'ORDDATA', 'MDSYS', 'OLAPSYS', 'GGSYS', 'XDB', 
                        'WMSYS', 'OJVMSYS', 'CTXSYS', 'DVSYS', 'LBACSYS'
                    )
                    ORDER BY username
                """)
                rows = await cur.fetchall()
                return [row[0] for row in rows]

    async def get_tables(self, schema: Optional[str] = None) -> List[TableMetadata]:
        if not self.pool: await self.connect()
        owner = schema or self.config.username.upper()
        async with self.pool.acquire() as conn:
            async with conn.cursor() as cur:
                await cur.execute("""
                    SELECT table_name, 'TABLE' as type
                    FROM all_tables 
                    WHERE owner = :owner
                    UNION ALL
                    SELECT view_name, 'VIEW' as type
                    FROM all_views
                    WHERE owner = :owner
                    FETCH FIRST """ + str(self.config.metadata_limit) + """ ROWS ONLY
                """, owner=owner.upper())
                rows = await cur.fetchall()
                return [TableMetadata(name=r[0], schema=owner, type=r[1].lower()) for r in rows]

    async def get_columns(self, table_name: str, schema: Optional[str] = None) -> List[Dict[str, Any]]:
        if not self.pool: await self.connect()
        owner = schema or self.config.username.upper()
        async with self.pool.acquire() as conn:
            async with conn.cursor() as cur:
                await cur.execute("""
                    SELECT column_name, data_type, nullable, data_default
                    FROM all_tab_columns
                    WHERE owner = :owner AND table_name = :table_name
                    ORDER BY column_id
                """, owner=owner.upper(), table_name=table_name.upper())
                columns = [col[0] for col in cur.description]
                return [dict(zip(columns, row)) for row in await cur.fetchall()]

    async def get_server_info(self) -> Dict[str, Any]:
        if not self.pool: await self.connect()
        async with self.pool.acquire() as conn:
            async with conn.cursor() as cur:
                await cur.execute("SELECT * FROM v$version")
                version = await cur.fetchone()
                return {"version": version[0] if version else "Unknown"}

    async def validate_credentials(self) -> bool:
        try:
            conn = await oracledb.connect_async(**self._connect_kwargs())
            await conn.close()
            return True
        except Exception:
            return False

    def get_capabilities(self) -> Dict[str, bool]:
        return {
            "streaming": True,
            "metadata_discovery": True,
            "ssl": True,
            "async": True,
            "wallet_auth": True
        }
