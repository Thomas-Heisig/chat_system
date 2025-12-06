# routes/database.py
"""
Database Admin API Routes
Endpoints for database administration and management
"""

from datetime import datetime
from typing import Any, Dict

from fastapi import APIRouter, Body, HTTPException, Query

from config.settings import enhanced_logger

# Note: database.adapters module is not yet implemented
# from database.adapters import get_available_adapters, get_adapter
from database.connection import (
    backup_database,
    check_database_health,
    get_database_stats,
    optimize_database,
    restore_database,
    run_database_maintenance,
)
from services.settings_service import settings_service

router = APIRouter(prefix="/api/database", tags=["database"])


@router.get("/status")
async def get_database_status():
    """Get database status and health information"""
    try:
        health = check_database_health()
        db_settings = settings_service.get_database_settings()

        return {
            "status": health.get("status", "unknown"),
            "health": health,
            "database_type": db_settings.get("type", "sqlite"),
            "settings": {
                "host": db_settings.get("host"),
                "port": db_settings.get("port"),
                "name": db_settings.get("name"),
                "pool_size": db_settings.get("pool_size"),
            },
            "timestamp": datetime.now().isoformat(),
        }

    except Exception as e:
        enhanced_logger.error("Failed to get database status", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/stats")
async def get_database_statistics():
    """Get comprehensive database statistics"""
    try:
        stats = get_database_stats()

        return {"statistics": stats, "timestamp": datetime.now().isoformat()}

    except Exception as e:
        enhanced_logger.error("Failed to get database stats", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/adapters")
async def list_available_adapters():
    """
    List available database adapters
    
    Returns information about supported database types and current adapter.
    See docs/adr/ADR-007-multi-database-support.md for details on database support.
    """
    try:
        # Supported database adapters based on ADR-007
        adapters = [
            {
                "name": "sqlite",
                "display_name": "SQLite",
                "description": "Lightweight embedded database (default)",
                "recommended_for": "development, small deployments",
                "status": "fully_supported"
            },
            {
                "name": "postgresql",
                "display_name": "PostgreSQL",
                "description": "Advanced open-source relational database",
                "recommended_for": "production, high-load applications",
                "status": "supported"
            },
            {
                "name": "mongodb",
                "display_name": "MongoDB",
                "description": "Document-oriented NoSQL database",
                "recommended_for": "flexible schema, document storage",
                "status": "supported"
            }
        ]
        
        current_type = settings_service.get("database", "type", "sqlite")

        return {
            "adapters": adapters,
            "current_adapter": current_type,
            "note": "SQLite is directly integrated. PostgreSQL and MongoDB require SQLAlchemy/Motor setup."
        }

    except Exception as e:
        enhanced_logger.error("Failed to list database adapters", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/test-connection")
async def test_database_connection(
    config: Dict[str, Any] = Body(None, description="Optional connection config to test")
):
    """
    Test database connection with optional configuration
    
    Note: Custom config testing is not yet implemented for SQLite connections.
    For production multi-database support, use the unified repository pattern
    documented in docs/adr/ADR-007-multi-database-support.md
    """
    try:
        if config:
            # Custom configuration testing would require implementing
            # adapter-specific connection methods. For now, we test the current connection.
            enhanced_logger.info(
                "Testing current connection (custom config testing requires adapter implementation)",
                config_provided=True
            )

        # Test current connection
        health = check_database_health()
        result = {
            "status": "connected" if health.get("status") == "healthy" else "error",
            "health": health,
        }

        enhanced_logger.info("Database connection test", result=result.get("status"))
        return result

    except Exception as e:
        enhanced_logger.error("Database connection test failed", error=str(e))
        return {"status": "error", "error": str(e)}


@router.post("/backup")
async def create_database_backup(
    backup_name: str = Query(None, description="Optional backup name"),
    compress: bool = Query(True, description="Compress backup"),
):
    """Create a database backup"""
    try:
        if backup_name:
            backup_path = f"backups/{backup_name}"
        else:
            backup_path = None

        result_path = backup_database(backup_path, compress)

        enhanced_logger.info("Database backup created", backup_path=result_path)

        return {
            "status": "success",
            "backup_path": result_path,
            "compressed": compress,
            "timestamp": datetime.now().isoformat(),
        }

    except Exception as e:
        enhanced_logger.error("Database backup failed", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/restore")
async def restore_database_from_backup(
    backup_path: str = Body(..., embed=True, description="Path to backup file")
):
    """Restore database from backup"""
    try:
        restore_database(backup_path)

        enhanced_logger.info("Database restored from backup", backup_path=backup_path)

        return {
            "status": "success",
            "restored_from": backup_path,
            "timestamp": datetime.now().isoformat(),
        }

    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Backup file not found")
    except Exception as e:
        enhanced_logger.error("Database restore failed", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/optimize")
async def optimize_database_request(
    aggressive: bool = Query(False, description="Perform aggressive optimization")
):
    """Optimize database performance"""
    try:
        optimize_database(aggressive)

        enhanced_logger.info("Database optimization completed", aggressive=aggressive)

        return {
            "status": "optimized",
            "aggressive": aggressive,
            "timestamp": datetime.now().isoformat(),
        }

    except Exception as e:
        enhanced_logger.error("Database optimization failed", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/maintenance")
async def run_maintenance():
    """Run database maintenance tasks"""
    try:
        result = run_database_maintenance()

        enhanced_logger.info("Database maintenance completed", result=result)

        return {
            "status": "completed",
            "maintenance_log": result,
            "timestamp": datetime.now().isoformat(),
        }

    except Exception as e:
        enhanced_logger.error("Database maintenance failed", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/tables")
async def list_database_tables():
    """List all database tables and their row counts"""
    try:
        stats = get_database_stats()

        tables = {}
        for key, value in stats.items():
            if key.endswith("_count") and not key.startswith("recent_"):
                table_name = key.replace("_count", "")
                tables[table_name] = value

        return {"tables": tables, "timestamp": datetime.now().isoformat()}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/config")
async def update_database_config(config: Dict[str, Any] = Body(...)):
    """Update database configuration"""
    try:
        success = settings_service.update_database_settings(**config)

        if success:
            enhanced_logger.info("Database config updated", keys=list(config.keys()))
            return {
                "status": "updated",
                "config": settings_service.get_database_settings(),
                "note": "Restart may be required for changes to take effect",
            }

        raise HTTPException(status_code=400, detail="Failed to update config")

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/backups")
async def list_backups():
    """List available database backups"""
    try:
        from pathlib import Path

        backup_dir = Path("backups")
        backups = []

        if backup_dir.exists():
            for f in backup_dir.iterdir():
                if f.is_file():
                    stat = f.stat()
                    backups.append(
                        {
                            "name": f.name,
                            "path": str(f),
                            "size_bytes": stat.st_size,
                            "created_at": datetime.fromtimestamp(stat.st_mtime).isoformat(),
                        }
                    )

        backups.sort(key=lambda x: x["created_at"], reverse=True)

        return {
            "backups": backups,
            "backup_directory": str(backup_dir),
            "total_count": len(backups),
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/backups/{backup_name}")
async def delete_backup(backup_name: str):
    """Delete a specific backup"""
    try:
        import os
        from pathlib import Path

        backup_path = Path(f"backups/{backup_name}")

        if not backup_path.exists():
            raise HTTPException(status_code=404, detail="Backup not found")

        os.remove(backup_path)

        enhanced_logger.info("Backup deleted", backup_name=backup_name)

        return {"status": "deleted", "backup_name": backup_name}

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
