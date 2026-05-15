from app.services.ai_service import AIService
import json

class AIAnalystService:
    def __init__(self, ai_service: AIService):
        self.ai_service = ai_service

    async def analyze_trend(self, data_summary: str, metric_name: str):
        prompt = f"""
        Analyze the following trend data for the metric '{metric_name}':
        {data_summary}

        Provide a business-grade analysis including:
        1. Key direction (increasing, decreasing, stable)
        2. Magnitude of change
        3. Potential anomalies
        4. Business implication summary
        
        Return in JSON format.
        """
        return await self.ai_service.generate_sql(prompt, "{}")

    async def perform_root_cause(self, target_metric: str, change_value: str, dimension_correlations: str):
        prompt = f"""
        Perform a Root Cause Analysis (RCA) for the change in '{target_metric}'.
        Change: {change_value}
        
        Correlation Data:
        {dimension_correlations}

        Determine the primary drivers of this change.
        Return:
        - "drivers": list of top contributing dimensions/factors
        - "explanation": narrative explanation
        - "confidence": 0-1 score
        """
        return await self.ai_service.generate_sql(prompt, "{}")
