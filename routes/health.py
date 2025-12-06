"""
Enhanced Health Check Endpoints

This module provides comprehensive health check endpoints for monitoring:
- Overall system health
- Database connectivity and performance
- Cache availability (Redis)
- AI service availability
- WebSocket connections
- Disk space
- Memory usage

Author: Chat System Team
Date: 2025-12-06
"""

import time
from typing import Dict, Optional

import psutil
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel

from config.settings import settings
from database.connection import check_database_health

router = APIRouter(prefix="/health", tags=["health"])


class HealthStatus(BaseModel):
    """Health status model"""

    status: str  # "healthy", "degraded", "unhealthy"
    timestamp: float
    version: str
    environment: str


class ComponentHealth(BaseModel):
    """Individual component health model"""

    status: str
    message: Optional[str] = None
    details: Optional[Dict] = None


class DetailedHealthResponse(BaseModel):
    """Detailed health check response model"""

    status: str
    timestamp: float
    app: Dict
    components: Dict[str, ComponentHealth]
    metrics: Optional[Dict] = None


@router.get("", response_model=HealthStatus, summary="Basic Health Check")
async def health_check():
    """
    Basic health check endpoint

    Returns minimal health status for load balancer health checks
    """
    return HealthStatus(
        status="healthy",
        timestamp=time.time(),
        version=settings.APP_VERSION,
        environment=settings.APP_ENVIRONMENT,
    )


@router.get("/liveness", summary="Kubernetes Liveness Probe")
async def liveness_probe():
    """
    Liveness probe for Kubernetes

    Indicates if the application is running (not deadlocked)
    Returns 200 if alive, 503 otherwise
    """
    return {"status": "alive", "timestamp": time.time()}


@router.get("/readiness", summary="Kubernetes Readiness Probe")
async def readiness_probe():
    """
    Readiness probe for Kubernetes

    Indicates if the application is ready to receive traffic
    Checks database connectivity
    """
    try:
        # Check database
        db_health = check_database_health()

        if db_health.get("status") != "healthy":
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Database not healthy",
            )

        return {
            "status": "ready",
            "timestamp": time.time(),
            "checks": {"database": "healthy"},
        }

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Not ready: {str(e)}",
        )


@router.get("/detailed", response_model=DetailedHealthResponse, summary="Detailed Health Check")
async def detailed_health_check():
    """
    Comprehensive health check with all components

    Returns detailed status of:
    - Database
    - Cache (Redis)
    - AI Services
    - WebSocket
    - System Resources
    """
    components = {}
    overall_status = "healthy"

    # Check Database
    try:
        db_health = check_database_health()
        components["database"] = ComponentHealth(
            status=db_health.get("status", "unknown"),
            details={
                "type": db_health.get("type"),
                "version": db_health.get("version"),
            },
        )
        if db_health.get("status") != "healthy":
            overall_status = "degraded"
    except Exception as e:
        components["database"] = ComponentHealth(status="unhealthy", message=str(e))
        overall_status = "unhealthy"

    # Check Redis Cache
    try:
        cache_status = await _check_redis_health()
        components["cache"] = cache_status
        if cache_status.status != "healthy":
            overall_status = "degraded"
    except Exception as e:
        components["cache"] = ComponentHealth(status="unknown", message=str(e))

    # Check AI Service
    try:
        ai_status = await _check_ai_service_health()
        components["ai_service"] = ai_status
        if ai_status.status != "healthy":
            # AI service is optional, so only degrade if it's expected to be available
            if settings.AI_ENABLED:
                overall_status = "degraded"
    except Exception as e:
        components["ai_service"] = ComponentHealth(status="unknown", message=str(e))

    # Check WebSocket
    components["websocket"] = ComponentHealth(
        status="healthy" if settings.WEBSOCKET_ENABLED else "disabled",
        details={"enabled": settings.WEBSOCKET_ENABLED},
    )

    # Get system metrics
    metrics = _get_system_metrics()

    # Check system resources
    if metrics:
        # Disk space warning
        if metrics.get("disk_usage_percent", 0) > 90:
            overall_status = "degraded"
            components["disk"] = ComponentHealth(
                status="warning",
                message="Disk usage above 90%",
                details={"usage_percent": metrics["disk_usage_percent"]},
            )
        else:
            components["disk"] = ComponentHealth(
                status="healthy",
                details={"usage_percent": metrics["disk_usage_percent"]},
            )

        # Memory warning
        if metrics.get("memory_usage_percent", 0) > 90:
            overall_status = "degraded"
            components["memory"] = ComponentHealth(
                status="warning",
                message="Memory usage above 90%",
                details={"usage_percent": metrics["memory_usage_percent"]},
            )
        else:
            components["memory"] = ComponentHealth(
                status="healthy",
                details={"usage_percent": metrics["memory_usage_percent"]},
            )

    return DetailedHealthResponse(
        status=overall_status,
        timestamp=time.time(),
        app={
            "name": settings.APP_NAME,
            "version": settings.APP_VERSION,
            "environment": settings.APP_ENVIRONMENT,
        },
        components=components,
        metrics=metrics,
    )


async def _check_redis_health() -> ComponentHealth:
    """Check Redis cache health"""
    try:
        # Try to import redis
        import redis

        # Try to connect
        r = redis.Redis(
            host=getattr(settings, "REDIS_HOST", "localhost"),
            port=getattr(settings, "REDIS_PORT", 6379),
            socket_timeout=2,
            socket_connect_timeout=2,
        )

        # Ping Redis
        r.ping()

        return ComponentHealth(status="healthy", message="Redis responding")

    except ImportError:
        return ComponentHealth(status="disabled", message="Redis client not installed")
    except Exception as e:
        return ComponentHealth(status="unhealthy", message=f"Redis error: {str(e)}")


async def _check_ai_service_health() -> ComponentHealth:
    """Check AI service health"""
    if not settings.AI_ENABLED:
        return ComponentHealth(status="disabled", message="AI service disabled")

    try:
        # Try to check Ollama health if configured
        if settings.OLLAMA_BASE_URL:
            import httpx

            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.get(f"{settings.OLLAMA_BASE_URL}/api/tags")
                if response.status_code == 200:
                    return ComponentHealth(
                        status="healthy",
                        message="Ollama responding",
                        details={"url": settings.OLLAMA_BASE_URL},
                    )
                else:
                    return ComponentHealth(
                        status="unhealthy",
                        message=f"Ollama returned status {response.status_code}",
                    )
        else:
            return ComponentHealth(status="unknown", message="AI service URL not configured")

    except Exception as e:
        return ComponentHealth(status="unhealthy", message=f"AI service error: {str(e)}")


def _get_system_metrics() -> Dict:
    """Get system resource metrics"""
    try:
        # CPU usage
        cpu_percent = psutil.cpu_percent(interval=0.1)

        # Memory usage
        memory = psutil.virtual_memory()

        # Disk usage
        disk = psutil.disk_usage("/")

        # Network IO
        net_io = psutil.net_io_counters()

        return {
            "cpu_usage_percent": cpu_percent,
            "memory_total_gb": round(memory.total / (1024**3), 2),
            "memory_used_gb": round(memory.used / (1024**3), 2),
            "memory_usage_percent": memory.percent,
            "disk_total_gb": round(disk.total / (1024**3), 2),
            "disk_used_gb": round(disk.used / (1024**3), 2),
            "disk_usage_percent": round(disk.percent, 1),
            "network_bytes_sent": net_io.bytes_sent,
            "network_bytes_recv": net_io.bytes_recv,
        }

    except Exception as e:
        return {"error": f"Failed to collect metrics: {str(e)}"}
