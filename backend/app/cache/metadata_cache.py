import json
from typing import Any, Optional
import redis.asyncio as redis
from loguru import logger
import os

class MetadataCache:
    """
    Enterprise Redis-backed metadata cache.
    """
    
    def __init__(self):
        redis_url = os.getenv("REDIS_URL", "redis://localhost:6379/0")
        self.client = redis.from_url(redis_url, decode_responses=True)
        self.ttl = 3600  # 1 hour default

    async def get(self, key: str) -> Optional[Any]:
        try:
            data = await self.client.get(f"metadata:{key}")
            return json.loads(data) if data else None
        except Exception as e:
            logger.error(f"Cache get error: {str(e)}")
            return None

    async def set(self, key: str, value: Any, ttl: Optional[int] = None):
        try:
            await self.client.set(
                f"metadata:{key}", 
                json.dumps(value), 
                ex=ttl or self.ttl
            )
        except Exception as e:
            logger.error(f"Cache set error: {str(e)}")

    async def invalidate(self, key: str):
        await self.client.delete(f"metadata:{key}")

    async def invalidate_connection(self, connection_id: str):
        """
        Invalidates all cached metadata for a specific connection.
        """
        keys = await self.client.keys(f"metadata:*{connection_id}*")
        if keys:
            await self.client.delete(*keys)
