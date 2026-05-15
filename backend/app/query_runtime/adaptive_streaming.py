import time
from typing import List, Dict

class AdaptiveStreaming:
    """Optimizes chunk sizing based on execution throughput and system load."""
    
    def __init__(self, base_chunk_size: int = 1000):
        self.base_chunk_size = base_chunk_size
        self.history = []

    def calculate_next_chunk_size(self, last_chunk_time: float, current_concurrency: int) -> int:
        """
        Adjust chunk size to maintain low latency.
        If last chunk was slow (> 500ms), decrease size.
        If concurrency is high, decrease size to save memory.
        """
        adjustment = 1.0
        
        # Latency check
        if last_chunk_time > 0.5:
            adjustment -= 0.2
        elif last_chunk_time < 0.1:
            adjustment += 0.1
            
        # Concurrency check
        if current_concurrency > 10:
            adjustment -= 0.3
            
        new_size = int(self.base_chunk_size * adjustment)
        return max(100, min(new_size, 5000))

    def fingerprint_query(self, sql: str) -> str:
        """Create a normalized fingerprint of the SQL query for caching/tracking."""
        import hashlib
        # Basic normalization
        normalized = " ".join(sql.lower().split())
        return hashlib.sha256(normalized.encode()).hexdigest()
