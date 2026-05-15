"""
Relationship Discovery Engine - Detects FK constraints and infers joins
"""
from typing import List, Dict, Any, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from app.models.catalog_models import CatalogTable, CatalogColumn, CatalogRelationship
from app.connectors.connector_factory import ConnectorFactory
from app.services.connection_manager import ConnectionManager
from loguru import logger


class RelationshipEngine:
    """
    Detects and infers relationships between tables.
    Uses both explicit FK constraints and heuristic name matching.
    """
    
    def __init__(self, db: AsyncSession):
        self.db = db

    async def discover_relationships(self, connection_id: str):
        """
        Main entry point for relationship discovery.
        1. First: Extract explicit FK constraints from database catalogs
        2. Second: Infer implicit relationships via naming heuristics
        """
        # 1. Get all tables for this connection
        stmt = select(CatalogTable).where(CatalogTable.connection_id == connection_id)
        result = await self.db.execute(stmt)
        tables = result.scalars().all()
        
        logger.info(f"Discovering relationships for {len(tables)} tables")

        if not tables:
            return

        # 2. Get connector for FK constraint extraction
        _, conn_config = await ConnectionManager._load_connection_config(self.db, connection_id)
        connector = ConnectorFactory.get_connector(conn_config)

        # 3. Extract explicit FK constraints first (high confidence)
        for table in tables:
            await self._discover_fk_constraints(connection_id, connector, table, tables)

        # 4. Infer implicit relationships (medium confidence)
        for source_table in tables:
            await self._infer_implicit_relationships(source_table, tables)

        await self.db.commit()
        logger.info(f"Completed relationship discovery for {len(tables)} tables")

    async def _discover_fk_constraints(self, connection_id: str, connector, 
                                       source_table: CatalogTable, all_tables: List[CatalogTable]):
        """
        Extract explicit FK constraints from the database catalog.
        Different SQL for each database type.
        """
        db_type = connector.config.type.lower()
        
        try:
            if db_type == "postgres":
                await self._discover_fk_postgres(connection_id, connector, source_table, all_tables)
            elif db_type == "mysql":
                await self._discover_fk_mysql(connection_id, connector, source_table, all_tables)
            elif db_type == "mssql":
                await self._discover_fk_mssql(connection_id, connector, source_table, all_tables)
            elif db_type == "oracle":
                await self._discover_fk_oracle(connection_id, connector, source_table, all_tables)
            elif db_type == "snowflake":
                await self._discover_fk_snowflake(connection_id, connector, source_table, all_tables)
        except Exception as e:
            logger.debug(f"FK discovery not available for {db_type}: {str(e)}")

    async def _discover_fk_postgres(self, connection_id: str, connector,
                                    source_table: CatalogTable, all_tables: List[CatalogTable]):
        """PostgreSQL FK constraint discovery"""
        query = f"""
            SELECT
                kcu.column_name,
                ccu.table_name AS foreign_table_name,
                ccu.column_name AS foreign_column_name
            FROM information_schema.table_constraints AS tc
            JOIN information_schema.key_column_usage AS kcu
                ON tc.constraint_name = kcu.constraint_name
            JOIN information_schema.constraint_column_usage AS ccu
                ON ccu.constraint_name = tc.constraint_name
            WHERE tc.constraint_type = 'FOREIGN KEY'
                AND tc.table_schema = '{source_table.schema_name}'
                AND tc.table_name = '{source_table.table_name}'
        """
        
        try:
            async for row in connector.stream_query(query, max_rows=1000):
                source_col_name = row.get("column_name")
                target_table_name = row.get("foreign_table_name")
                target_col_name = row.get("foreign_column_name")
                
                await self._create_fk_relationship(
                    connection_id, source_table, source_col_name,
                    all_tables, target_table_name, target_col_name
                )
        except Exception as e:
            logger.debug(f"PostgreSQL FK discovery failed: {str(e)}")

    async def _discover_fk_mysql(self, connection_id: str, connector,
                                 source_table: CatalogTable, all_tables: List[CatalogTable]):
        """MySQL FK constraint discovery"""
        db_name = source_table.schema_name or connector.config.database
        query = f"""
            SELECT
                COLUMN_NAME,
                REFERENCED_TABLE_NAME,
                REFERENCED_COLUMN_NAME
            FROM INFORMATION_SCHEMA.KEY_COLUMN_USAGE
            WHERE TABLE_SCHEMA = '{db_name}'
                AND TABLE_NAME = '{source_table.table_name}'
                AND REFERENCED_TABLE_NAME IS NOT NULL
        """
        
        try:
            async for row in connector.stream_query(query, max_rows=1000):
                source_col_name = row.get("COLUMN_NAME")
                target_table_name = row.get("REFERENCED_TABLE_NAME")
                target_col_name = row.get("REFERENCED_COLUMN_NAME")
                
                await self._create_fk_relationship(
                    connection_id, source_table, source_col_name,
                    all_tables, target_table_name, target_col_name
                )
        except Exception as e:
            logger.debug(f"MySQL FK discovery failed: {str(e)}")

    async def _discover_fk_mssql(self, connection_id: str, connector,
                                 source_table: CatalogTable, all_tables: List[CatalogTable]):
        """MSSQL FK constraint discovery"""
        query = f"""
            SELECT
                COL_NAME(fkc.parent_object_id, fkc.parent_column_id) AS source_column,
                OBJECT_NAME(fkc.referenced_object_id) AS target_table,
                COL_NAME(fkc.referenced_object_id, fkc.referenced_column_id) AS target_column
            FROM sys.foreign_key_columns AS fkc
            WHERE OBJECT_NAME(fkc.parent_object_id) = '{source_table.table_name}'
        """
        
        try:
            async for row in connector.stream_query(query, max_rows=1000):
                source_col_name = row.get("source_column")
                target_table_name = row.get("target_table")
                target_col_name = row.get("target_column")
                
                await self._create_fk_relationship(
                    connection_id, source_table, source_col_name,
                    all_tables, target_table_name, target_col_name
                )
        except Exception as e:
            logger.debug(f"MSSQL FK discovery failed: {str(e)}")

    async def _discover_fk_oracle(self, connection_id: str, connector,
                                  source_table: CatalogTable, all_tables: List[CatalogTable]):
        """Oracle FK constraint discovery"""
        # Placeholder - would need proper Oracle implementation
        pass

    async def _discover_fk_snowflake(self, connection_id: str, connector,
                                     source_table: CatalogTable, all_tables: List[CatalogTable]):
        """Snowflake FK constraint discovery"""
        # Placeholder - Snowflake doesn't enforce FKs
        pass

    async def _create_fk_relationship(self, connection_id: str, source_table: CatalogTable,
                                     source_col_name: str, all_tables: List[CatalogTable],
                                     target_table_name: str, target_col_name: str):
        """
        Helper: Create FK relationship from extracted constraint.
        """
        try:
            # Find source column
            source_col = next((col for col in source_table.columns if col.name.lower() == source_col_name.lower()), None)
            if not source_col:
                return

            # Find target table and column
            target_table = next((t for t in all_tables if t.table_name.lower() == target_table_name.lower()), None)
            if not target_table:
                return

            target_col = next((col for col in target_table.columns if col.name.lower() == target_col_name.lower()), None)
            if not target_col:
                return

            # Create relationship
            await self._create_relationship(
                connection_id=connection_id,
                source_table_id=source_table.id,
                source_column_id=source_col.id,
                target_table_id=target_table.id,
                target_column_id=target_col.id,
                relationship_type="Many-to-One",
                confidence=0.95,  # High confidence for explicit FKs
                method="explicit_fk_constraint"
            )
        except Exception as e:
            logger.debug(f"Could not create FK relationship: {str(e)}")

    async def _infer_implicit_relationships(self, source_table: CatalogTable, all_tables: List[CatalogTable]):
        """
        Infers relationships using naming conventions (e.g. customer_id -> customers.id).
        Lower confidence than explicit FKs.
        """
        # Load columns for source table
        stmt = select(CatalogTable).where(CatalogTable.id == source_table.id).options(
            selectinload(CatalogTable.columns)
        )
        result = await self.db.execute(stmt)
        source_table = result.scalar_one()

        for column in source_table.columns:
            col_name = column.name.lower()
            
            # Look for "entity_id" patterns
            if col_name.endswith("_id") or col_name.endswith("id"):
                potential_target_name = col_name.replace("_id", "").replace("id", "").rstrip('_')
                
                for target_table in all_tables:
                    if target_table.id == source_table.id:
                        continue
                        
                    # Match if target table name is similar to the prefix
                    # Match with pluralization consideration
                    if (target_table.table_name.lower().rstrip('s') == potential_target_name.rstrip('s')):
                        # Check if this FK doesn't already exist
                        existing = await self.db.execute(
                            select(CatalogRelationship).where(
                                CatalogRelationship.source_column_id == column.id,
                                CatalogRelationship.target_table_id == target_table.id
                            )
                        )
                        if not existing.scalar_one_or_none():
                            await self._create_relationship(
                                connection_id=source_table.connection_id,
                                source_table_id=source_table.id,
                                source_column_id=column.id,
                                target_table_id=target_table.id,
                                target_column_id=None,  # Will find 'id' column
                                relationship_type="Many-to-One",
                                confidence=0.75,  # Medium confidence for heuristics
                                method="heuristic_name_match"
                            )

    async def _create_relationship(self, connection_id: str, source_table_id: str, source_column_id: str,
                                  target_table_id: str, target_column_id: Optional[str], 
                                  relationship_type: str, confidence: float, method: str):
        """
        Saves a discovered relationship.
        """
        # If target column not specified, find 'id' column
        if not target_column_id:
            stmt = select(CatalogColumn).where(
                CatalogColumn.table_id == target_table_id,
                CatalogColumn.name.ilike("id")
            )
            res = await self.db.execute(stmt)
            target_col = res.scalar_one_or_none()
            
            if not target_col:
                return
            target_column_id = target_col.id

        # Check if already exists
        check_stmt = select(CatalogRelationship).where(
            CatalogRelationship.source_column_id == source_column_id,
            CatalogRelationship.target_column_id == target_column_id
        )
        existing = await self.db.execute(check_stmt)
        if existing.scalar_one_or_none():
            return

        rel = CatalogRelationship(
            connection_id=connection_id,
            source_table_id=source_table_id,
            source_column_id=source_column_id,
            target_table_id=target_table_id,
            target_column_id=target_column_id,
            relationship_type=relationship_type,
            confidence_score=confidence,
            discovery_method=method
        )
        self.db.add(rel)
        logger.info(f"Created {method} relationship: {source_table_id}.{source_column_id} -> {target_table_id}.{target_column_id} (confidence: {confidence})")
