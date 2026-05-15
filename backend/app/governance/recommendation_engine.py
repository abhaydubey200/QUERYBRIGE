"""
Recommendation Engine

Automatically suggests improvements to metadata and governance.
Identifies missing owners, unmasked PII, unused tables, quality issues, etc.
"""

from datetime import datetime, timedelta
from typing import List, Optional
from uuid import UUID
import logging

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, func, desc
from pydantic import BaseModel

from app.models.catalog_models import (
    CatalogTable,
    CatalogColumn,
    DataProfile,
    CatalogLineage,
)

logger = logging.getLogger(__name__)


class MetadataRecommendation(BaseModel):
    """Metadata recommendation."""

    id: str
    workspace_id: UUID
    resource_type: str  # "table", "column"
    resource_id: UUID
    resource_name: str
    recommendation_type: str  # "assign_owner", "mask_pii", "fix_description", "flag_unused", "add_glossary", "improve_quality"
    title: str
    description: str
    suggested_action: str
    severity: str  # "info", "warning", "critical"
    created_at: datetime = None

    def __init__(self, **data):
        super().__init__(**data)
        if self.created_at is None:
            self.created_at = datetime.utcnow()


class RecommendationEngine:
    """Generate metadata recommendations."""

    def __init__(self, db_session: AsyncSession):
        self.db = db_session
        self.unused_threshold_days = 90  # Flag tables not queried in 90 days

    # ============================================================================
    # PUBLIC METHODS
    # ============================================================================

    async def generate_recommendations(
        self, workspace_id: UUID
    ) -> List[MetadataRecommendation]:
        """
        Generate all recommendations for a workspace.

        Args:
            workspace_id: Workspace ID

        Returns:
            List of recommendations
        """
        recommendations = []

        try:
            # Get all tables
            tables = await self.db.scalars(
                select(CatalogTable).where(
                    CatalogTable.workspace_id == workspace_id
                )
            )

            for table in tables:
                # Check for owner
                owner_rec = await self._check_assign_owner(table, workspace_id)
                if owner_rec:
                    recommendations.append(owner_rec)

                # Check for PII
                pii_recs = await self._check_mask_pii(table, workspace_id)
                recommendations.extend(pii_recs)

                # Check for description
                desc_rec = await self._check_fix_description(table, workspace_id)
                if desc_rec:
                    recommendations.append(desc_rec)

                # Check for unused
                unused_rec = await self._check_flag_unused(table, workspace_id)
                if unused_rec:
                    recommendations.append(unused_rec)

                # Check for quality
                quality_recs = await self._check_improve_quality(table, workspace_id)
                recommendations.extend(quality_recs)

            logger.info(f"Generated {len(recommendations)} recommendations")
            return recommendations
        except Exception as e:
            logger.error(f"Error generating recommendations: {e}")
            return []

    async def get_recommendations_for_resource(
        self, resource_id: UUID
    ) -> List[MetadataRecommendation]:
        """Get recommendations for a specific resource."""
        recommendations = []

        try:
            # Check if table or column
            table = await self.db.scalar(
                select(CatalogTable).where(CatalogTable.id == resource_id)
            )

            if table:
                # Get all recs for this table
                owner_rec = await self._check_assign_owner(table, table.workspace_id)
                if owner_rec:
                    recommendations.append(owner_rec)

                pii_recs = await self._check_mask_pii(table, table.workspace_id)
                recommendations.extend(pii_recs)

                desc_rec = await self._check_fix_description(table, table.workspace_id)
                if desc_rec:
                    recommendations.append(desc_rec)

                unused_rec = await self._check_flag_unused(table, table.workspace_id)
                if unused_rec:
                    recommendations.append(unused_rec)

                quality_recs = await self._check_improve_quality(table, table.workspace_id)
                recommendations.extend(quality_recs)

            return recommendations
        except Exception as e:
            logger.error(f"Error getting recommendations: {e}")
            return []

    # ============================================================================
    # PRIVATE METHODS - RECOMMENDATION CHECKS
    # ============================================================================

    async def _check_assign_owner(
        self, table: CatalogTable, workspace_id: UUID
    ) -> Optional[MetadataRecommendation]:
        """Check if table needs owner assignment."""
        if table.owner_id:
            return None

        return MetadataRecommendation(
            id=f"assign_owner_{table.id}",
            workspace_id=workspace_id,
            resource_type="table",
            resource_id=table.id,
            resource_name=table.name,
            recommendation_type="assign_owner",
            title=f"Assign owner to {table.name}",
            description=f"The '{table.name}' table does not have a designated owner. "
            f"Assigning an owner ensures accountability and proper data governance.",
            suggested_action="Navigate to table details and assign an owner from the team",
            severity="warning",
        )

    async def _check_mask_pii(
        self, table: CatalogTable, workspace_id: UUID
    ) -> List[MetadataRecommendation]:
        """Check for unmasked PII columns."""
        recommendations = []

        try:
            # Get columns
            columns = await self.db.scalars(
                select(CatalogColumn).where(
                    and_(
                        CatalogColumn.table_id == table.id,
                    )
                )
            )

            pii_columns = []
            for col in columns:
                # Check if marked as PII but not masked
                # (This would require a masked_at field in production)
                if col.is_pii and not col.is_masked:
                    pii_columns.append(col.name)

            if pii_columns:
                recommendations.append(
                    MetadataRecommendation(
                        id=f"mask_pii_{table.id}",
                        workspace_id=workspace_id,
                        resource_type="table",
                        resource_id=table.id,
                        resource_name=table.name,
                        recommendation_type="mask_pii",
                        title=f"Apply masking to {len(pii_columns)} PII columns in {table.name}",
                        description=f"Columns {', '.join(pii_columns)} contain PII and should be "
                        f"masked to comply with GDPR, CCPA, and other privacy regulations.",
                        suggested_action="Apply masking policies to these columns via governance settings",
                        severity="critical",
                    )
                )

            return recommendations
        except Exception as e:
            logger.error(f"Error checking PII: {e}")
            return []

    async def _check_fix_description(
        self, table: CatalogTable, workspace_id: UUID
    ) -> Optional[MetadataRecommendation]:
        """Check if table description is missing or vague."""
        if table.description and len(table.description.strip()) > 20:
            return None

        return MetadataRecommendation(
            id=f"fix_description_{table.id}",
            workspace_id=workspace_id,
            resource_type="table",
            resource_id=table.id,
            resource_name=table.name,
            recommendation_type="fix_description",
            title=f"Add description to {table.name}",
            description=f"The '{table.name}' table lacks a clear description. "
            f"Adding a business-friendly description helps other users understand the table's purpose.",
            suggested_action="Edit the table and add a meaningful description in the metadata form",
            severity="info",
        )

    async def _check_flag_unused(
        self, table: CatalogTable, workspace_id: UUID
    ) -> Optional[MetadataRecommendation]:
        """Check if table is unused (not queried recently)."""
        try:
            # Get last profile timestamp
            last_profile = await self.db.scalar(
                select(DataProfile)
                .where(DataProfile.table_id == table.id)
                .order_by(desc(DataProfile.created_at))
                .limit(1)
            )

            if not last_profile:
                return None

            days_since_update = (datetime.utcnow() - last_profile.created_at).days

            if days_since_update > self.unused_threshold_days:
                return MetadataRecommendation(
                    id=f"flag_unused_{table.id}",
                    workspace_id=workspace_id,
                    resource_type="table",
                    resource_id=table.id,
                    resource_name=table.name,
                    recommendation_type="flag_unused",
                    title=f"Review {table.name} for deprecation",
                    description=f"The '{table.name}' table hasn't been accessed in {days_since_update} days. "
                    f"Consider archiving or deprecating this table if it's no longer needed.",
                    suggested_action="Review with data owner; archive or mark as deprecated if unused",
                    severity="info",
                )

            return None
        except Exception as e:
            logger.error(f"Error checking unused tables: {e}")
            return None

    async def _check_improve_quality(
        self, table: CatalogTable, workspace_id: UUID
    ) -> List[MetadataRecommendation]:
        """Check for data quality issues."""
        recommendations = []

        try:
            # Get latest profile
            profile = await self.db.scalar(
                select(DataProfile)
                .where(DataProfile.table_id == table.id)
                .order_by(desc(DataProfile.created_at))
                .limit(1)
            )

            if not profile or not profile.profile_data:
                return []

            profile_data = profile.profile_data
            if not isinstance(profile_data, dict):
                return []

            # Check for high null %
            columns_data = profile_data.get("columns", [])
            for col_data in columns_data:
                null_pct = col_data.get("null_percentage", 0)
                col_name = col_data.get("name")

                if null_pct > 50:
                    recommendations.append(
                        MetadataRecommendation(
                            id=f"high_null_{table.id}_{col_name}",
                            workspace_id=workspace_id,
                            resource_type="column",
                            resource_id=table.id,
                            resource_name=f"{table.name}.{col_name}",
                            recommendation_type="improve_quality",
                            title=f"High null percentage in {col_name}",
                            description=f"Column '{col_name}' in '{table.name}' has {null_pct:.0f}% null values. "
                            f"This indicates potential data quality issues.",
                            suggested_action="Investigate data pipeline; check for ETL failures or data deletion",
                            severity="high",
                        )
                    )

            return recommendations
        except Exception as e:
            logger.error(f"Error checking quality: {e}")
            return []
