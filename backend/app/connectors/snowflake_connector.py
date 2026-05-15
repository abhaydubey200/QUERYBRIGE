import asyncio
import re
import time
from typing import Any, AsyncGenerator, Dict, List, Optional
import snowflake.connector
from app.connectors.base_connector import BaseConnector, ConnectionConfig, ConnectionResult, TableMetadata
from loguru import logger
from concurrent.futures import ThreadPoolExecutor

class SnowflakeConnector(BaseConnector):
    def __init__(self, config: ConnectionConfig):
        super().__init__(config)
        self._executor = ThreadPoolExecutor(max_workers=self.config.pool_size)
        self._closed = False

    def _get_connection(self):
        kwargs = dict(
            user=self.config.username,
            account=self.config.host,  # In Snowflake, 'host' usually refers to the account identifier
            warehouse=self.config.warehouse,
            database=self.config.database,
            schema=self.config.schema_name,
            role=self.config.role,
            login_timeout=self.config.timeout,
            ocsp_fail_open=bool(self.extra("ocsp_fail_open", False)),
            insecure_mode=False,
        )
        authenticator = self.extra("authenticator")
        if authenticator:
            kwargs["authenticator"] = authenticator
        if self.config.password and authenticator != "externalbrowser":
            kwargs["password"] = self.config.password
        return snowflake.connector.connect(**kwargs)

    @staticmethod
    def _quote_identifier(identifier: str) -> str:
        if not identifier:
            raise ValueError("Identifier is required")
        parts = [part.strip() for part in identifier.split(".") if part.strip()]
        if not parts:
            raise ValueError("Identifier is required")
        return ".".join(f'"{part.replace(chr(34), chr(34) + chr(34))}"' for part in parts)

    def _schema_ref(self, schema: Optional[str]) -> str:
        schema_name = schema or self.config.schema_name
        if not schema_name:
            raise ValueError("Snowflake schema is required for metadata discovery")
        if self.config.database and "." not in schema_name:
            return f"{self._quote_identifier(self.config.database)}.{self._quote_identifier(schema_name)}"
        return self._quote_identifier(schema_name)

    async def connect(self) -> None:
        if self._closed:
            self._executor = ThreadPoolExecutor(max_workers=self.config.pool_size)
            self._closed = False

    async def disconnect(self) -> None:
        if not self._closed:
            self._executor.shutdown(wait=False, cancel_futures=True)
            self._closed = True

    async def test_connection(self) -> ConnectionResult:
        start_time = time.perf_counter()
        try:
            await self.connect()
            loop = asyncio.get_running_loop()
            version = await loop.run_in_executor(self._executor, self._test_sync)
            
            latency = (time.perf_counter() - start_time) * 1000
            return ConnectionResult(
                success=True,
                message="Connected successfully",
                latency_ms=round(latency, 2),
                server_version=version,
                diagnostics={"account": self.config.host, "auth": "Password"}
            )
        except Exception as e:
            latency = (time.perf_counter() - start_time) * 1000
            return ConnectionResult(
                success=False,
                message=str(e),
                latency_ms=round(latency, 2),
                diagnostics={"error_type": type(e).__name__}
            )

    def _test_sync(self):
        with self._get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT CURRENT_VERSION()")
                return cur.fetchone()[0]

    async def stream_query(self, query: str, params: Optional[Dict[str, Any]] = None) -> AsyncGenerator[Dict[str, Any], None]:
        await self.connect()
        loop = asyncio.get_running_loop()
        
        def execute_and_fetch():
            conn = self._get_connection()
            cur = conn.cursor(snowflake.connector.DictCursor)
            try:
                cur.execute(query, params or {})
                while True:
                    rows = cur.fetchmany(100)
                    if not rows:
                        break
                    yield rows
            finally:
                cur.close()
                conn.close()

        def get_next_chunk(gen):
            try:
                return next(gen)
            except StopIteration:
                return None

        gen = execute_and_fetch()
        try:
            while True:
                chunk = await loop.run_in_executor(self._executor, get_next_chunk, gen)
                if chunk is None:
                    break
                for row in chunk:
                    yield row
                    await asyncio.sleep(0)
        finally:
            gen.close()

    async def get_schemas(self) -> List[str]:
        await self.connect()
        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(self._executor, self._get_schemas_sync)

    def _get_schemas_sync(self):
        with self._get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("SHOW SCHEMAS")
                return [row[1] for row in cur.fetchmany(self.config.metadata_limit)]

    async def get_tables(self, schema: Optional[str] = None) -> List[TableMetadata]:
        await self.connect()
        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(self._executor, self._get_tables_sync, schema)

    def _get_tables_sync(self, schema: Optional[str]):
        schema_ref = self._schema_ref(schema) if schema or self.config.schema_name else None
        tables: List[TableMetadata] = []
        with self._get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(f"SHOW TABLES IN SCHEMA {schema_ref}" if schema_ref else "SHOW TABLES")
                for row in cur.fetchmany(self.config.metadata_limit):
                    tables.append(TableMetadata(name=row[1], schema=row[3], type="table"))
                remaining = self.config.metadata_limit - len(tables)
                if remaining > 0:
                    cur.execute(f"SHOW VIEWS IN SCHEMA {schema_ref}" if schema_ref else "SHOW VIEWS")
                    for row in cur.fetchmany(remaining):
                        tables.append(TableMetadata(name=row[1], schema=row[3], type="view"))
        return tables

    async def get_columns(self, table_name: str, schema: Optional[str] = None) -> List[Dict[str, Any]]:
        await self.connect()
        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(self._executor, self._get_columns_sync, table_name, schema)

    def _get_columns_sync(self, table_name: str, schema: Optional[str]):
        table_ref = self._quote_identifier(table_name)
        schema_ref = self._schema_ref(schema) if schema or self.config.schema_name else None
        full_name = f"{schema_ref}.{table_ref}" if schema_ref else table_ref
        with self._get_connection() as conn:
            with conn.cursor(snowflake.connector.DictCursor) as cur:
                cur.execute(f"DESCRIBE TABLE {full_name}")
                return [dict(row) for row in cur.fetchall()]

    async def get_server_info(self) -> Dict[str, Any]:
        await self.connect()
        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(self._executor, self._get_server_info_sync)

    def _get_server_info_sync(self):
        with self._get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT CURRENT_REGION(), CURRENT_VERSION(), CURRENT_WAREHOUSE(), CURRENT_ROLE()")
                res = cur.fetchone()
                return {"region": res[0], "version": res[1], "warehouse": res[2], "role": res[3]}

    async def validate_credentials(self) -> bool:
        try:
            await self.connect()
            loop = asyncio.get_running_loop()
            await loop.run_in_executor(self._executor, self._test_sync)
            return True
        except Exception:
            return False

    def get_capabilities(self) -> Dict[str, bool]:
        return {
            "streaming": True,
            "metadata_discovery": True,
            "ssl": True,
            "async": False,
            "cloud_native": True
        }
