from typing import List, Optional, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from app.models.catalog_models import CatalogTable, CatalogColumn, CatalogProfile, CatalogRelationship
from app.catalog.schema_discovery import SchemaDiscoveryEngine
from loguru import logger

class CatalogService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.discovery_engine = SchemaDiscoveryEngine(db)

    async def refresh_catalog(self, connection_id: str):
        """
        Triggers a full metadata refresh for a connection.
        """
        logger.info(f"Triggering catalog refresh for connection: {connection_id}")
        await self.discovery_engine.run_discovery(connection_id)
        return {"status": "success", "message": "Discovery job completed"}

    async def get_tables(self, connection_id: str, schema: Optional[str] = None):
        """
        Lists all tables in the catalog for a given connection.
        """
        query = select(CatalogTable).where(CatalogTable.connection_id == connection_id)
        if schema:
            query = query.where(CatalogTable.schema_name == schema)
        
        result = await self.db.execute(query)
        return result.scalars().all()

    async def get_table_details(self, table_id: str):
        """
        Returns full details for a table including columns and profiles.
        """
        from sqlalchemy.orm import selectinload
        query = select(CatalogTable).where(CatalogTable.id == table_id).options(
            selectinload(CatalogTable.columns),
            selectinload(CatalogTable.profiles)
        )
        
        result = await self.db.execute(query)
        table = result.scalar_one_or_none()
        
        if not table:
            return None
            
        return table

    async def search_catalog(self, query: str, connection_id: Optional[str] = None):
        """
        Global search across tables and columns.
        """
        # Search tables
        table_query = select(CatalogTable).where(CatalogTable.table_name.ilike(f"%{query}%"))
        if connection_id:
            table_query = table_query.where(CatalogTable.connection_id == connection_id)
        
        # Search columns
        column_query = select(CatalogColumn).where(CatalogColumn.name.ilike(f"%{query}%"))
        
        table_results = await self.db.execute(table_query)
        column_results = await self.db.execute(column_query)
        
        return {
            "tables": table_results.scalars().all(),
            "columns": column_results.scalars().all()
        }
