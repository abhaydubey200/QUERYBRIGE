from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.models import SemanticMetric, SemanticDimension
from app.semantic.semantic_models import MetricCreate, DimensionCreate
import uuid

class SemanticRegistry:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_metric(self, metric: MetricCreate):
        db_metric = SemanticMetric(
            id=str(uuid.uuid4()),
            name=metric.name,
            description=metric.description,
            formula=metric.formula,
            connection_id=metric.connection_id,
            metadata_json=metric.metadata # Assuming metadata_json based on typical naming
        )
        self.db.add(db_metric)
        await self.db.commit()
        return db_metric

    async def get_metrics(self, connection_id: str):
        result = await self.db.execute(
            select(SemanticMetric).where(SemanticMetric.connection_id == connection_id)
        )
        return result.scalars().all()

    async def create_dimension(self, dimension: DimensionCreate):
        db_dim = SemanticDimension(
            id=str(uuid.uuid4()),
            name=dimension.name,
            description=dimension.description,
            column_name=dimension.column_name,
            table_name=dimension.table_name,
            connection_id=dimension.connection_id
        )
        self.db.add(db_dim)
        await self.db.commit()
        return db_dim

    async def get_dimensions(self, connection_id: str):
        result = await self.db.execute(
            select(SemanticDimension).where(SemanticDimension.connection_id == connection_id)
        )
        return result.scalars().all()
