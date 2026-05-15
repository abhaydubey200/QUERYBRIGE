import os
import httpx
from typing import List, Dict, Any
from loguru import logger

class AIService:
    def __init__(self):
        self.api_key = os.getenv("NVIDIA_API_KEY")
        self.base_url = "https://integrate.api.nvidia.com/v1"
        self.model = "nvidia/qwen2-7b-instruct"

    async def _call_llm(self, messages: List[Dict[str, str]]) -> str:
        if not self.api_key:
            return "AI Error: NVIDIA_API_KEY not configured."

        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(
                    f"{self.base_url}/chat/completions",
                    headers={
                        "Authorization": f"Bearer {self.api_key}",
                        "Content-Type": "application/json"
                    },
                    json={
                        "model": self.model,
                        "messages": messages,
                        "temperature": 0.2,
                        "max_tokens": 1024
                    },
                    timeout=30.0
                )
                response.raise_for_status()
                return response.json()["choices"][0]["message"]["content"]
            except Exception as e:
                logger.error(f"AI API call failed: {str(e)}")
                return f"AI Error: {str(e)}"

    async def generate_sql(self, schema_context: str, natural_language: str) -> str:
        system_prompt = f"""
        You are an expert SQL engineer.
        Target Database: PostgreSQL
        Schema Context:
        {schema_context}
        
        Rules:
        1. Return ONLY the SQL query.
        2. No markdown formatting.
        3. No explanations.
        4. Use best practices (indexing, limit).
        """
        user_prompt = f"Generate a SQL query for: {natural_language}"
        messages = [{"role": "system", "content": system_prompt}, {"role": "user", "content": user_prompt}]
        return await self._call_llm(messages)

    async def analyze_query(self, sql: str, schema_context: str) -> Dict[str, Any]:
        """
        Analyzes a SQL query for performance anti-patterns and risk.
        """
        system_prompt = f"""
        You are a Database Performance Engineer.
        Analyze the provided SQL for anti-patterns and performance risks.
        Schema: {schema_context}
        
        Return a JSON object with:
        1. performance_score (0-100)
        2. risk_score (0-100)
        3. anti_patterns (list of strings)
        4. recommendations (list of strings)
        5. estimated_impact (low/medium/high)
        """
        messages = [{"role": "system", "content": system_prompt}, {"role": "user", "content": f"Analyze this SQL: {sql}"}]
        
        from app.services.ai_json_recovery import AIJsonRecovery
        raw_response = await self._call_llm(messages)
        return AIJsonRecovery.extract_json(raw_response) or {"error": "Recovery failed"}
