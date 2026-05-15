"""
Relationship Explanation Engine

Generates human-readable descriptions of table joins and relationships.
Explains cardinality and business meaning.
"""

import re
from typing import Optional, Tuple
from uuid import UUID
import logging

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.catalog_models import (
    CatalogTable,
    CatalogRelationship,
)

logger = logging.getLogger(__name__)


class RelationshipExplainer:
    """Generate human-readable join explanations."""

    def __init__(self, db_session: AsyncSession):
        self.db = db_session

    # ============================================================================
    # PUBLIC METHODS
    # ============================================================================

    async def explain_relationship(
        self, source_table_id: UUID, target_table_id: UUID
    ) -> str:
        """
        Generate explanation for a relationship between two tables.

        Args:
            source_table_id: Source table ID
            target_table_id: Target table ID

        Returns:
            Human-readable explanation
        """
        try:
            # Get tables
            source = await self.db.scalar(
                select(CatalogTable).where(CatalogTable.id == source_table_id)
            )
            target = await self.db.scalar(
                select(CatalogTable).where(CatalogTable.id == target_table_id)
            )

            if not source or not target:
                return "Unable to find tables for explanation."

            # Get relationship
            relationship = await self.db.scalar(
                select(CatalogRelationship).where(
                    (CatalogRelationship.source_table_id == source_table_id)
                    & (CatalogRelationship.target_table_id == target_table_id)
                )
            )

            if not relationship:
                return f"No direct relationship between {source.table_name} and {target.table_name}."

            # Explain
            explanation = await self.explain_join(
                relationship,
                source,
                target,
            )

            return explanation
        except Exception as e:
            logger.error(f"Error explaining relationship: {e}")
            return "Error: Could not generate explanation."

    async def explain_join(
        self,
        relationship: CatalogRelationship,
        source_table: Optional[CatalogTable] = None,
        target_table: Optional[CatalogTable] = None,
    ) -> str:
        """
        Generate explanation for a join.

        Args:
            relationship: Relationship definition
            source_table: Optional source table (for better explanation)
            target_table: Optional target table (for better explanation)

        Returns:
            Human-readable join explanation
        """
        try:
            # Get tables if not provided
            if not source_table:
                source_table = await self.db.scalar(
                    select(CatalogTable).where(
                        CatalogTable.id == relationship.source_table_id
                    )
                )

            if not target_table:
                target_table = await self.db.scalar(
                    select(CatalogTable).where(
                        CatalogTable.id == relationship.target_table_id
                    )
                )

            if not source_table or not target_table:
                return "Unable to generate explanation."

            # Infer entity names
            source_entity = self._infer_entity_name(source_table.table_name)
            target_entity = self._infer_entity_name(target_table.table_name)

            # Get cardinality from relationship
            cardinality = relationship.relationship_type or "unknown"

            # Generate explanation
            explanation = self._generate_explanation(
                source_entity=source_entity,
                target_entity=target_entity,
                cardinality=cardinality,
                source_column=relationship.source_column_id,
                target_column=relationship.target_column_id,
                confidence=relationship.confidence_score,
            )

            return explanation
        except Exception as e:
            logger.error(f"Error explaining join: {e}")
            return "Error: Could not generate explanation."

    async def explain_many_to_many(
        self,
        source_table_id: UUID,
        target_table_id: UUID,
        junction_table_id: UUID,
    ) -> str:
        """
        Generate explanation for many-to-many relationship.

        Args:
            source_table_id: First table ID
            target_table_id: Second table ID
            junction_table_id: Junction/bridge table ID

        Returns:
            Human-readable explanation
        """
        try:
            source = await self.db.scalar(
                select(CatalogTable).where(CatalogTable.id == source_table_id)
            )
            target = await self.db.scalar(
                select(CatalogTable).where(CatalogTable.id == target_table_id)
            )
            junction = await self.db.scalar(
                select(CatalogTable).where(CatalogTable.id == junction_table_id)
            )

            if not (source and target and junction):
                return "Unable to find tables for explanation."

            source_entity = self._infer_entity_name(source.name)
            target_entity = self._infer_entity_name(target.name)
            junction_entity = self._infer_entity_name(junction.name)

            explanation = (
                f"Each {source_entity} can be associated with many {target_entity}s, "
                f"and vice versa, through the {junction_entity} table."
            )

            return explanation
        except Exception as e:
            logger.error(f"Error explaining many-to-many: {e}")
            return "Error: Could not generate explanation."

    async def explain_join_path(self, path: list) -> str:
        """
        Generate explanation for a join path.

        Args:
            path: List of table IDs in join path

        Returns:
            Human-readable path explanation
        """
        try:
            if not path or len(path) < 2:
                return "Join path too short."

            tables = []
            for table_id in path:
                table = await self.db.scalar(
                    select(CatalogTable).where(CatalogTable.id == table_id)
                )
                if table:
                    tables.append(table)

            if len(tables) < 2:
                return "Unable to resolve all tables in path."

            # Build explanation
            entities = [self._infer_entity_name(t.name) for t in tables]

            if len(entities) == 2:
                return f"To join {entities[0]} to {entities[1]}, use: {' → '.join(entities)}"

            explanation = f"To join {entities[0]} to {entities[-1]}, traverse: {' → '.join(entities)}"

            return explanation
        except Exception as e:
            logger.error(f"Error explaining join path: {e}")
            return "Error: Could not generate explanation."

    # ============================================================================
    # HELPER METHODS
    # ============================================================================

    def _infer_entity_name(self, table_name: str) -> str:
        """Extract entity name from table name."""
        # Remove common suffixes
        cleaned = re.sub(
            r"(_v\d+|_temp|_archive|_staging|_fact|_dim|_bridge)$",
            "",
            table_name,
            flags=re.I,
        )

        # Convert underscores to spaces
        cleaned = re.sub(r"_+", " ", cleaned)

        # Capitalize words
        cleaned = " ".join(word.capitalize() for word in cleaned.split())

        # Remove trailing 's' for singularity
        if cleaned.endswith("s"):
            cleaned = cleaned[:-1]

        return cleaned or table_name

    def _generate_explanation(
        self,
        source_entity: str,
        target_entity: str,
        cardinality: str,
        source_column: str,
        target_column: str,
        confidence: float,
    ) -> str:
        """Generate join explanation based on cardinality."""

        # Normalize cardinality
        card_lower = cardinality.lower()

        if "one_to_many" in card_lower or "1:n" in card_lower:
            explanation = (
                f"Each {source_entity} can have zero or more {target_entity}s. "
                f"Join on {source_column} = {target_column}."
            )
        elif "many_to_one" in card_lower or "n:1" in card_lower:
            explanation = (
                f"Each {target_entity} belongs to exactly one {source_entity}. "
                f"Join on {source_column} = {target_column}."
            )
        elif "many_to_many" in card_lower or "n:n" in card_lower:
            explanation = (
                f"Each {source_entity} can be related to many {target_entity}s, "
                f"and vice versa. Join on {source_column} = {target_column}."
            )
        elif "one_to_one" in card_lower or "1:1" in card_lower:
            explanation = (
                f"Each {source_entity} maps to exactly one {target_entity}. "
                f"Join on {source_column} = {target_column}."
            )
        else:
            explanation = (
                f"There is a relationship between {source_entity} and {target_entity}. "
                f"Join on {source_column} = {target_column}."
            )

        # Add confidence note
        if confidence and confidence < 0.80:
            explanation += f" ⚠️ (Low confidence: {confidence:.0%})"
        elif confidence and confidence >= 0.95:
            explanation += f" ✓ (High confidence: {confidence:.0%})"

        return explanation
