import time
from typing import Dict, Any, List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, text
from app.models.catalog_models import CatalogTable, CatalogColumn, CatalogProfile
from app.connectors.connector_factory import ConnectorFactory
from app.services.connection_manager import ConnectionManager
from loguru import logger
import datetime

class TableProfiler:
    """
    Enterprise table profiling engine.
    Calculates statistics without loading full datasets into memory.
    """
    
    def __init__(self, db: AsyncSession):
        self.db = db

    async def profile_table(self, table_id: str, sample_size: int = 10000):
        """
        Profiles a table by analyzing its columns.
        """
        # 1. Load table metadata
        from sqlalchemy.orm import selectinload
        stmt = select(CatalogTable).where(CatalogTable.id == table_id).options(selectinload(CatalogTable.columns))
        result = await self.db.execute(stmt)
        table = result.scalar_one_or_none()
        
        if not table:
            raise ValueError(f"Table {table_id} not found in catalog")

        # 2. Get connector
        _, conn_config = await ConnectionManager._load_connection_config(self.db, table.connection_id)
        connector = ConnectorFactory.get_connector(conn_config)

        logger.info(f"Profiling table: {table.schema_name}.{table.table_name}")

        # 3. Calculate Row Count (Fast)
        row_count = await self._get_row_count(connector, table.schema_name, table.table_name)
        table.row_count_estimate = row_count
        await self.db.commit()

        # 4. Profile each column
        for column in table.columns:
            await self._profile_column(connector, table, column, row_count, sample_size)

        table.last_metadata_sync = datetime.datetime.utcnow()
        await self.db.commit()

    async def _get_row_count(self, connector, schema: str, table: str) -> int:
        """
        Gets the row count for a table using count(*).
        """
        query = f"SELECT COUNT(*) FROM {schema}.{table}"
        # Note: In production, we'd use metadata-based counts if available for speed
        async for row in connector.stream_query(query, max_rows=1):
            return int(list(row.values())[0])
        return 0

    async def _profile_column(self, connector, table, column, total_rows: int, sample_size: int):
        """
        Profiles a single column.
        """
        logger.info(f"Profiling column: {column.name}")
        
        # We'll use a sample if the table is large
        use_sample = total_rows > sample_size
        table_ref = f"{table.schema_name}.{table.table_name}"
        
        # 1. Null count and distinct count
        stats_query = f"""
            SELECT 
                COUNT(*) as total,
                COUNT({column.name}) as non_null,
                COUNT(DISTINCT {column.name}) as distinct_vals
            FROM {table_ref}
        """
        if use_sample:
            # Different databases have different sampling syntax
            if connector.config.type == "postgres":
                stats_query += f" TABLESAMPLE SYSTEM ({(sample_size/total_rows)*100})"
            else:
                stats_query += f" LIMIT {sample_size}"

        stats = {"total": 0, "non_null": 0, "distinct_vals": 0}
        async for row in connector.stream_query(stats_query, max_rows=1):
            stats = row
            break

        null_count = stats.get("total", 0) - stats.get("non_null", 0)
        
        # 2. Top Values
        top_values_query = f"""
            SELECT {column.name} as value, COUNT(*) as count
            FROM {table_ref}
            WHERE {column.name} IS NOT NULL
            GROUP BY 1
            ORDER BY 2 DESC
            LIMIT 10
        """
        top_values = []
        async for row in connector.stream_query(top_values_query, max_rows=10):
            top_values.append(row)

        # 3. Save Profile
        # Check if profile already exists
        stmt = select(CatalogProfile).where(CatalogProfile.column_id == column.id)
        res = await self.db.execute(stmt)
        profile = res.scalar_one_or_none()
        
        if not profile:
            profile = CatalogProfile(table_id=table.id, column_id=column.id)
            self.db.add(profile)

        profile.null_count = null_count
        profile.distinct_count = stats.get("distinct_vals", 0)
        profile.top_values = top_values
        profile.cardinality = (stats.get("distinct_vals", 0) / stats.get("total", 1)) if stats.get("total", 0) > 0 else 0
        profile.last_profiled = datetime.datetime.utcnow()
        
        await self.db.flush()
