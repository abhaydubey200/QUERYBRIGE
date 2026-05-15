import psutil
import logging
from typing import Dict

class MemoryBudgetManager:
    """Enterprise-grade memory governor to prevent OOM on local machines."""
    
    def __init__(self, system_limit_percent: float = 80.0):
        self.limit_percent = system_limit_percent
        self.component_usage: Dict[str, float] = {}

    def can_allocate(self, component: str, requested_mb: float) -> bool:
        """Checks if the system has enough memory to allow an operation."""
        current_mem = psutil.virtual_memory()
        if current_mem.percent > self.limit_percent:
            logging.warning(f"Memory limit reached: {current_mem.percent}%")
            return False
            
        # Check component-specific quotas (e.g., Notebooks max 2GB)
        if component == "notebook" and self.component_usage.get("notebook", 0) + requested_mb > 2048:
            return False
            
        return True

    def record_allocation(self, component: str, amount_mb: float):
        self.component_usage[component] = self.component_usage.get(component, 0) + amount_mb

    def release_allocation(self, component: str, amount_mb: float):
        self.component_usage[component] = max(0, self.component_usage.get(component, 0) - amount_mb)

class ConcurrencyController:
    """Limits simultaneous heavy operations (AI, SQL, Python)."""
    
    _limits = {
        "sql_query": 5,
        "ai_request": 3,
        "notebook_cell": 2
    }
    
    _active = {
        "sql_query": 0,
        "ai_request": 0,
        "notebook_cell": 0
    }

    @classmethod
    def acquire(cls, op_type: str) -> bool:
        if cls._active.get(op_type, 0) < cls._limits.get(op_type, 10):
            cls._active[op_type] = cls._active.get(op_type, 0) + 1
            return True
        return False

    @classmethod
    def release(cls, op_type: str):
        cls._active[op_type] = max(0, cls._active.get(op_type, 0) - 1)
