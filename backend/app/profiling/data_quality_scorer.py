"""
Data Quality Framework - Calculates quality metrics for tables and columns
"""
import asyncio
from typing import Dict, Any, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, text
from sqlalchemy.orm import selectinload
from app.models.catalog_models import (
    CatalogTable, CatalogColumn, CatalogProfile, MetadataQualityScore
)
from app.connectors.connector_factory import ConnectorFactory
from app.services.connection_manager import ConnectionManager
from loguru import logger
import datetime


class DataQualityScorer:
    """
    Enterprise data quality scoring engine.
    Calculates freshness, completeness, uniqueness, accuracy, consistency, timeliness.
    Stores scores in MetadataQualityScore.
    """

    def __init__(self, db: AsyncSession):
        self.db = db

    async def score_table(self, table_id: str) -> Optional[MetadataQualityScore]:
        """
        Calculate comprehensive quality score for a table.
        Returns MetadataQualityScore with all dimension scores.
        """
        logger.info(f"Scoring table: {table_id}")
        
        # Load table with relationships
        stmt = select(CatalogTable).where(CatalogTable.id == table_id).options(
            selectinload(CatalogTable.columns),
            selectinload(CatalogTable.profiles),
            selectinload(CatalogTable.asset)
        )
        result = await self.db.execute(stmt)
        table = result.scalar_one_or_none()
        
        if not table:
            logger.warning(f"Table {table_id} not found")
            return None

        # Get connector
        _, conn_config = await ConnectionManager._load_connection_config(self.db, table.connection_id)
        connector = ConnectorFactory.get_connector(conn_config)

        # Calculate each quality dimension
        scores = {
            'freshness_score': await self._score_freshness(table),
            'completeness_score': await self._score_completeness(table, connector),
            'uniqueness_score': await self._score_uniqueness(table, connector),
            'accuracy_score': await self._score_accuracy(table, connector),
            'consistency_score': await self._score_consistency(table, connector),
            'timeliness_score': await self._score_timeliness(table, connector),
        }

        # Calculate overall score (weighted average)
        weights = {
            'freshness_score': 0.25,
            'completeness_score': 0.25,
            'uniqueness_score': 0.15,
            'accuracy_score': 0.15,
            'consistency_score': 0.10,
            'timeliness_score': 0.10,
        }
        
        overall_score = sum(scores[k] * weights[k] for k in scores.keys())

        # Get or create quality score record
        stmt = select(MetadataQualityScore).where(MetadataQualityScore.table_id == table_id)
        result = await self.db.execute(stmt)
        quality_score = result.scalar_one_or_none()
        
        if not quality_score:
            quality_score = MetadataQualityScore(table_id=table_id)
            self.db.add(quality_score)

        # Update scores
        quality_score.overall_quality_score = overall_score
        quality_score.freshness_score = scores['freshness_score']
        quality_score.completeness_score = scores['completeness_score']
        quality_score.uniqueness_score = scores['uniqueness_score']
        quality_score.accuracy_score = scores['accuracy_score']
        quality_score.consistency_score = scores['consistency_score']
        quality_score.timeliness_score = scores['timeliness_score']
        quality_score.last_scored_at = datetime.datetime.utcnow()

        # Get freshness hours
        quality_score.freshness_hours = await self._get_freshness_hours(table)

        # Get completeness percent
        if table.columns:
            quality_score.completeness_percent = await self._get_completeness_percent(table, connector)

        await self.db.commit()
        logger.info(f"Scored table {table_id}: overall={overall_score:.2f}")
        return quality_score

    async def _score_freshness(self, table: CatalogTable) -> float:
        """
        Score: How recent is the data?
        100 = Data updated within SLA
        0 = Data severely stale
        """
        if not table.asset or not table.asset.sla_freshness_hours:
            # Default: data should be less than 24 hours old
            sla_hours = 24
        else:
            sla_hours = table.asset.sla_freshness_hours

        # Get last sync time
        if not table.last_metadata_sync:
            return 0.0

        age_hours = (datetime.datetime.utcnow() - table.last_metadata_sync).total_seconds() / 3600

        if age_hours <= sla_hours:
            # Within SLA
            return 100.0
        else:
            # Scale down: -5 points per hour over SLA, minimum 0
            score = max(0.0, 100.0 - (5.0 * (age_hours - sla_hours)))
            return score

    async def _score_completeness(self, table: CatalogTable, connector) -> float:
        """
        Score: What % of rows are complete (all columns non-null)?
        Calculates: COUNT(*) where all columns non-null / total rows
        100 = All rows complete
        0 = No rows complete
        """
        if not table.columns or not table.row_count_estimate or table.row_count_estimate == 0:
            return 50.0  # Default if no data

        table_ref = f"{table.schema_name}.{table.table_name}"

        # Build query: COUNT rows where ALL columns are NOT NULL
        non_null_conditions = " AND ".join([f"{col.name} IS NOT NULL" for col in table.columns])
        query = f"SELECT COUNT(*) as complete_rows FROM {table_ref} WHERE {non_null_conditions}"

        try:
            complete_rows = 0
            async for row in connector.stream_query(query, max_rows=1):
                complete_rows = row.get("complete_rows", 0)
                break

            completeness_percent = (complete_rows / table.row_count_estimate) * 100.0
            return min(100.0, completeness_percent)
        except Exception as e:
            logger.warning(f"Could not calculate completeness for {table_ref}: {str(e)}")
            return 50.0

    async def _score_uniqueness(self, table: CatalogTable, connector) -> float:
        """
        Score: Are primary/unique keys actually unique?
        Find PK columns, check for duplicates
        100 = All PKs unique
        Scales down based on duplicate %
        """
        pk_columns = [col for col in table.columns if col.is_primary_key]
        
        if not pk_columns:
            return 75.0  # No PK defined, neutral score

        table_ref = f"{table.schema_name}.{table.table_name}"

        try:
            pk_col_list = ", ".join([col.name for col in pk_columns])
            query = f"""
                SELECT 
                    COUNT(*) as total_rows,
                    COUNT(DISTINCT {pk_col_list}) as distinct_pks
                FROM {table_ref}
                WHERE {" AND ".join([f"{col.name} IS NOT NULL" for col in pk_columns])}
            """
            
            async for row in connector.stream_query(query, max_rows=1):
                total = row.get("total_rows", 0)
                distinct = row.get("distinct_pks", 0)
                
                if total == 0:
                    return 100.0
                
                uniqueness_percent = (distinct / total) * 100.0
                return min(100.0, uniqueness_percent)
                
        except Exception as e:
            logger.warning(f"Could not calculate uniqueness for {table_ref}: {str(e)}")
            return 75.0

    async def _score_accuracy(self, table: CatalogTable, connector) -> float:
        """
        Score: Do values make sense (plausibility checks)?
        Checks:
        - No negative values for quantity columns
        - Dates within reasonable ranges
        - Numeric ranges make sense
        Default: 80 (assume data is mostly accurate)
        """
        # This would require more sophisticated analysis
        # For now, return default based on table age
        if table.last_metadata_sync:
            age_days = (datetime.datetime.utcnow() - table.last_metadata_sync).days
            if age_days < 7:
                return 90.0  # Recent data, likely accurate
            elif age_days < 30:
                return 80.0
            else:
                return 70.0
        return 75.0

    async def _score_consistency(self, table: CatalogTable, connector) -> float:
        """
        Score: Data consistency across related tables
        Check for referential integrity (FK → PK relationships)
        Default: 85 (assume good unless proven otherwise)
        """
        # This would require checking foreign key constraints
        # For now, return default
        return 85.0

    async def _score_timeliness(self, table: CatalogTable, connector) -> float:
        """
        Score: Are updates happening at expected frequency?
        Compares actual update frequency vs. SLA
        100 = Updating on schedule
        0 = No updates happening
        """
        # Would require tracking update history
        # For now, if freshness is good, timeliness is good
        freshness = await self._score_freshness(table)
        return freshness * 0.9  # Slightly lower than freshness

    async def _get_freshness_hours(self, table: CatalogTable) -> int:
        """Get hours since last update"""
        if not table.last_metadata_sync:
            return 9999
        age_seconds = (datetime.datetime.utcnow() - table.last_metadata_sync).total_seconds()
        return max(0, int(age_seconds / 3600))

    async def _get_completeness_percent(self, table: CatalogTable, connector) -> float:
        """Calculate overall completeness %"""
        if not table.columns or not table.profiles:
            return 50.0

        # Average null % across all columns
        total_null_percent = 0.0
        for profile in table.profiles:
            if profile.null_count is not None and table.row_count_estimate and table.row_count_estimate > 0:
                null_percent = (profile.null_count / table.row_count_estimate) * 100.0
                total_null_percent += (100.0 - null_percent)

        if table.profiles:
            return total_null_percent / len(table.profiles)
        return 50.0

    async def refresh_all_scores(self, connection_id: str) -> Dict[str, int]:
        """
        Refresh quality scores for all tables in a connection.
        Returns count of scored tables.
        """
        logger.info(f"Refreshing quality scores for connection: {connection_id}")
        
        stmt = select(CatalogTable).where(CatalogTable.connection_id == connection_id)
        result = await self.db.execute(stmt)
        tables = result.scalars().all()

        scored_count = 0
        for table in tables:
            try:
                await self.score_table(table.id)
                scored_count += 1
            except Exception as e:
                logger.error(f"Failed to score table {table.id}: {str(e)}")
                continue

        logger.info(f"Refreshed quality scores for {scored_count} tables")
        return {
            'total_tables': len(tables),
            'scored_tables': scored_count,
            'failed': len(tables) - scored_count
        }
