from typing import List, Dict, Any

class ContextOptimizer:
    """Enterprise-grade context management for reducing hallucinations and costs."""
    
    def __init__(self, token_limit: int = 4096):
        self.token_limit = token_limit

    def rank_entities(self, query: str, entities: List[Dict]) -> List[Dict]:
        """Simple keyword-based relevance ranking for entities."""
        keywords = set(query.lower().split())
        scored_entities = []
        
        for entity in entities:
            score = 0
            name_parts = entity.get("name", "").lower().split("_")
            score += len(keywords.intersection(name_parts)) * 10
            
            # Boost if used in recent queries
            if entity.get("last_used"):
                score += 5
                
            scored_entities.append((score, entity))
        
        # Sort by score descending
        scored_entities.sort(key=lambda x: x[0], reverse=True)
        return [e[1] for e in scored_entities]

    def optimize_context(self, system_prompt: str, user_query: str, schema_data: str) -> str:
        """Truncate and optimize context to fit token budget."""
        # Note: In production, use tiktoken for precise counting
        total_len = len(system_prompt) + len(user_query) + len(schema_data)
        
        if total_len > self.token_limit * 4: # Crude approximation
            # Priority: System > User > Schema
            available_schema_len = (self.token_limit * 4) - len(system_prompt) - len(user_query)
            schema_data = schema_data[:max(0, available_schema_len)]
            
        return schema_data

class SchemaSummarizer:
    """Summarizes DB schema into an LLM-optimized compact format."""
    
    def summarize(self, tables: List[Dict]) -> str:
        summary = []
        for table in tables:
            cols = [f"{c['name']} ({c['type']})" for c in table['columns'][:10]]
            summary.append(f"Table {table['name']}: {', '.join(cols)}")
        return "\n".join(summary)
