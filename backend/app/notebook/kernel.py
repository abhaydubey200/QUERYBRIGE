from typing import Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from app.notebook_runtime.sandbox import NotebookSandbox
from app.connectors.connector_factory import ConnectorFactory
from loguru import logger

class NotebookKernel:
    """
    Orchestrates code execution within the QueryBridge notebook environment.
    Handles SQL, Python, and AI cell types.
    """
    
    def __init__(self, db: AsyncSession):
        self.db = db
        self.sandbox = NotebookSandbox(memory_limit_mb=512, timeout_seconds=30)

    async def execute(self, code: str, cell_type: str = "python", connection_id: str = None, context: Dict = None) -> Dict[str, Any]:
        """
        Executes code based on the cell type.
        """
        logger.info(f"Executing {cell_type} cell...")
        
        if cell_type == "python":
            return await self._execute_python(code, context)
        elif cell_type == "sql":
            if not connection_id:
                return {"status": "error", "error": "No connection selected for SQL execution"}
            return await self._execute_sql(code, connection_id)
        else:
            return {"status": "error", "error": f"Unsupported cell type: {cell_type}"}

    async def _execute_python(self, code: str, context: Dict = None) -> Dict[str, Any]:
        # Run in the sandbox
        # Non-blocking async wait for results
        result = await self.sandbox.run(code, context)
        return result

    async def _execute_sql(self, sql: str, connection_id: str) -> Dict[str, Any]:
        """
        Executes SQL via the standardized ConnectorFactory.
        """
        from app.services.connection_manager import ConnectionManager
        try:
            _, conn_config = await ConnectionManager._load_connection_config(self.db, connection_id)
            connector = ConnectorFactory.get_connector(conn_config)
            
            # Use streaming fetch for memory safety
            data = []
            async for row in connector.stream_query(sql):
                data.append(row)
                if len(data) >= 1000: # Kernel limit for notebook cells
                    break
            
            return {
                "status": "success",
                "data": data,
                "execution_time_ms": 0 # TODO: Track latency
            }
        except Exception as e:
            logger.error(f"SQL execution failed in kernel: {str(e)}")
            return {"status": "error", "error": str(e)}
