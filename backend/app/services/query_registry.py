from typing import Dict, Any

class QueryRegistry:
    """
    Singleton registry to track active query tasks.
    """
    _instance = None
    _active_queries: Dict[str, Any] = {}

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(QueryRegistry, cls).__new__(cls)
        return cls._instance

    def register(self, task_id: str, metadata: Dict[str, Any]):
        self._active_queries[task_id] = metadata

    def unregister(self, task_id: str):
        if task_id in self._active_queries:
            del self._active_queries[task_id]

    def get_active(self):
        return self._active_queries
