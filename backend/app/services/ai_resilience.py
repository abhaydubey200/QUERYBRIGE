import asyncio
import random
from typing import Callable, Any
from loguru import logger

class AIResilience:
    """
    Handles AI retry logic, circuit breaking, and timeout management.
    """
    def __init__(self, max_retries: int = 3, base_delay: float = 1.0):
        self.max_retries = max_retries
        self.base_delay = base_delay
        self.failure_count = 0
        self.circuit_open = False
        self.last_failure_time = 0

    async def execute_with_retry(self, func: Callable, *args, **kwargs) -> Any:
        if self.circuit_open:
            if asyncio.get_event_loop().time() - self.last_failure_time > 60:
                self.circuit_open = False
                self.failure_count = 0
            else:
                raise Exception("AI Circuit Breaker is OPEN. Please wait.")

        for attempt in range(self.max_retries):
            try:
                return await func(*args, **kwargs)
            except Exception as e:
                self.failure_count += 1
                if self.failure_count >= 5:
                    self.circuit_open = True
                    self.last_failure_time = asyncio.get_event_loop().time()
                
                if attempt == self.max_retries - 1:
                    raise e
                
                delay = self.base_delay * (2 ** attempt) + random.uniform(0, 1)
                logger.warning(f"AI Call failed. Retrying in {delay:.2f}s... (Attempt {attempt + 1})")
                await asyncio.sleep(delay)
