from abc import ABC, abstractmethod
from typing import List, Dict, Any, AsyncGenerator

class QueryBridgeConnector(ABC):
    """
    Abstract Base Class for all QueryBridge database connectors.
    Plugins must inherit from this and implement the methods.
    """

    @abstractmethod
    async def connect(self, credentials: Dict[str, Any]):
        pass

    @abstractmethod
    async def execute_stream(self, sql: str) -> AsyncGenerator[List[Dict[str, Any]], None]:
        """Stream results in chunks of dictionaries."""
        pass

    @abstractmethod
    async def get_schema(self) -> Dict[str, Any]:
        """Return the database schema (tables, columns, types)."""
        pass

    @abstractmethod
    def validate_sql(self, sql: str) -> bool:
        """Validate SQL for syntax or security before execution."""
        pass
