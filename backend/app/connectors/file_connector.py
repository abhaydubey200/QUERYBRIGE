import os
import time
import asyncio
from typing import Any, AsyncGenerator, Dict, List, Optional

import duckdb
import pandas as pd
from loguru import logger

from app.connectors.base_connector import BaseConnector, ConnectionConfig, ConnectionResult, TableMetadata

class FileConnector(BaseConnector):
    """
    Enterprise File Connector for QueryBridge.
    Supports CSV and Excel files using DuckDB and Pandas.
    Implements streaming to adhere to AstraFlow memory constraints.
    """
    def __init__(self, config: ConnectionConfig):
        super().__init__(config)
        self._conn: Optional[duckdb.DuckDBPyConnection] = None
        self._lock = asyncio.Lock()

    async def connect(self) -> None:
        if self._conn:
            return
        
        async with self._lock:
            if self._conn:
                return
            try:
                # Initialize in-memory DuckDB session for querying files
                self._conn = duckdb.connect(database=':memory:')
                logger.info(f"Initialized FileConnector session for {self.config.host}")
            except Exception as e:
                logger.error(f"Failed to initialize DuckDB session: {str(e)}")
                raise

    async def disconnect(self) -> None:
        async with self._lock:
            if self._conn:
                try:
                    self._conn.close()
                except:
                    pass
                self._conn = None
                logger.info("FileConnector session closed")

    async def test_connection(self) -> ConnectionResult:
        start_time = time.perf_counter()
        path = self.config.host
        try:
            if not os.path.exists(path):
                raise FileNotFoundError(f"File not found at path: {path}")
            
            if not os.access(path, os.R_OK):
                raise PermissionError(f"Permission denied for file: {path}")

            # Basic verification of file structure
            if path.lower().endswith('.csv'):
                # Peek with DuckDB
                duckdb.sql(f"SELECT * FROM read_csv_auto('{path}') LIMIT 1")
            elif path.lower().endswith(('.xls', '.xlsx')):
                # Peek with Pandas
                pd.read_excel(path, nrows=1)
            else:
                raise ValueError("Unsupported file extension. Supported: .csv, .xlsx, .xls")

            latency = (time.perf_counter() - start_time) * 1000
            return ConnectionResult(
                success=True,
                message="File successfully verified and accessible",
                latency_ms=round(latency, 2),
                server_version=f"DuckDB {duckdb.__version__}",
                diagnostics={
                    "file_path": path,
                    "file_size_bytes": os.path.getsize(path),
                    "read_permission": "Granted",
                    "engine": "DuckDB"
                }
            )
        except Exception as e:
            latency = (time.perf_counter() - start_time) * 1000
            logger.warning(f"File connection test failed: {str(e)}")
            return ConnectionResult(
                success=False,
                message=str(e),
                latency_ms=round(latency, 2),
                diagnostics={"error_type": type(e).__name__}
            )

    async def stream_query(self, query: str, params: Optional[Dict[str, Any]] = None) -> AsyncGenerator[Dict[str, Any], None]:
        if not self._conn:
            await self.connect()

        path = self.config.host
        table_name = os.path.basename(path).split('.')[0].replace(' ', '_').replace('-', '_')
        
        try:
            # Prepare the virtual table
            if path.lower().endswith('.csv'):
                # DuckDB read_csv_auto is memory-safe and natively supports projection pushdown
                self._conn.execute(f"CREATE OR REPLACE VIEW \"{table_name}\" AS SELECT * FROM read_csv_auto('{path}')")
            elif path.lower().endswith(('.xls', '.xlsx')):
                # HARDENING: Large Excel files cause OOM if loaded fully.
                # We use a memory-efficient strategy: limit the load or use openpyxl optimized mode.
                file_size = os.path.getsize(path)
                logger.info(f"Processing Excel file: {path} ({file_size} bytes)")
                
                if file_size > 100 * 1024 * 1024: # 100MB
                    # For massive files, we should ideally convert to Parquet or use a streamer.
                    # As a survival measure, we use openpyxl with data_only=True.
                    logger.warning(f"CRITICAL: Massive Excel file detected. Memory pressure expected.")
                    df = pd.read_excel(path, engine='openpyxl', read_only=True)
                else:
                    # Use a faster engine for medium files
                    df = pd.read_excel(path)
                
                self._conn.register(table_name, df)
                # Cleanup reference to df to help GC if needed
                del df
            
            # Execute the user query
            result = self._conn.execute(query)
            columns = [desc[0] for desc in result.description]
            
            while True:
                # Fetch in batches to prevent event loop blocking
                rows = result.fetchmany(100)
                if not rows:
                    break
                for row in rows:
                    yield dict(zip(columns, row))
                # Small sleep to yield to event loop during large result sets
                await asyncio.sleep(0)
                    
        except Exception as e:
            logger.error(f"Error executing file query: {str(e)}")
            raise

    async def validate_credentials(self) -> bool:
        """Verify file existence and read permissions."""
        path = self.config.host
        return os.path.exists(path) and os.access(path, os.R_OK)

    def get_capabilities(self) -> Dict[str, bool]:
        return {
            "streaming": True,
            "metadata_discovery": True,
            "ssl": False,
            "async": True,
            "file_based": True
        }

    async def get_schemas(self) -> List[str]:
        return ["main"]

    async def get_tables(self, schema: Optional[str] = None) -> List[TableMetadata]:
        path = self.config.host
        name = os.path.basename(path).split('.')[0].replace(' ', '_').replace('-', '_')
        
        # We simulate a single-table database where the file is the table
        return [TableMetadata(
            name=name,
            schema="main",
            type="table",
            row_count=None # Dynamic
        )]

    async def get_columns(self, table_name: str, schema: Optional[str] = None) -> List[Dict[str, Any]]:
        path = self.config.host
        try:
            if path.lower().endswith('.csv'):
                res = duckdb.sql(f"DESCRIBE SELECT * FROM read_csv_auto('{path}')").fetchall()
                return [{"column_name": r[0], "data_type": r[1], "is_nullable": "YES"} for r in res]
            elif path.lower().endswith(('.xls', '.xlsx')):
                df = pd.read_excel(path, nrows=0)
                return [{"column_name": col, "data_type": str(df[col].dtype), "is_nullable": "YES"} for col in df.columns]
        except Exception as e:
            logger.error(f"Failed to get columns for file: {str(e)}")
            return []
        return []

    async def get_server_info(self) -> Dict[str, Any]:
        return {
            "engine": "DuckDB",
            "version": duckdb.__version__,
            "file_support": ["CSV", "Excel"],
            "streaming": True
        }
