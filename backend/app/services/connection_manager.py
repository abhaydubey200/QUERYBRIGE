import asyncio
import datetime
import time
import uuid
from typing import Any, AsyncGenerator, Dict, List, Optional

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.models import DBConnection, Workspace
from app.connectors.connector_factory import ConnectorFactory
from app.connectors.base_connector import ConnectionConfig, ConnectionResult, TableMetadata
from app.security.encryption_service import encryption_service
from app.core.metrics import CONNECTION_LATENCY, QUERY_EXECUTION_DURATION
from loguru import logger

import enum


class ConnectionState(str, enum.Enum):
    INIT = "init"
    VALIDATING = "validating"
    CONNECTING = "connecting"
    CONNECTED = "connected"
    TESTING = "testing"
    DISCOVERING = "discovering"
    STREAMING = "streaming"
    FAILED = "failed"
    DISCONNECTED = "disconnected"
    TIMEOUT = "timeout"
    DESTROYED = "destroyed"
    ONLINE = "online"
    OFFLINE = "offline"
    DEGRADED = "degraded"


class ConnectionManager:
    @staticmethod
    def _advanced_settings(config: Dict[str, Any]) -> Dict[str, Any]:
        advanced = dict(config.get("advanced_settings") or config.get("extra_params") or {})
        for key in (
            "ssl_mode",
            "schema_name",
            "warehouse",
            "role",
            "auth_type",
            "service_name",
            "sid",
            "wallet_location",
            "wallet_password",
            "authenticator",
            "metadata_limit",
            "charset",
            "ssl_ca",
            "ssl_ca_data",
        ):
            if config.get(key) not in (None, ""):
                advanced[key] = config[key]
        return advanced

    @staticmethod
    def _config_from_payload(config: Dict[str, Any], conn_id: Optional[str] = None) -> ConnectionConfig:
        advanced = ConnectionManager._advanced_settings(config)
        return ConnectionConfig(
            id=conn_id or config.get("id"),
            name=config.get("name", "Connection"),
            type=config.get("db_type") or config.get("type") or config.get("engine"),
            host=config["host"],
            port=config.get("port"),
            database=config.get("database"),
            username=config.get("username") or "",
            password=config.get("password", ""),
            ssl_mode=advanced.get("ssl_mode", config.get("ssl_mode", "prefer")),
            schema_name=advanced.get("schema_name"),
            warehouse=advanced.get("warehouse"),
            role=advanced.get("role"),
            pool_size=int(config.get("pool_size") or (config.get("pool_settings") or {}).get("max_size", 10)),
            timeout=int(config.get("timeout") or (config.get("pool_settings") or {}).get("timeout", 30)),
            metadata_limit=int(advanced.get("metadata_limit", config.get("metadata_limit", 1000))),
            extra_params=advanced,
        )

    @staticmethod
    def _config_from_model(conn_model: DBConnection, password: str) -> ConnectionConfig:
        advanced = dict(conn_model.advanced_settings or {})
        pool_settings = conn_model.pool_settings or {}
        return ConnectionConfig(
            id=conn_model.id,
            name=conn_model.name,
            type=conn_model.db_type,
            host=conn_model.host,
            port=conn_model.port,
            database=conn_model.database,
            username=conn_model.username or "",
            password=password,
            ssl_mode=advanced.get("ssl_mode", "prefer"),
            schema_name=advanced.get("schema_name"),
            warehouse=advanced.get("warehouse"),
            role=advanced.get("role"),
            pool_size=int(pool_settings.get("max_size", 10)),
            timeout=int(pool_settings.get("timeout", 30)),
            metadata_limit=int(advanced.get("metadata_limit", 1000)),
            extra_params=advanced,
        )

    @staticmethod
    async def _load_connection_config(db: AsyncSession, conn_id: str) -> tuple:
        result = await db.execute(select(DBConnection).where(DBConnection.id == conn_id))
        conn_model = result.scalar_one_or_none()
        if not conn_model:
            raise ValueError("Connection not found")
        password = encryption_service.decrypt(conn_model.password_encrypted)
        return conn_model, ConnectionManager._config_from_model(conn_model, password)

    @staticmethod
    async def create_connection(db: AsyncSession, config: Dict[str, Any], user_id: Optional[str] = None) -> DBConnection:
        """Creates a new database connection with encrypted credentials."""
        password = config.get("password", "")
        encrypted_password = encryption_service.encrypt(password)
        conn_config = ConnectionManager._config_from_payload(config)
        advanced_settings = ConnectionManager._advanced_settings(config)

        # Ensure workspace exists
        workspace_id = config.get("workspace_id") or config.get("workspace")
        if not workspace_id:
            ws_result = await db.execute(select(Workspace))
            ws = ws_result.scalars().first()
            if not ws:
                ws = Workspace(id=str(uuid.uuid4()), name="Default Workspace", slug="default")
                db.add(ws)
                await db.flush()
            workspace_id = ws.id

        new_conn = DBConnection(
            id=str(uuid.uuid4()),
            workspace_id=workspace_id,
            name=config["name"],
            db_type=conn_config.type,
            host=config["host"],
            port=conn_config.port,
            database=config.get("database"),
            username=config.get("username"),
            password_encrypted=encrypted_password,
            is_active=True,
            status="unknown",
            advanced_settings=advanced_settings,
            pool_settings={
                "max_size": conn_config.pool_size,
                "timeout": conn_config.timeout,
            }
        )

        db.add(new_conn)
        await db.commit()
        await db.refresh(new_conn)

        logger.info(f"Connection Created: {new_conn.id} [{new_conn.db_type}]")
        return new_conn

    @staticmethod
    async def test_connection(config: Dict[str, Any]) -> ConnectionResult:
        """Tests a connection with timeout protection. No subprocess — simple and reliable."""
        start_time = time.perf_counter()
        trace_id = str(uuid.uuid4())

        try:
            conn_config = ConnectionManager._config_from_payload(config)
        except Exception as e:
            logger.error(f"[{trace_id}] Config validation failed: {str(e)}")
            return ConnectionResult(
                success=False,
                message=f"Invalid configuration: {str(e)}",
                latency_ms=(time.perf_counter() - start_time) * 1000,
                diagnostics={"trace_id": trace_id, "stage": "validation"}
            )

        try:
            logger.info(f"[{trace_id}] Testing {conn_config.type} -> {conn_config.host}")
            connector = ConnectorFactory.get_connector(conn_config)

            # Use asyncio.wait_for for timeout protection
            result = await asyncio.wait_for(
                connector.test_connection(),
                timeout=float(conn_config.timeout)
            )

            try:
                CONNECTION_LATENCY.labels(
                    connection_id="probe",
                    name=str(conn_config.name or "unknown"),
                    type=str(conn_config.type or "unknown")
                ).observe(float(result.latency_ms or 0) / 1000.0)
            except Exception:
                pass  # Never let metrics crash the request

            return result

        except asyncio.TimeoutError:
            logger.error(f"[{trace_id}] Connection test timed out after {conn_config.timeout}s")
            return ConnectionResult(
                success=False,
                message=f"Connection timed out after {conn_config.timeout}s",
                latency_ms=(time.perf_counter() - start_time) * 1000,
                diagnostics={"trace_id": trace_id, "stage": "timeout"}
            )
        except Exception as e:
            logger.error(f"[{trace_id}] Connection test failed: {str(e)}")
            return ConnectionResult(
                success=False,
                message=f"Driver error: {str(e)}",
                latency_ms=(time.perf_counter() - start_time) * 1000,
                diagnostics={
                    "trace_id": trace_id,
                    "stage": "driver",
                    "connector": conn_config.type,
                    "exception": type(e).__name__
                }
            )

    @staticmethod
    async def get_metadata(db: AsyncSession, conn_id: str) -> Dict[str, Any]:
        """Discovers database metadata with lifecycle tracking."""
        conn_model, conn_config = await ConnectionManager._load_connection_config(db, conn_id)
        connector = ConnectorFactory.get_connector(conn_config)
        trace_id = str(uuid.uuid4())

        try:
            schemas = await connector.get_schemas()

            default_schema = conn_config.schema_name
            target_schemas = [default_schema] if default_schema else schemas
            if not target_schemas:
                target_schemas = [None]

            tables: List[TableMetadata] = []
            truncated = False
            for schema in target_schemas:
                if len(tables) >= conn_config.metadata_limit:
                    truncated = True
                    break
                table_batch = await connector.get_tables(schema=schema)
                remaining = conn_config.metadata_limit - len(tables)
                tables.extend(table_batch[:remaining])
                if len(table_batch) > remaining:
                    truncated = True
                    break

            server_info = await connector.get_server_info()

            conn_model.last_heartbeat = datetime.datetime.utcnow()
            conn_model.status = ConnectionState.ONLINE
            await db.commit()

            return {
                "schemas": schemas,
                "tables": [t.model_dump() for t in tables],
                "server_info": server_info,
                "connection_id": conn_id,
                "selected_schema": default_schema,
                "truncated": truncated,
                "trace_id": trace_id
            }
        except Exception as e:
            logger.error(f"[{trace_id}] Metadata discovery failed: {str(e)}")
            conn_model.status = ConnectionState.DEGRADED
            await db.commit()
            raise

    @staticmethod
    async def run_health_check(db: AsyncSession, conn_id: str) -> Dict[str, Any]:
        try:
            conn_model, conn_config = await ConnectionManager._load_connection_config(db, conn_id)
        except ValueError:
            return {"success": False, "error": "Connection not found"}

        connector = ConnectorFactory.get_connector(conn_config)
        test_result = await connector.test_connection()

        conn_model.status = "online" if test_result.success else "offline"
        conn_model.last_heartbeat = datetime.datetime.utcnow()
        await db.commit()

        return {
            "connection_id": conn_id,
            "success": test_result.success,
            "latency_ms": test_result.latency_ms,
            "status": conn_model.status,
            "diagnostics": test_result.diagnostics
        }

    @staticmethod
    async def stream_query(
        db: AsyncSession,
        conn_id: str,
        query: str,
        params: Optional[Dict[str, Any]] = None,
        max_rows: int = 1000,
        timeout_seconds: int = 60,
    ) -> AsyncGenerator[Dict[str, Any], None]:
        if not query or not query.strip():
            raise ValueError("Query is required")
        if not ConnectionManager._is_read_only_query(query):
            raise ValueError("Only read-only queries are allowed")

        _, conn_config = await ConnectionManager._load_connection_config(db, conn_id)
        connector = ConnectorFactory.get_connector(conn_config)
        max_rows = max(1, min(int(max_rows), 100000))
        timeout_seconds = max(1, min(int(timeout_seconds), 600))

        start_time = time.perf_counter()
        count = 0
        deadline = time.perf_counter() + timeout_seconds
        try:
            async for row in connector.stream_query(query, params or {}):
                if time.perf_counter() > deadline:
                    raise TimeoutError(f"Query exceeded timeout of {timeout_seconds}s")
                yield row
                count += 1
                if count >= max_rows:
                    break
        finally:
            try:
                QUERY_EXECUTION_DURATION.labels(connection_id=conn_id).observe(time.perf_counter() - start_time)
            except Exception:
                pass

    @staticmethod
    async def execute_query(
        db: AsyncSession,
        conn_id: str,
        query: str,
        params: Optional[Dict[str, Any]] = None,
        max_rows: int = 1000,
        timeout_seconds: int = 60,
    ) -> Dict[str, Any]:
        rows = []
        async for row in ConnectionManager.stream_query(db, conn_id, query, params, max_rows, timeout_seconds):
            rows.append(row)
        return {"connection_id": conn_id, "rows": rows, "row_count": len(rows), "truncated": len(rows) >= max_rows}

    @staticmethod
    def _is_read_only_query(query: str) -> bool:
        normalized = query.lstrip().lower()
        return normalized.startswith(("select", "with", "show", "describe", "desc", "explain"))
