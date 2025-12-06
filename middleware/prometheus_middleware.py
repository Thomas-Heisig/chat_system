"""
Prometheus Metrics Middleware for FastAPI

This module provides comprehensive metrics collection for the application:
- Request duration and counts
- HTTP status code tracking
- Active connections
- Database query performance
- Cache hit/miss rates
- WebSocket connection tracking

Author: Chat System Team
Date: 2025-12-06
"""

from typing import Callable

from fastapi import Request, Response
from prometheus_client import (
    Counter,
    Gauge,
    Histogram,
    Info,
    generate_latest,
)
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response as StarletteResponse

from config.settings import settings

# Application info
app_info = Info("chat_system_app", "Application information")
app_info.info(
    {
        "version": settings.APP_VERSION,
        "environment": settings.APP_ENVIRONMENT,
        "name": settings.APP_NAME,
    }
)

# HTTP Request Metrics
http_requests_total = Counter(
    "http_requests_total",
    "Total HTTP requests",
    ["method", "endpoint", "status"],
)

http_request_duration_seconds = Histogram(
    "http_request_duration_seconds",
    "HTTP request duration in seconds",
    ["method", "endpoint"],
    buckets=(0.01, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0),
)

http_requests_in_progress = Gauge(
    "http_requests_in_progress",
    "Number of HTTP requests currently being processed",
    ["method", "endpoint"],
)

# Application Metrics
websocket_connections_active = Gauge(
    "websocket_connections_active", "Number of active WebSocket connections"
)

database_connections_active = Gauge(
    "database_connections_active", "Number of active database connections"
)

database_query_duration_seconds = Histogram(
    "database_query_duration_seconds",
    "Database query duration in seconds",
    ["operation"],
    buckets=(0.001, 0.005, 0.01, 0.05, 0.1, 0.5, 1.0, 5.0),
)

# Cache Metrics
cache_hits_total = Counter("cache_hits_total", "Total cache hits", ["cache_type"])

cache_misses_total = Counter("cache_misses_total", "Total cache misses", ["cache_type"])

# AI/RAG Metrics
ai_requests_total = Counter("ai_requests_total", "Total AI requests", ["model", "status"])

ai_request_duration_seconds = Histogram(
    "ai_request_duration_seconds",
    "AI request duration in seconds",
    ["model"],
    buckets=(0.1, 0.5, 1.0, 2.0, 5.0, 10.0, 30.0, 60.0),
)

rag_queries_total = Counter("rag_queries_total", "Total RAG queries", ["vector_db", "status"])

# File Upload Metrics
file_uploads_total = Counter("file_uploads_total", "Total file uploads", ["status", "file_type"])

file_upload_size_bytes = Histogram(
    "file_upload_size_bytes",
    "File upload size in bytes",
    buckets=(1024, 10240, 102400, 1048576, 10485760, 104857600),
)

# Error Metrics
errors_total = Counter(
    "errors_total",
    "Total errors",
    ["error_type", "endpoint"],
)


class PrometheusMiddleware(BaseHTTPMiddleware):
    """
    Middleware to collect Prometheus metrics for all HTTP requests
    """

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """
        Process the request and collect metrics

        Args:
            request: The incoming request
            call_next: The next middleware/route handler

        Returns:
            Response from the application
        """
        # Skip metrics collection for the metrics endpoint itself
        if request.url.path == "/metrics":
            return await call_next(request)

        method = request.method
        endpoint = request.url.path

        # Track in-progress requests
        http_requests_in_progress.labels(method=method, endpoint=endpoint).inc()

        try:
            # Measure request duration
            with http_request_duration_seconds.labels(method=method, endpoint=endpoint).time():
                response = await call_next(request)

            # Record request completion
            http_requests_total.labels(
                method=method, endpoint=endpoint, status=response.status_code
            ).inc()

            return response

        except Exception as e:
            # Record error
            errors_total.labels(error_type=type(e).__name__, endpoint=endpoint).inc()
            raise

        finally:
            # Decrement in-progress counter
            http_requests_in_progress.labels(method=method, endpoint=endpoint).dec()


async def metrics_endpoint(request: Request) -> StarletteResponse:
    """
    Endpoint to expose Prometheus metrics

    Args:
        request: The incoming request

    Returns:
        Response with Prometheus metrics in text format
    """
    metrics = generate_latest()
    return StarletteResponse(
        content=metrics,
        media_type="text/plain; version=0.0.4; charset=utf-8",
    )


# Helper functions for tracking custom metrics
def track_websocket_connection(connected: bool):
    """Track WebSocket connection changes"""
    if connected:
        websocket_connections_active.inc()
    else:
        websocket_connections_active.dec()


def track_database_query(operation: str, duration: float):
    """Track database query performance"""
    database_query_duration_seconds.labels(operation=operation).observe(duration)


def track_cache_operation(cache_type: str, hit: bool):
    """Track cache hits and misses"""
    if hit:
        cache_hits_total.labels(cache_type=cache_type).inc()
    else:
        cache_misses_total.labels(cache_type=cache_type).inc()


def track_ai_request(model: str, duration: float, success: bool):
    """Track AI request metrics"""
    status = "success" if success else "failure"
    ai_requests_total.labels(model=model, status=status).inc()
    ai_request_duration_seconds.labels(model=model).observe(duration)


def track_rag_query(vector_db: str, success: bool):
    """Track RAG query metrics"""
    status = "success" if success else "failure"
    rag_queries_total.labels(vector_db=vector_db, status=status).inc()


def track_file_upload(success: bool, file_type: str, size_bytes: int):
    """Track file upload metrics"""
    status = "success" if success else "failure"
    file_uploads_total.labels(status=status, file_type=file_type).inc()
    if success:
        file_upload_size_bytes.observe(size_bytes)


def track_database_connections(count: int):
    """Update active database connections gauge"""
    database_connections_active.set(count)
