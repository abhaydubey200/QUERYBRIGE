import asyncio
import logging
from typing import Dict, List, Any
from enum import Enum

class ServiceStatus(Enum):
    STARTING = "starting"
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"
    STOPPED = "stopped"

class RuntimeSupervisor:
    """Enterprise-grade supervisor for managing platform micro-services."""
    
    def __init__(self):
        self.services: Dict[str, Dict] = {}
        self.logger = logging.getLogger("QueryBridge.Runtime")
        self.is_running = False

    def register_service(self, name: str, service_obj: Any, dependencies: List[str] = None):
        self.services[name] = {
            "instance": service_obj,
            "dependencies": dependencies or [],
            "status": ServiceStatus.STOPPED,
            "restarts": 0,
            "last_heartbeat": None
        }
        self.logger.info(f"Registered service: {name}")

    async def start_all(self):
        self.is_running = True
        # Simple dependency-aware startup
        started = set()
        while len(started) < len(self.services):
            for name, meta in self.services.items():
                if name in started: continue
                
                if all(dep in started for dep in meta["dependencies"]):
                    self.logger.info(f"Starting service: {name}")
                    meta["status"] = ServiceStatus.STARTING
                    try:
                        if hasattr(meta["instance"], "start"):
                            await meta["instance"].start()
                        meta["status"] = ServiceStatus.HEALTHY
                        started.add(name)
                    except Exception as e:
                        self.logger.error(f"Failed to start {name}: {e}")
                        meta["status"] = ServiceStatus.UNHEALTHY
            await asyncio.sleep(0.1)

    async def monitor_loop(self):
        """Continuous health monitoring and auto-recovery."""
        while self.is_running:
            for name, meta in self.services.items():
                try:
                    if hasattr(meta["instance"], "check_health"):
                        is_healthy = await meta["instance"].check_health()
                        meta["status"] = ServiceStatus.HEALTHY if is_healthy else ServiceStatus.DEGRADED
                except Exception:
                    meta["status"] = ServiceStatus.UNHEALTHY
                    await self._recover_service(name)
            await asyncio.sleep(5)

    async def _recover_service(self, name: str):
        meta = self.services[name]
        if meta["restarts"] > 5:
            self.logger.critical(f"Service {name} reached max restarts. Disabling.")
            return

        self.logger.warning(f"Recovering service: {name}")
        meta["restarts"] += 1
        try:
            if hasattr(meta["instance"], "start"):
                await meta["instance"].start()
            meta["status"] = ServiceStatus.HEALTHY
        except Exception as e:
            self.logger.error(f"Recovery failed for {name}: {e}")

    def get_system_health(self) -> Dict:
        return {name: meta["status"].value for name, meta in self.services.items()}
