from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.catalog_models import CatalogTable, CatalogColumn
from app.services.ai_service import AIService
from loguru import logger

class SchemaSummarizer:
    """
    AI-powered schema intelligence engine.
    Explains business meaning of technical database objects.
    """
    
    def __init__(self, db: AsyncSession):
        self.db = db
        self.ai_service = AIService()

    async def summarize_table(self, table_id: str, use_cache: bool = True) -> str:
        """
        Generates a business summary for a table based on its columns and samples.
        """
        from sqlalchemy.orm import selectinload
        stmt = select(CatalogTable).where(CatalogTable.id == str(table_id)).options(selectinload(CatalogTable.columns))
        result = await self.db.execute(stmt)
        table = result.scalar_one_or_none()
        
        if not table:
            return "Table not found"

        if use_cache and table.description:
            return table.description
        
        # Prepare context for AI
        column_info = [f"{c.name} ({c.data_type})" for c in table.columns]
        
        prompt = f"""
        You are an expert Data Architect. 
        Explain the business purpose of the table '{table.table_name}' in the schema '{table.schema_name}'.
        
        Columns:
        {', '.join(column_info)}
        
        Provide a concise 1-2 sentence business description. 
        Focus on what this data represents in a business context (e.g., 'Tracks customer order transactions').
        """
        
        summary = await self.ai_service.generate_text(prompt)
        
        # Update table description
        table.description = summary
        await self.db.commit()
        
        return summary

    async def summarize_column(self, column_id: str, use_cache: bool = True) -> str:
        """
        Generates a business summary for a specific column.
        """
        stmt = select(CatalogColumn).where(CatalogColumn.id == str(column_id))
        result = await self.db.execute(stmt)
        column = result.scalar_one_or_none()
        
        if not column:
            return "Column not found"

        if use_cache and column.description:
            return column.description

        prompt = f"""
        Explain the business meaning of the column '{column.name}' with data type '{column.data_type}'.
        Provide a concise 1-sentence business definition.
        """
        
        summary = await self.ai_service.generate_text(prompt)
        
        # Update column description
        column.description = summary
        await self.db.commit()
        
        return summary

    async def batch_summarize_tables(self, table_ids: List[str]) -> dict:
        """
        Batch summarize multiple tables.
        """
        results = {}
        for tid in table_ids:
            results[tid] = await self.summarize_table(tid)
        return results

    async def infer_business_entities(self, connection_id: str):
        """
        Identifies core business entities (Customer, Product, etc.) from the catalog.
        """
        stmt = select(CatalogTable).where(CatalogTable.connection_id == connection_id)
        result = await self.db.execute(stmt)
        tables = result.scalars().all()
        
        table_names = [t.table_name for t in tables]
        
        prompt = f"""
        Analyze these database table names and identify the core 'Business Entities' they represent.
        Group related tables under a single entity.
        
        Tables: {', '.join(table_names)}
        
        Return a JSON mapping like: {{"Customer": ["customers", "customer_addresses"], "Sales": ["orders", "order_items"]}}
        """
        
        # In a real implementation, we'd parse this JSON and save to a SemanticEntities table
        entities = await self.ai_service.generate_text(prompt)
        return entities
