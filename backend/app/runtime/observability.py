import time
from typing import Dict, Any, List
from loguru import logger
import psutil
import os

class ObservabilityManager:
    """
    Enterprise runtime observability and telemetry manager.
    Tracks performance metrics, error intelligence, and system pressure.
    """
    def __init__(self):
        self.start_time = time.time()
        self.query_counts = 0
        self.error_counts = 0
        self.latency_samples: List[float] = []

    def log_query(self, duration: float, success: bool = True):
        self.query_counts += 1
        if not success:
            self.error_counts += 1
        self.latency_samples.append(duration)
        # Keep window of last 1000 samples
        if len(self.latency_samples) > 1000:
            self.latency_samples.pop(0)

    def get_runtime_metrics(self) -> Dict[str, Any]:
        avg_latency = sum(self.latency_samples) / len(self.latency_samples) if self.latency_samples else 0
        
        return {
            "uptime_seconds": int(time.time() - self.start_time),
            "throughput": {
                "total_queries": self.query_counts,
                "error_rate": (self.error_counts / self.query_counts * 100) if self.query_counts > 0 else 0,
                "avg_latency_ms": int(avg_latency * 1000)
            },
            "system_pressure": {
                "cpu_percent": psutil.cpu_percent(),
                "memory_usage_mb": int(psutil.Process(os.getpid()).memory_info().rss / 1024 / 1024),
                "active_threads": psutil.Process(os.getpid()).num_threads()
            },
            "status": "HEALTHY" if self.error_counts < (self.query_counts * 0.1) else "DEGRADED"
        }

    def log_error_with_context(self, error: Exception, context: Dict[str, Any]):
        """
        Deep error intelligence with contextual breadcrumbs.
        """
        error_report = {
            "error_type": type(error).__name__,
            "message": str(error),
            "context": context,
            "timestamp": time.time(),
            "process_id": os.getpid()
        }
        logger.error(f"RUNTIME_ERROR: {error_report}")
        # In prod, this would push to Sentry/Elasticsearch
        return error_report

# Global singleton for easy access across routers
telemetry = ObservabilityManager()
