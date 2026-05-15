import time
from prometheus_client import Counter, Histogram, generate_latest, CONTENT_TYPE_LATEST
from starlette.middleware.base import BaseHTTPMiddleware
from fastapi import Request, Response

from prometheus_client import Counter, Histogram, generate_latest, CONTENT_TYPE_LATEST, REGISTRY

def create_counter_safe(name, documentation, labelnames=()):
    try:
        return Counter(name, documentation, labelnames)
    except ValueError:
        # If already registered, return the existing collector
        return REGISTRY._names_to_collectors.get(name)

def create_histogram_safe(name, documentation, labelnames=()):
    try:
        return Histogram(name, documentation, labelnames)
    except ValueError:
        return REGISTRY._names_to_collectors.get(name)

# Metrics definitions
HTTP_REQUESTS_TOTAL = create_counter_safe(
    "querybridge_http_requests_total", 
    "Total HTTP requests", 
    ["method", "endpoint", "status"]
)

HTTP_REQUEST_DURATION = create_histogram_safe(
    "querybridge_http_request_duration_seconds", 
    "HTTP request duration", 
    ["method", "endpoint"]
)

QUERY_EXECUTION_DURATION = create_histogram_safe(
    "querybridge_query_duration_seconds",
    "Database query duration",
    ["connection_id"]
)

AI_FAILURE_COUNT = create_counter_safe(
    "querybridge_ai_failures_total", 
    "Total AI generation failures", 
    ["type"]
)

SEMANTIC_RESOLUTION_TIME = create_histogram_safe(
    "querybridge_semantic_resolution_seconds", 
    "Time taken to resolve semantic queries"
)

QUERY_COST_ESTIMATE = create_counter_safe(
    "querybridge_query_cost_estimate_total", 
    "Estimated cost of executed queries based on row scans"
)

CONNECTION_HEALTH = create_counter_safe(
    "querybridge_connection_health",
    "Database connection health status (1 for online, 0 for offline)",
    ["connection_id", "name", "type"]
)

CONNECTION_LATENCY = create_histogram_safe(
    "querybridge_connection_latency_seconds",
    "Database connection probe latency",
    ["connection_id", "name", "type"]
)

class MetricsMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        start_time = time.time()
        try:
            response = await call_next(request)
            duration = time.time() - start_time
            
            endpoint = request.url.path
            method = request.method
            status = str(response.status_code)
            
            HTTP_REQUESTS_TOTAL.labels(method=method, endpoint=endpoint, status=status).inc()
            HTTP_REQUEST_DURATION.labels(method=method, endpoint=endpoint).observe(duration)
            
            return response
        except Exception:
            # If an exception bubbles up to here, record it as a 500 error
            duration = time.time() - start_time
            HTTP_REQUESTS_TOTAL.labels(method=request.method, endpoint=request.url.path, status="500").inc()
            raise

def get_metrics():
    return Response(content=generate_latest(), media_type=CONTENT_TYPE_LATEST)
