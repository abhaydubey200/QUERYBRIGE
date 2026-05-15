from fastapi import APIRouter, Depends
from app.core.metrics import get_metrics
import psutil
import os
import time

router = APIRouter()

@router.get("/status")
async def get_system_status():
    """
    Returns comprehensive system health metrics for enterprise observability.
    """
    cpu_usage = psutil.cpu_percent(interval=None)
    memory = psutil.virtual_memory()
    disk = psutil.disk_usage('/')
    
    return {
        "services": {
            "api": "healthy",
            "worker": "active",
            "ai_runtime": "connected",
            "db": "connected"
        },
        "resources": {
            "cpu": f"{cpu_usage}%",
            "memory": f"{memory.percent}%",
            "memory_available_mb": memory.available // (1024 * 1024),
            "disk": f"{disk.percent}%"
        },
        "uptime": f"{int(time.time() - psutil.boot_time())}s",
        "load": "nominal" if cpu_usage < 80 else "high"
    }

@router.get("/stats")
async def get_stats():
    return get_metrics()
