from typing import Dict, Any

class PromptRegistry:
    """Centralized management for versioned system prompts."""
    
    _prompts = {
        "sql_generation": {
            "v1": "Generate SQL for {schema}.",
            "v2": "You are an expert Data Engineer. Given the schema {schema} and semantic metrics {metrics}, generate an optimized SQL query. Explain your reasoning and confidence level."
        },
        "semantic_resolver": {
            "v1": "Map {nl} to {entities}."
        },
        "ai_analyst": {
            "v1": "Analyze this data: {data}. Focus on {metric}."
        }
    }

    @classmethod
    def get_prompt(cls, task: str, version: str = "v2") -> str:
        return cls._prompts.get(task, {}).get(version, "Invalid Prompt Task/Version")

    @classmethod
    def list_versions(cls, task: str):
        return list(cls._prompts.get(task, {}).keys())
