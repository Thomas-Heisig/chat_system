"""
Middleware package for the chat system

This package contains various middleware components for:
- Prometheus metrics collection
- Security headers and CSP
- Response compression
- Request rate limiting
- Error handling and tracking

Author: Chat System Team
Date: 2025-12-06
"""

from .compression_middleware import CompressionMiddleware
from .prometheus_middleware import (
    PrometheusMiddleware,
    metrics_endpoint,
    track_ai_request,
    track_cache_operation,
    track_database_connections,
    track_database_query,
    track_file_upload,
    track_rag_query,
    track_websocket_connection,
)
from .security_middleware import SecurityHeadersMiddleware

__all__ = [
    "PrometheusMiddleware",
    "SecurityHeadersMiddleware",
    "CompressionMiddleware",
    "metrics_endpoint",
    "track_websocket_connection",
    "track_database_query",
    "track_cache_operation",
    "track_ai_request",
    "track_rag_query",
    "track_file_upload",
    "track_database_connections",
]
