from typing import List, Dict, Any, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, or_, func
from app.models.catalog_models import CatalogTable, CatalogColumn
from loguru import logger

class MetadataSearch:
    """
    Ranked search engine for enterprise metadata.
    """
    
    def __init__(self, db: AsyncSession):
        self.db = db

    async def search(self, query: str, connection_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Performs a fuzzy search across tables and columns.
        """
        search_term = f"%{query}%"
        
        # 1. Table Search (Higher weight)
        table_stmt = select(CatalogTable).where(
            or_(
                CatalogTable.table_name.ilike(search_term),
                CatalogTable.description.ilike(search_term)
            )
        )
        if connection_id:
            table_stmt = table_stmt.where(CatalogTable.connection_id == connection_id)
            
        # 2. Column Search
        column_stmt = select(CatalogColumn, CatalogTable.table_name, CatalogTable.schema_name).join(
            CatalogTable, CatalogColumn.table_id == CatalogTable.id
        ).where(
            or_(
                CatalogColumn.name.ilike(search_term),
                CatalogColumn.description.ilike(search_term)
            )
        )
        if connection_id:
            column_stmt = column_stmt.where(CatalogTable.connection_id == connection_id)

        table_results = await self.db.execute(table_stmt)
        column_results = await self.db.execute(column_stmt)

        tables = table_results.scalars().all()
        columns = []
        for row in column_results:
            col = row[0]
            columns.append({
                "id": col.id,
                "name": col.name,
                "table_name": row[1],
                "schema_name": row[2],
                "data_type": col.data_type,
                "pii_tag": col.pii_tag
            })

        # 3. Ranking logic (Simple for now: exact match first)
        results = {
            "tables": self._rank_results(tables, query, "table_name"),
            "columns": self._rank_results(columns, query, "name")
        }
        
        return results

    def _rank_results(self, items: List[Any], query: str, field: str) -> List[Any]:
        """
        Ranks results based on match quality.
        """
        def get_score(item):
            name = getattr(item, field) if hasattr(item, field) else item.get(field, "")
            name = name.lower()
            query_lower = query.lower()
            
            if name == query_lower: return 100
            if name.startswith(query_lower): return 80
            if query_lower in name: return 50
            return 10

        return sorted(items, key=get_score, reverse=True)
