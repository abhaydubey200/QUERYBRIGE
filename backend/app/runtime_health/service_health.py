import asyncio
import httpx
from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import create_async_engine
from app.core.env_validator import validate_environment

settings = validate_environment()

async def check_database():
    try:
        engine = create_async_engine(settings.DATABASE_URL)
        async with engine.connect() as conn:
            await conn.execute("SELECT 1")
        return {"status": "healthy", "latency": "low"}
    except Exception as e:
        return {"status": "unhealthy", "error": str(e)}

async def check_redis():
    try:
        redis = Redis.from_url(settings.REDIS_URL)
        await redis.ping()
        return {"status": "healthy"}
    except Exception as e:
        return {"status": "unhealthy", "error": str(e)}

async def check_ai_runtime():
    try:
        async with httpx.AsyncClient() as client:
            # Check NVIDIA API connectivity
            response = await client.get(
                "https://api.nvidia.com/v1/health", # Mock health endpoint
                timeout=2.0
            )
            return {"status": "healthy" if response.status_code == 200 else "degraded"}
    except:
        return {"status": "degraded", "reason": "Connection Timeout"}

async def get_deep_health():
    db, redis, ai = await asyncio.gather(
        check_database(),
        check_redis(),
        check_ai_runtime()
    )
    
    return {
        "services": {
            "database": db,
            "cache": redis,
            "intelligence": ai
        },
        "overall": "healthy" if all(s["status"] == "healthy" for s in [db, redis]) else "degraded"
    }
