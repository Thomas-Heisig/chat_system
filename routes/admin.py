# routes/admin.py
"""
Admin Dashboard API Routes
Endpoints for system administration and monitoring
"""

from fastapi import APIRouter, HTTPException, Query, Body
from typing import Dict, Any, Optional, List
from datetime import datetime

from services.settings_service import settings_service
from services.auth_service import auth_service
from database.connection import get_database_stats, check_database_health
from config.settings import settings, logger, enhanced_logger

router = APIRouter(prefix="/api/admin", tags=["admin"])


@router.get("/dashboard")
async def get_dashboard_data():
    """Get comprehensive dashboard data"""
    try:
        # Get database stats
        db_stats = get_database_stats()
        db_health = check_database_health()
        
        # Get auth stats
        auth_stats = auth_service.get_stats()
        
        # Build dashboard data
        dashboard = {
            "system_status": {
                "status": "operational",
                "uptime": "N/A",  # Would track actual uptime
                "version": "2.0.0",
                "environment": settings.APP_ENVIRONMENT
            },
            "statistics": {
                "total_messages": db_stats.get('messages_count', 0),
                "total_users": db_stats.get('users_count', 0),
                "total_projects": db_stats.get('projects_count', 0),
                "total_tickets": db_stats.get('tickets_count', 0),
                "total_files": db_stats.get('files_count', 0),
                "recent_messages_24h": db_stats.get('recent_messages_24h', 0)
            },
            "database": {
                "status": db_health.get('status', 'unknown'),
                "type": settings_service.get("database", "type", "sqlite"),
                "size_bytes": db_stats.get('database_size_bytes', 0)
            },
            "authentication": auth_stats,
            "features": settings_service.get_feature_settings(),
            "timestamp": datetime.now().isoformat()
        }
        
        return dashboard
        
    except Exception as e:
        enhanced_logger.error("Failed to get dashboard data", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/system-info")
async def get_system_info():
    """Get system information"""
    try:
        import platform
        import psutil
        
        # System info
        system_info = {
            "platform": platform.system(),
            "platform_release": platform.release(),
            "platform_version": platform.version(),
            "architecture": platform.machine(),
            "processor": platform.processor(),
            "python_version": platform.python_version()
        }
        
        # Resource usage
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('/')
        
        resources = {
            "cpu_percent": psutil.cpu_percent(interval=1),
            "cpu_count": psutil.cpu_count(),
            "memory_total_gb": round(memory.total / (1024**3), 2),
            "memory_used_gb": round(memory.used / (1024**3), 2),
            "memory_percent": memory.percent,
            "disk_total_gb": round(disk.total / (1024**3), 2),
            "disk_used_gb": round(disk.used / (1024**3), 2),
            "disk_percent": round((disk.used / disk.total) * 100, 1)
        }
        
        return {
            "system": system_info,
            "resources": resources,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        enhanced_logger.error("Failed to get system info", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/logs")
async def get_recent_logs(
    limit: int = Query(100, ge=1, le=1000, description="Number of log entries"),
    level: str = Query(None, description="Filter by log level"),
    search: str = Query(None, description="Search in log messages")
):
    """Get recent log entries"""
    try:
        import os
        from pathlib import Path
        
        log_file = Path("logs/chat_system.log")
        logs = []
        
        if log_file.exists():
            with open(log_file, 'r') as f:
                lines = f.readlines()
                
            # Get last N lines
            recent_lines = lines[-limit:]
            
            for line in recent_lines:
                line = line.strip()
                if not line:
                    continue
                    
                # Apply filters
                if level and level.upper() not in line.upper():
                    continue
                if search and search.lower() not in line.lower():
                    continue
                    
                logs.append(line)
        
        return {
            "logs": logs,
            "total_count": len(logs),
            "log_file": str(log_file),
            "filters": {"level": level, "search": search}
        }
        
    except Exception as e:
        enhanced_logger.error("Failed to get logs", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/users")
async def list_users(
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    role: str = Query(None, description="Filter by role"),
    active: bool = Query(None, description="Filter by active status")
):
    """List system users"""
    try:
        from database.repositories import UserRepository
        
        # This would normally use proper pagination
        # For now, return mock data structure
        return {
            "users": [],  # Would be populated from UserRepository
            "total": 0,
            "limit": limit,
            "offset": offset,
            "filters": {"role": role, "active": active}
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/api-keys")
async def list_api_keys():
    """List all API keys (admin only)"""
    try:
        # Get all API keys (would filter by admin access in production)
        return {
            "api_keys": [],  # Would be populated from auth_service
            "total": 0
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/api-keys")
async def create_api_key(
    name: str = Body(..., description="Key name"),
    user_id: str = Body(..., description="User ID"),
    permissions: List[str] = Body(["read"], description="Permissions")
):
    """Create a new API key"""
    try:
        result = auth_service.create_api_key(user_id, name, permissions)
        
        enhanced_logger.info("API key created by admin", 
                           key_id=result['id'],
                           user_id=user_id)
        
        return result
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/api-keys/{api_key}")
async def revoke_api_key(api_key: str):
    """Revoke an API key"""
    try:
        success = auth_service.revoke_api_key(api_key)
        
        if success:
            enhanced_logger.info("API key revoked by admin")
            return {"status": "revoked"}
        
        raise HTTPException(status_code=404, detail="API key not found")
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/sessions")
async def list_active_sessions():
    """List active user sessions"""
    try:
        stats = auth_service.get_stats()
        
        return {
            "active_sessions": stats.get('active_sessions', 0),
            "total_sessions": stats.get('total_sessions', 0),
            "session_details": []  # Would include session data
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/sessions/cleanup")
async def cleanup_sessions(
    max_age_hours: int = Body(24, embed=True, description="Max session age in hours")
):
    """Clean up expired sessions"""
    try:
        removed = auth_service.cleanup_expired_sessions(max_age_hours)
        
        enhanced_logger.info("Sessions cleaned up", removed=removed)
        
        return {
            "status": "completed",
            "removed_sessions": removed,
            "max_age_hours": max_age_hours
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/health")
async def get_system_health():
    """Get comprehensive system health check"""
    try:
        # Database health
        db_health = check_database_health()
        
        # Build health report
        health = {
            "status": "healthy",
            "components": {
                "database": db_health,
                "api": {"status": "healthy"},
                "websocket": {"status": "healthy"},
                "ai_service": {"status": "unknown"}  # Would check AI service
            },
            "timestamp": datetime.now().isoformat()
        }
        
        # Determine overall status
        unhealthy = any(
            c.get('status') == 'unhealthy' 
            for c in health['components'].values()
        )
        if unhealthy:
            health['status'] = 'unhealthy'
        
        return health
        
    except Exception as e:
        enhanced_logger.error("Health check failed", error=str(e))
        return {
            "status": "unhealthy",
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }


@router.get("/configuration")
async def get_full_configuration():
    """Get full system configuration"""
    try:
        return {
            "settings": settings_service.get_all(),
            "environment": settings.APP_ENVIRONMENT,
            "app_info": {
                "name": settings.APP_NAME,
                "version": "2.0.0",
                "debug": settings.APP_DEBUG
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/broadcast")
async def broadcast_system_message(
    message: str = Body(..., description="Message to broadcast"),
    message_type: str = Body("system", description="Message type")
):
    """Broadcast a system message to all connected clients"""
    try:
        from websocket.manager import manager
        
        await manager.broadcast({
            "type": "system_message",
            "message": message,
            "message_type": message_type,
            "timestamp": datetime.now().isoformat()
        })
        
        enhanced_logger.info("System message broadcast", message_type=message_type)
        
        return {
            "status": "broadcast",
            "message": message,
            "recipients": manager.get_connection_stats().get('active_connections', 0)
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
