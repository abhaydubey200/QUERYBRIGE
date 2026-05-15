from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.endpoints import (
    auth, connections, ai, catalog, dashboards, 
    websocket, health, semantic, notebooks, 
    governance, monitoring, workspaces, plugins, ai_schema, storage
)
from app.core.metrics import get_metrics
from app.core.env_validator import validate_environment
from app.connectors.connector_factory import ConnectorFactory
from fastapi import Request
from fastapi.responses import JSONResponse
from loguru import logger
import traceback
import uuid
import time
from starlette.types import ASGIApp, Scope, Receive, Send
from app.core.metrics import HTTP_REQUESTS_TOTAL, HTTP_REQUEST_DURATION

# Validate environment before startup
settings = validate_environment()

app = FastAPI(
    title="QueryBridge Enterprise API", 
    version="2.1.0",
    description="The central intelligence hub for the QueryBridge Analytics OS."
)

# ═══════════════════════════════════════════════════════════════
# CORS — MUST be outermost middleware. Added FIRST so it wraps everything.
# ═══════════════════════════════════════════════════════════════
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["X-Trace-ID", "Content-Type", "Authorization"],
)

# ═══════════════════════════════════════════════════════════════
# Global Exception Handler — catches ANY unhandled exception
# ═══════════════════════════════════════════════════════════════
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    trace_id = str(uuid.uuid4())
    logger.error(f"[{trace_id}] Unhandled exception on {request.url.path}: {str(exc)}")
    logger.error(traceback.format_exc())
    return JSONResponse(
        status_code=500,
        content={
            "success": False,
            "data": None,
            "error": {
                "code": "INTERNAL_SERVER_ERROR",
                "message": f"Internal error: {str(exc)}",
                "trace_id": trace_id,
            }
        }
    )

# ═══════════════════════════════════════════════════════════════
# Metrics middleware — simple request counting
# ═══════════════════════════════════════════════════════════════
@app.middleware("http")
async def metrics_middleware(request: Request, call_next):
    start = time.time()
    try:
        response = await call_next(request)
        duration = time.time() - start
        try:
            HTTP_REQUESTS_TOTAL.labels(
                method=request.method, endpoint=request.url.path, status=str(response.status_code)
            ).inc()
            HTTP_REQUEST_DURATION.labels(
                method=request.method, endpoint=request.url.path
            ).observe(duration)
        except Exception:
            pass  # Never let metrics crash a request
        response.headers["X-Trace-ID"] = str(uuid.uuid4())
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        return response
    except Exception as exc:
        logger.error(f"Middleware caught exception: {str(exc)}")
        return JSONResponse(
            status_code=500,
            content={
                "success": False,
                "data": None,
                "error": {
                    "code": "MIDDLEWARE_ERROR",
                    "message": str(exc),
                    "trace_id": str(uuid.uuid4()),
                }
            }
        )

# ═══════════════════════════════════════════════════════════════
# Startup — ensure all database tables exist
# ═══════════════════════════════════════════════════════════════
@app.on_event("startup")
async def startup_ensure_tables():
    """Create any missing tables on startup as a safety net."""
    from app.db.session import engine, Base
    # Import all models so they're registered with Base.metadata
    import app.models.models  # noqa
    import app.models.catalog_models  # noqa
    try:
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        logger.info("Database tables verified/created successfully")
    except Exception as e:
        logger.error(f"Table creation failed (non-fatal): {str(e)}")

# ═══════════════════════════════════════════════════════════════
# Feature Activation — Route Registration
# ═══════════════════════════════════════════════════════════════
app.include_router(auth.router, prefix="/api/v1/auth", tags=["Security"])
app.include_router(connections.router, prefix="/api/v1/connections", tags=["Infrastructure"])
app.include_router(ai.router, prefix="/api/v1/ai", tags=["Intelligence"])
app.include_router(ai_schema.router, tags=["AI Schema & Search"])
app.include_router(catalog.router, prefix="/api/v1/catalog", tags=["Data Catalog"])
app.include_router(dashboards.router, prefix="/api/v1/dashboards", tags=["Analytics"])
app.include_router(semantic.router, prefix="/api/v1/semantic", tags=["Semantic Layer"])
app.include_router(notebooks.router, prefix="/api/v1/notebooks", tags=["Data Science"])
app.include_router(governance.router, prefix="/api/v1/governance", tags=["Compliance"])
app.include_router(monitoring.router, prefix="/api/v1/monitoring", tags=["Observability"])
app.include_router(workspaces.router, prefix="/api/v1/workspaces", tags=["Tenancy"])
app.include_router(plugins.router, prefix="/api/v1/plugins", tags=["Extensions"])
app.include_router(websocket.router, prefix="/api/v1/ws", tags=["Streaming"])
app.include_router(storage.router, prefix="/api/v1/storage", tags=["Storage"])
app.include_router(health.router, prefix="/api/v1/health", tags=["Lifecycle"])

@app.get("/metrics")
async def metrics():
    return get_metrics()

@app.get("/")
async def root():
    return {
        "status": "QueryBridge Enterprise Activated",
        "version": "2.1.0",
        "runtime": "Production-Ready"
    }

@app.on_event("shutdown")
async def shutdown_connectors():
    await ConnectorFactory.cleanup()
