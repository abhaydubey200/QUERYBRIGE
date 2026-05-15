from app.services.ai_service import AIService
from app.semantic.metric_registry import SemanticRegistry
from sqlalchemy.ext.asyncio import AsyncSession
import json

class SemanticResolver:
    def __init__(self, db: AsyncSession, ai_service: AIService):
        self.db = db
        self.ai_service = ai_service
        self.registry = SemanticRegistry(db)

    async def resolve_query(self, natural_language: str, connection_id: str):
        # 1. Fetch available metrics and dimensions
        metrics = await self.registry.get_metrics(connection_id)
        dimensions = await self.registry.get_dimensions(connection_id)

        # 2. Build context for AI
        context = {
            "metrics": [{"name": m.name, "formula": m.formula, "desc": m.description} for m in metrics],
            "dimensions": [{"name": d.name, "column": d.column_name, "table": d.table_name} for d in dimensions]
        }

        prompt = f"""
        Given the following semantic layer definitions:
        {json.dumps(context, indent=2)}

        Resolve the following natural language request:
        "{natural_language}"

        Return a JSON object with:
        - "resolved_metrics": list of metric names
        - "resolved_dimensions": list of dimension names
        - "filters": list of suspected filters (dimension, operator, value)
        - "time_grain": e.g. "daily", "monthly", "quarterly" or null
        - "reasoning": why you chose these
        """

        # AI processing with safety grounding
        response = await self.ai_service.generate_sql(prompt, "{}") 
        
        return response
