"""
Semantic Layer Implementation

Maps technical schema to business entities, metrics, and dimensions.
Detects table entities, metrics, and dimensions using heuristics and pattern matching.
"""

import re
from typing import Optional, List, Dict, Tuple
from uuid import UUID
import logging

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from pydantic import BaseModel

from app.models.catalog_models import (
    CatalogTable,
    CatalogColumn,
    CatalogRelationship,
)

logger = logging.getLogger(__name__)


class SemanticEntity(BaseModel):
    """Semantic entity mapping."""
    
    table_name: str
    entity_name: str
    entity_type: str  # "fact", "dimension", "bridge"
    confidence: float
    columns: Dict[str, str]  # column_name → role
    metrics: Dict[str, str]  # metric_name → aggregation
    dimensions: Dict[str, str]  # dimension_name → type
    detected_by: str  # "name_heuristic", "relationship_analysis", "ml_model"


class SemanticMapper:
    """Build semantic understanding of schema."""

    def __init__(self, db_session: AsyncSession):
        self.db = db_session

    # ============================================================================
    # PUBLIC METHODS
    # ============================================================================

    async def detect_entities(
        self, workspace_id: UUID, connection_id: UUID
    ) -> List[SemanticEntity]:
        """
        Detect all semantic entities in a workspace.

        Args:
            workspace_id: Workspace ID
            connection_id: Connection ID

        Returns:
            List of detected entities
        """
        entities = []

        try:
            # Get all tables
            stmt = select(CatalogTable).where(CatalogTable.connection_id == str(connection_id))
            tables = await self.db.scalars(stmt)

            for table in tables:
                entity = await self.map_table_to_entity(table.id)
                if entity:
                    entities.append(entity)

            logger.info(f"Detected {len(entities)} semantic entities")
            return entities
        except Exception as e:
            logger.error(f"Error detecting entities: {e}")
            return []

    async def map_table_to_entity(self, table_id: UUID) -> Optional[SemanticEntity]:
        """
        Map a table to a semantic entity.

        Args:
            table_id: Table ID

        Returns:
            SemanticEntity if detected, None otherwise
        """
        try:
            from sqlalchemy import or_
            table = await self.db.scalar(
                select(CatalogTable).where(CatalogTable.id == str(table_id))
            )
            if not table:
                return None

            # Get columns
            columns = await self.db.scalars(
                select(CatalogColumn).where(CatalogColumn.table_id == str(table_id))
            )
            columns_list = list(columns)

            if not columns_list:
                return None

            # Get relationships
            relationships = await self.db.scalars(
                select(CatalogRelationship).where(
                    or_(
                        CatalogRelationship.source_table_id == str(table_id),
                        CatalogRelationship.target_table_id == str(table_id),
                    )
                )
            )
            relationships_list = list(relationships)

            # Detect entity
            entity_name, entity_type, confidence = self._detect_entity_type(
                table_name=table.table_name,
                columns=columns_list,
                relationships=relationships_list,
            )

            # Classify columns
            column_roles = self._classify_columns(columns_list)

            # Detect metrics
            metrics = self._detect_metrics(columns_list, entity_name)

            # Detect dimensions
            dimensions = self._detect_dimensions(columns_list)

            return SemanticEntity(
                table_name=table.table_name,
                entity_name=entity_name,
                entity_type=entity_type,
                confidence=confidence,
                columns=column_roles,
                metrics=metrics,
                dimensions=dimensions,
                detected_by="name_heuristic_and_relationships",
            )
        except Exception as e:
            logger.error(f"Error mapping table to entity: {e}")
            return None

    async def detect_metrics(self, table_id: UUID) -> Dict[str, str]:
        """
        Detect metrics in a table.

        Args:
            table_id: Table ID

        Returns:
            Dict mapping metric_name → aggregation
        """
        try:
            columns = await self.db.scalars(
                select(CatalogColumn).where(CatalogColumn.table_id == table_id)
            )
            columns_list = list(columns)

            return self._detect_metrics(columns_list, "")
        except Exception as e:
            logger.error(f"Error detecting metrics: {e}")
            return {}

    async def detect_dimensions(self, table_id: UUID) -> Dict[str, str]:
        """
        Detect dimensions in a table.

        Args:
            table_id: Table ID

        Returns:
            Dict mapping dimension_name → type
        """
        try:
            columns = await self.db.scalars(
                select(CatalogColumn).where(CatalogColumn.table_id == table_id)
            )
            columns_list = list(columns)

            return self._detect_dimensions(columns_list)
        except Exception as e:
            logger.error(f"Error detecting dimensions: {e}")
            return {}

    async def detect_facts(self, table_id: UUID) -> Dict[str, str]:
        """
        Detect fact columns in a table.

        Args:
            table_id: Table ID

        Returns:
            Dict mapping fact_column → type
        """
        try:
            columns = await self.db.scalars(
                select(CatalogColumn).where(CatalogColumn.table_id == table_id)
            )
            columns_list = list(columns)

            facts = {}
            for col in columns_list:
                if self._is_fact_column(col):
                    facts[col.name] = col.data_type

            return facts
        except Exception as e:
            logger.error(f"Error detecting facts: {e}")
            return {}

    # ============================================================================
    # PRIVATE METHODS - ENTITY DETECTION
    # ============================================================================

    def _detect_entity_type(
        self, table_name: str, columns: list, relationships: list
    ) -> Tuple[str, str, float]:
        """
        Detect entity type: fact, dimension, or bridge.

        Returns:
            (entity_name, entity_type, confidence)
        """
        col_count = len(columns)
        fk_count = sum(1 for c in columns if c.is_foreign_key)
        pk_count = sum(1 for c in columns if c.is_primary_key)
        incoming_relationships = sum(
            1 for r in relationships if r.target_table_id
        )

        # Fact table heuristics
        if col_count > 10 and fk_count >= 2 and incoming_relationships > 2:
            entity_name = self._extract_entity_name(table_name)
            return entity_name, "fact", 0.85

        # Dimension table heuristics
        if col_count <= 10 and fk_count <= 1:
            entity_name = self._extract_entity_name(table_name)
            return entity_name, "dimension", 0.80

        # Bridge table heuristics
        if "bridge" in table_name.lower() or "junction" in table_name.lower():
            entity_name = self._extract_entity_name(table_name)
            return entity_name, "bridge", 0.90

        # Default
        entity_name = self._extract_entity_name(table_name)
        return entity_name, "entity", 0.50

    def _classify_columns(self, columns: list) -> Dict[str, str]:
        """Classify columns by role (PK, FK, measure, dimension, etc.)."""
        roles = {}

        for col in columns:
            if col.is_primary_key:
                roles[col.name] = "pk"
            elif col.is_foreign_key:
                roles[col.name] = "fk"
            elif self._is_metric_column(col):
                roles[col.name] = "measure"
            elif self._is_dimension_column(col):
                roles[col.name] = "dimension"
            else:
                roles[col.name] = "attribute"

        return roles

    def _detect_metrics(self, columns: list, entity_name: str) -> Dict[str, str]:
        """Detect metric columns and their aggregation type."""
        metrics = {}

        for col in columns:
            if self._is_metric_column(col):
                agg_type = self._infer_aggregation_type(col.name)
                metric_name = self._extract_metric_name(col.name)
                metrics[metric_name] = agg_type

        return metrics

    def _detect_dimensions(self, columns: list) -> Dict[str, str]:
        """Detect dimension columns."""
        dimensions = {}

        for col in columns:
            if self._is_dimension_column(col):
                dim_type = self._infer_dimension_type(col.name, col.data_type)
                dimensions[col.name] = dim_type

        return dimensions

    # ============================================================================
    # HELPER METHODS - COLUMN CLASSIFICATION
    # ============================================================================

    def _is_metric_column(self, col: CatalogColumn) -> bool:
        """Check if column is a metric/measure."""
        col_name = col.name.lower()
        data_type = (col.data_type or "").lower()

        # Numeric types
        if not any(x in data_type for x in ["int", "decimal", "numeric", "float"]):
            return False

        # Metric indicators
        metric_keywords = [
            "amount", "total", "sum", "count", "quantity", "qty",
            "revenue", "sales", "cost", "price", "value", "rate",
            "percentage", "avg", "average", "min", "max", "metric",
        ]

        return any(kw in col_name for kw in metric_keywords)

    def _is_dimension_column(self, col: CatalogColumn) -> bool:
        """Check if column is a dimension."""
        col_name = col.name.lower()
        data_type = (col.data_type or "").lower()

        # Date/time
        if any(x in data_type for x in ["date", "time", "timestamp"]):
            return True

        # Categorical
        categorical_keywords = [
            "type", "category", "status", "region", "country", "state",
            "city", "channel", "segment", "department", "product",
        ]

        return any(kw in col_name for kw in categorical_keywords)

    def _is_fact_column(self, col: CatalogColumn) -> bool:
        """Check if column is a fact (transactional detail)."""
        return not (col.is_primary_key or col.is_foreign_key) and not self._is_metric_column(col)

    # ============================================================================
    # HELPER METHODS - NAME INFERENCE
    # ============================================================================

    def _extract_entity_name(self, table_name: str) -> str:
        """Extract entity name from table name."""
        # Remove common suffixes
        cleaned = re.sub(r"(_v\d+|_temp|_archive|_staging|_fact|_dim)$", "", table_name, flags=re.I)

        # Convert to title case
        cleaned = re.sub(r"_+", " ", cleaned)
        cleaned = " ".join(word.capitalize() for word in cleaned.split())

        return cleaned or table_name

    def _extract_metric_name(self, column_name: str) -> str:
        """Extract clean metric name from column name."""
        # Remove prefixes like "total_", "sum_", "avg_"
        cleaned = re.sub(r"^(total|sum|avg|count|max|min)_", "", column_name, flags=re.I)

        # Convert to title case
        cleaned = re.sub(r"_+", " ", cleaned)
        cleaned = " ".join(word.capitalize() for word in cleaned.split())

        return cleaned or column_name

    def _infer_aggregation_type(self, column_name: str) -> str:
        """Infer aggregation type from column name."""
        col_lower = column_name.lower()

        if "count" in col_lower:
            return "COUNT"
        if "avg" in col_lower or "average" in col_lower:
            return "AVG"
        if "min" in col_lower:
            return "MIN"
        if "max" in col_lower:
            return "MAX"
        if any(x in col_lower for x in ["sum", "total", "amount", "revenue"]):
            return "SUM"

        return "SUM"  # Default

    def _infer_dimension_type(self, column_name: str, data_type: str) -> str:
        """Infer dimension type from column name and data type."""
        col_lower = column_name.lower()
        dtype_lower = (data_type or "").lower()

        # Time dimension
        if any(x in col_lower for x in ["date", "time", "timestamp", "year", "month", "day"]):
            return "time"

        # Geography dimension
        if any(x in col_lower for x in ["country", "state", "city", "region", "location", "geo"]):
            return "geography"

        # Product dimension
        if any(x in col_lower for x in ["product", "item", "sku"]):
            return "product"

        # Customer dimension
        if any(x in col_lower for x in ["customer", "client", "account"]):
            return "customer"

        # Category dimension
        if any(x in col_lower for x in ["category", "type", "class", "segment"]):
            return "category"

        # String → categorical
        if "varchar" in dtype_lower or "char" in dtype_lower or "text" in dtype_lower:
            return "categorical"

        return "attribute"
