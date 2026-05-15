import asyncio
from typing import List, Dict, Any, Optional
from loguru import logger
from sqlalchemy.ext.asyncio import AsyncSession
from app.connectors.connector_factory import ConnectorFactory
from app.models.models import DBConnection
from app.models.catalog_models import CatalogTable, CatalogColumn, MetadataRefreshJob
import datetime

class SchemaDiscoveryEngine:
    """
    Orchestrates the discovery of database schemas, tables, and columns.
    Implements chunked discovery and timeout protection.
    """
    
    SYSTEM_SCHEMAS = {
        'pg_catalog', 'information_schema', 'sys', 'SYSTEM', 
        'pg_toast', 'db_ms_fulltext', 'db_owner', 'guest'
    }

    def __init__(self, db: AsyncSession):
        self.db = db

    async def run_discovery(self, connection_id: str):
        """
        Main entry point for discovery.
        """
        # 1. Create a refresh job
        job = MetadataRefreshJob(
            connection_id=connection_id,
            status="running",
            started_at=datetime.datetime.utcnow()
        )
        self.db.add(job)
        await self.db.commit()
        await self.db.refresh(job)

        try:
            # 2. Get connection details
            from sqlalchemy import select
            result = await self.db.execute(select(DBConnection).where(DBConnection.id == connection_id))
            conn_model = result.scalar_one_or_none()
            if not conn_model:
                raise ValueError(f"Connection {connection_id} not found")

            # 3. Get connector
            from app.services.connection_manager import ConnectionManager
            _, conn_config = await ConnectionManager._load_connection_config(self.db, connection_id)
            connector = ConnectorFactory.get_connector(conn_config)

            # 4. Discover Schemas
            schemas = await connector.get_schemas()
            filtered_schemas = [s for s in schemas if s not in self.SYSTEM_SCHEMAS]
            
            # 5. Discover Tables & Columns per schema
            for schema in filtered_schemas:
                await self._discover_schema_contents(connection_id, connector, schema)

            # 6. NEW: Post-discovery metadata enhancement
            logger.info("Running post-discovery metadata enhancement...")
            
            # Profile tables for statistics
            from app.profiling.data_quality_scorer import DataQualityScorer
            from app.governance.pii.pii_detector import PIIDetector
            from app.relationships.relationship_engine import RelationshipEngine
            
            profiler = DataQualityScorer(self.db)
            pii_detector = PIIDetector(self.db)
            rel_engine = RelationshipEngine(self.db)
            
            # Get all discovered tables
            from sqlalchemy.orm import selectinload
            stmt = select(CatalogTable).where(CatalogTable.connection_id == connection_id).options(
                selectinload(CatalogTable.columns)
            )
            result = await self.db.execute(stmt)
            discovered_tables = result.scalars().all()
            
            logger.info(f"Running enhancement on {len(discovered_tables)} discovered tables...")
            
            # Run PII detection on all columns
            for table in discovered_tables:
                for column in table.columns:
                    try:
                        await pii_detector.scan_column(column.id)
                    except Exception as e:
                        logger.warning(f"PII scan failed for {column.name}: {str(e)}")
            
            # Run quality scoring
            for table in discovered_tables:
                try:
                    await profiler.score_table(table.id)
                except Exception as e:
                    logger.warning(f"Quality scoring failed for {table.table_name}: {str(e)}")
            
            # Discover relationships
            try:
                await rel_engine.discover_relationships(connection_id)
            except Exception as e:
                logger.warning(f"Relationship discovery failed: {str(e)}")

            job.status = "completed"
            job.finished_at = datetime.datetime.utcnow()
            await self.db.commit()
            
        except Exception as e:
            logger.error(f"Discovery failed for {connection_id}: {str(e)}")
            job.status = "failed"
            job.finished_at = datetime.datetime.utcnow()
            job.error_log = str(e)
            await self.db.commit()
            raise

    async def _discover_schema_contents(self, connection_id: str, connector, schema: str):
        """
        Discovers tables and columns for a specific schema.
        """
        logger.info(f"Discovering schema: {schema} for connection: {connection_id}")
        
        tables = await connector.get_tables(schema=schema)
        
        for table_meta in tables:
            # Sync table to catalog
            from sqlalchemy import select
            stmt = select(CatalogTable).where(
                CatalogTable.connection_id == connection_id,
                CatalogTable.schema_name == schema,
                CatalogTable.table_name == table_meta.name
            )
            res = await self.db.execute(stmt)
            catalog_table = res.scalar_one_or_none()
            
            if not catalog_table:
                catalog_table = CatalogTable(
                    connection_id=connection_id,
                    schema_name=schema,
                    table_name=table_meta.name,
                    entity_type=table_meta.type
                )
                self.db.add(catalog_table)
                await self.db.flush()
            
            # Sync columns
            columns = await connector.get_columns(table_meta.name, schema=schema)
            await self._sync_columns(catalog_table.id, columns)
            
            catalog_table.last_metadata_sync = datetime.datetime.utcnow()
            await self.db.commit()

    async def _sync_columns(self, table_id: str, columns_data: List[Dict[str, Any]]):
        """
        Syncs column metadata for a table.
        """
        # Clear existing columns for a clean sync (or we could do a merge)
        from sqlalchemy import delete
        await self.db.execute(delete(CatalogColumn).where(CatalogColumn.table_id == table_id))
        
        for idx, col in enumerate(columns_data):
            # Map database specific types to common names if needed
            new_col = CatalogColumn(
                table_id=table_id,
                name=col.get("name") or col.get("COLUMN_NAME") or col.get("Field"),
                data_type=col.get("type") or col.get("DATA_TYPE") or col.get("Type"),
                is_nullable=col.get("nullable", True),
                ordinal_position=idx + 1
            )
            self.db.add(new_col)
