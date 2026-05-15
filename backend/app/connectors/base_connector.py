import asyncio
import hashlib
import json
from abc import ABC, abstractmethod
from typing import Any, AsyncGenerator, Dict, List, Optional

from pydantic import AliasChoices, BaseModel, ConfigDict, Field, model_validator

class ConnectionConfig(BaseModel):
    model_config = ConfigDict(populate_by_name=True, extra="ignore")

    id: Optional[str] = None
    name: str = "Connection"
    type: str = Field(validation_alias=AliasChoices("type", "db_type", "engine"))
    host: str
    port: Optional[int] = None
    database: Optional[str] = None
    username: str = ""
    password: str = ""
    ssl_mode: str = "prefer"
    schema_name: Optional[str] = None
    warehouse: Optional[str] = None
    role: Optional[str] = None
    pool_size: int = 10
    timeout: int = 30
    metadata_limit: int = 1000
    extra_params: Dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="before")
    @classmethod
    def merge_advanced_settings(cls, values: Any) -> Any:
        if not isinstance(values, dict):
            return values

        merged = dict(values)
        advanced_settings = merged.get("advanced_settings") or {}
        extra_params = dict(merged.get("extra_params") or {})

        if isinstance(advanced_settings, dict):
            extra_params.update(advanced_settings)

        for key in (
            "ssl_mode",
            "schema_name",
            "warehouse",
            "role",
            "auth_type",
            "service_name",
            "sid",
            "metadata_limit",
        ):
            if key not in merged and key in extra_params:
                merged[key] = extra_params[key]

        merged["extra_params"] = extra_params
        return merged

    @model_validator(mode="after")
    def normalize(self) -> "ConnectionConfig":
        normalized = self.type.strip().lower()
        self.type = {
            "postgresql": "postgres",
            "sqlserver": "mssql",
            "sql_server": "mssql",
            "sql-server": "mssql",
        }.get(normalized, normalized)

        default_ports = {
            "postgres": 5432,
            "mysql": 3306,
            "mssql": 1433,
            "oracle": 1521,
            "snowflake": 443,
        }
        if self.port is None:
            self.port = default_ports.get(self.type)

        if not self.schema_name:
            self.schema_name = self.extra_params.get("schema_name")
        if not self.warehouse:
            self.warehouse = self.extra_params.get("warehouse")
        if not self.role:
            self.role = self.extra_params.get("role")

        self.ssl_mode = (self.ssl_mode or "prefer").strip().lower()
        self.pool_size = max(1, min(int(self.pool_size or 1), 50))
        self.timeout = max(1, min(int(self.timeout or 30), 300))
        self.metadata_limit = max(1, min(int(self.metadata_limit or 1000), 10000))
        return self

    def cache_signature(self) -> str:
        payload = self.model_dump(exclude={"password"}, mode="json")
        return hashlib.sha256(json.dumps(payload, sort_keys=True, default=str).encode()).hexdigest()

class TableMetadata(BaseModel):
    name: str
    schema: str
    type: str  # table, view
    columns: List[Dict[str, Any]] = Field(default_factory=list)
    row_count: Optional[int] = None

class ConnectionResult(BaseModel):
    success: bool
    message: str
    latency_ms: float
    server_version: Optional[str] = None
    diagnostics: Dict[str, Any] = {}

class BaseConnector(ABC):
    def __init__(self, config: ConnectionConfig):
        self.config = config
        self._connect_lock = asyncio.Lock()

    def extra(self, key: str, default: Any = None) -> Any:
        return self.config.extra_params.get(key, default)

    @abstractmethod
    async def connect(self) -> None:
        pass

    @abstractmethod
    async def disconnect(self) -> None:
        pass

    @abstractmethod
    async def test_connection(self) -> ConnectionResult:
        pass

    @abstractmethod
    async def stream_query(self, query: str, params: Optional[Dict[str, Any]] = None) -> AsyncGenerator[Dict[str, Any], None]:
        raise NotImplementedError

    @abstractmethod
    async def get_schemas(self) -> List[str]:
        pass

    @abstractmethod
    async def get_tables(self, schema: Optional[str] = None) -> List[TableMetadata]:
        pass

    @abstractmethod
    async def get_columns(self, table_name: str, schema: Optional[str] = None) -> List[Dict[str, Any]]:
        pass

    @abstractmethod
    async def get_server_info(self) -> Dict[str, Any]:
        pass

    @abstractmethod
    async def validate_credentials(self) -> bool:
        """Verify if the current credentials have sufficient permissions."""
        pass

    @abstractmethod
    def get_capabilities(self) -> Dict[str, bool]:
        """Return a mapping of supported features (e.g. streaming, metadata_discovery)."""
        pass
