"""
Data Quality Anomaly Detector

Detects unusual patterns in table profiling data.
Identifies row count spikes, null % increases, cardinality shifts, freshness delays.
"""

from datetime import datetime, timedelta
from typing import Optional, List, Dict
from uuid import UUID
import logging

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, desc
from pydantic import BaseModel

from app.models.catalog_models import (
    CatalogTable,
    DataProfile,
    CatalogColumn,
)

logger = logging.getLogger(__name__)


class Anomaly(BaseModel):
    """Represents a detected anomaly."""

    id: str
    table_id: UUID
    column_id: Optional[UUID] = None
    anomaly_type: str  # "row_spike", "null_increase", "cardinality_shift", "freshness_delay"
    severity: str  # "low", "medium", "high", "critical"
    detected_at: datetime
    baseline_value: float
    current_value: float
    deviation_pct: float
    description: str
    suggested_action: str


class AnomalyDetector:
    """Detect anomalies in table profiling data."""

    def __init__(self, db_session: AsyncSession):
        self.db = db_session

    # ============================================================================
    # PUBLIC METHODS
    # ============================================================================

    async def detect_anomalies(
        self, table_id: UUID, lookback_days: int = 30
    ) -> List[Anomaly]:
        """
        Detect all anomalies for a table.

        Args:
            table_id: Table ID
            lookback_days: Days to look back for historical data

        Returns:
            List of detected anomalies
        """
        anomalies = []

        try:
            # Get current profile
            current_profile = await self.db.scalar(
                select(DataProfile)
                .where(DataProfile.table_id == table_id)
                .order_by(desc(DataProfile.created_at))
                .limit(1)
            )

            if not current_profile:
                logger.debug(f"No profile found for table {table_id}")
                return []

            # Detect row count spike
            row_spike = await self.detect_row_count_spike(table_id, lookback_days)
            if row_spike:
                anomalies.append(row_spike)

            # Detect null % increase
            null_anomalies = await self.detect_null_increase(table_id, lookback_days)
            anomalies.extend(null_anomalies)

            # Detect cardinality shift
            cardinality_anomalies = await self.detect_cardinality_shift(
                table_id, lookback_days
            )
            anomalies.extend(cardinality_anomalies)

            # Detect freshness delay
            freshness_anomaly = await self.detect_freshness_delay(table_id)
            if freshness_anomaly:
                anomalies.append(freshness_anomaly)

            return anomalies
        except Exception as e:
            logger.error(f"Error detecting anomalies: {e}")
            return []

    async def detect_row_count_spike(
        self, table_id: UUID, lookback_days: int = 30
    ) -> Optional[Anomaly]:
        """
        Detect if row count has spiked.

        Args:
            table_id: Table ID
            lookback_days: Days to look back

        Returns:
            Anomaly if detected, None otherwise
        """
        try:
            table = await self.db.scalar(
                select(CatalogTable).where(CatalogTable.id == table_id)
            )
            if not table:
                return None

            # Get historical profiles
            cutoff_date = datetime.utcnow() - timedelta(days=lookback_days)
            profiles = await self.db.scalars(
                select(DataProfile)
                .where(
                    and_(
                        DataProfile.table_id == table_id,
                        DataProfile.created_at >= cutoff_date,
                    )
                )
                .order_by(DataProfile.created_at)
            )
            profiles_list = list(profiles)

            if len(profiles_list) < 2:
                return None

            # Calculate baseline (average excluding outliers)
            row_counts = [p.row_count for p in profiles_list if p.row_count]
            if len(row_counts) < 2:
                return None

            baseline = sum(row_counts[:-1]) / len(row_counts[:-1]) if len(row_counts) > 1 else row_counts[0]
            current = row_counts[-1]

            # Calculate deviation
            deviation_pct = ((current - baseline) / baseline) * 100 if baseline > 0 else 0

            # Detect spike
            if deviation_pct > 30:  # 30% increase threshold
                severity = self._calculate_severity_from_deviation(deviation_pct)

                return Anomaly(
                    id=f"row_spike_{table_id}_{datetime.utcnow().timestamp()}",
                    table_id=table_id,
                    anomaly_type="row_spike",
                    severity=severity,
                    detected_at=datetime.utcnow(),
                    baseline_value=baseline,
                    current_value=current,
                    deviation_pct=deviation_pct,
                    description=f"Row count increased {deviation_pct:.1f}% from {self._format_number(int(baseline))} to {self._format_number(int(current))}",
                    suggested_action="Investigate data quality; check for data loads or processing errors",
                )

            return None
        except Exception as e:
            logger.error(f"Error detecting row count spike: {e}")
            return None

    async def detect_null_increase(
        self, table_id: UUID, lookback_days: int = 30
    ) -> List[Anomaly]:
        """
        Detect columns where null % has increased.

        Args:
            table_id: Table ID
            lookback_days: Days to look back

        Returns:
            List of anomalies
        """
        anomalies = []

        try:
            # Get columns
            columns = await self.db.scalars(
                select(CatalogColumn).where(CatalogColumn.table_id == table_id)
            )

            for column in columns:
                # Get historical profiles for this column
                cutoff_date = datetime.utcnow() - timedelta(days=lookback_days)
                profiles = await self.db.scalars(
                    select(DataProfile)
                    .where(
                        and_(
                            DataProfile.table_id == table_id,
                            DataProfile.created_at >= cutoff_date,
                        )
                    )
                    .order_by(DataProfile.created_at)
                )
                profiles_list = list(profiles)

                if len(profiles_list) < 2:
                    continue

                # Extract null pct from JSON profile
                null_pcts = []
                for p in profiles_list:
                    if p.profile_data and isinstance(p.profile_data, dict):
                        for col_profile in p.profile_data.get("columns", []):
                            if col_profile.get("name") == column.name:
                                null_pcts.append(col_profile.get("null_percentage", 0))
                                break

                if len(null_pcts) < 2:
                    continue

                baseline_null = null_pcts[0]
                current_null = null_pcts[-1]

                # Detect increase
                if current_null > baseline_null and (current_null - baseline_null) > 10:
                    deviation_pct = ((current_null - baseline_null) / baseline_null * 100) if baseline_null > 0 else 100

                    severity = "high" if current_null > 50 else "medium" if current_null > 25 else "low"

                    anomalies.append(
                        Anomaly(
                            id=f"null_increase_{column.id}_{datetime.utcnow().timestamp()}",
                            table_id=table_id,
                            column_id=column.id,
                            anomaly_type="null_increase",
                            severity=severity,
                            detected_at=datetime.utcnow(),
                            baseline_value=baseline_null,
                            current_value=current_null,
                            deviation_pct=deviation_pct,
                            description=f"Column '{column.name}' null % increased from {baseline_null:.1f}% to {current_null:.1f}%",
                            suggested_action="Review data quality; check for missing values or ETL issues",
                        )
                    )

            return anomalies
        except Exception as e:
            logger.error(f"Error detecting null increase: {e}")
            return []

    async def detect_cardinality_shift(
        self, table_id: UUID, lookback_days: int = 30
    ) -> List[Anomaly]:
        """
        Detect columns where distinct value count has shifted.

        Args:
            table_id: Table ID
            lookback_days: Days to look back

        Returns:
            List of anomalies
        """
        anomalies = []

        try:
            columns = await self.db.scalars(
                select(CatalogColumn).where(CatalogColumn.table_id == table_id)
            )

            for column in columns:
                cutoff_date = datetime.utcnow() - timedelta(days=lookback_days)
                profiles = await self.db.scalars(
                    select(DataProfile)
                    .where(
                        and_(
                            DataProfile.table_id == table_id,
                            DataProfile.created_at >= cutoff_date,
                        )
                    )
                    .order_by(DataProfile.created_at)
                )
                profiles_list = list(profiles)

                if len(profiles_list) < 2:
                    continue

                # Extract cardinality from JSON profile
                cardinalities = []
                for p in profiles_list:
                    if p.profile_data and isinstance(p.profile_data, dict):
                        for col_profile in p.profile_data.get("columns", []):
                            if col_profile.get("name") == column.name:
                                cardinalities.append(col_profile.get("distinct_count", 0))
                                break

                if len(cardinalities) < 2:
                    continue

                baseline_card = cardinalities[0]
                current_card = cardinalities[-1]

                # Detect stalled growth (dimension should grow over time)
                if baseline_card > 0 and current_card == baseline_card:
                    days_stalled = (profiles_list[-1].created_at - profiles_list[0].created_at).days
                    if days_stalled > 7:  # Stalled for >7 days
                        anomalies.append(
                            Anomaly(
                                id=f"cardinality_stall_{column.id}_{datetime.utcnow().timestamp()}",
                                table_id=table_id,
                                column_id=column.id,
                                anomaly_type="cardinality_shift",
                                severity="warning",
                                detected_at=datetime.utcnow(),
                                baseline_value=baseline_card,
                                current_value=current_card,
                                deviation_pct=0,
                                description=f"Column '{column.name}' cardinality stalled at {current_card} values",
                                suggested_action="Check if dimension table stopped being updated",
                            )
                        )

                # Detect sudden drop
                if baseline_card > 0 and current_card < baseline_card * 0.8:
                    drop_pct = ((baseline_card - current_card) / baseline_card) * 100

                    anomalies.append(
                        Anomaly(
                            id=f"cardinality_drop_{column.id}_{datetime.utcnow().timestamp()}",
                            table_id=table_id,
                            column_id=column.id,
                            anomaly_type="cardinality_shift",
                            severity="high",
                            detected_at=datetime.utcnow(),
                            baseline_value=baseline_card,
                            current_value=current_card,
                            deviation_pct=-drop_pct,
                            description=f"Column '{column.name}' cardinality dropped {drop_pct:.1f}% from {baseline_card} to {current_card}",
                            suggested_action="Investigate data quality; check for data deletions or purging",
                        )
                    )

            return anomalies
        except Exception as e:
            logger.error(f"Error detecting cardinality shift: {e}")
            return []

    async def detect_freshness_delay(self, table_id: UUID) -> Optional[Anomaly]:
        """
        Detect if table update is delayed beyond expected frequency.

        Args:
            table_id: Table ID

        Returns:
            Anomaly if detected, None otherwise
        """
        try:
            table = await self.db.scalar(
                select(CatalogTable).where(CatalogTable.id == table_id)
            )
            if not table:
                return None

            # Get current profile
            current_profile = await self.db.scalar(
                select(DataProfile)
                .where(DataProfile.table_id == table_id)
                .order_by(desc(DataProfile.created_at))
                .limit(1)
            )

            if not current_profile or not current_profile.last_updated:
                return None

            # Calculate time since update
            time_since_update = datetime.utcnow() - current_profile.last_updated
            hours_since_update = time_since_update.total_seconds() / 3600

            # Estimate expected frequency (default: daily)
            expected_frequency_hours = 24

            if current_profile.profile_data and isinstance(current_profile.profile_data, dict):
                freq = current_profile.profile_data.get("update_frequency_hours")
                if freq:
                    expected_frequency_hours = freq

            # Detect delay
            if hours_since_update > expected_frequency_hours * 2:
                days_delayed = hours_since_update / 24
                severity = "critical" if days_delayed > 7 else "high" if days_delayed > 3 else "medium"

                return Anomaly(
                    id=f"freshness_delay_{table_id}_{datetime.utcnow().timestamp()}",
                    table_id=table_id,
                    anomaly_type="freshness_delay",
                    severity=severity,
                    detected_at=datetime.utcnow(),
                    baseline_value=expected_frequency_hours,
                    current_value=hours_since_update,
                    deviation_pct=((hours_since_update - expected_frequency_hours) / expected_frequency_hours) * 100,
                    description=f"Table should update every {expected_frequency_hours}h but hasn't updated in {days_delayed:.1f} days",
                    suggested_action="Check ETL/data pipeline status; verify table is being updated",
                )

            return None
        except Exception as e:
            logger.error(f"Error detecting freshness delay: {e}")
            return None

    # ============================================================================
    # HELPER METHODS
    # ============================================================================

    def _calculate_severity_from_deviation(self, deviation_pct: float) -> str:
        """Calculate severity based on deviation %."""
        if deviation_pct < 50:
            return "low"
        if deviation_pct < 100:
            return "medium"
        if deviation_pct < 200:
            return "high"
        return "critical"

    @staticmethod
    def _format_number(num: int) -> str:
        """Format large numbers in human-readable format."""
        if num >= 1_000_000:
            return f"{num / 1_000_000:.1f}M"
        if num >= 1_000:
            return f"{num / 1_000:.1f}K"
        return str(num)
