# routes/database.py
"""
Database Admin API Routes
Endpoints for database administration and management
"""

from fastapi import APIRouter, HTTPException, Query, Body
from typing import Dict, Any, Optional
from datetime import datetime

from database.adapters import get_available_adapters, get_adapter
from database.connection import (
    get_database_stats, 
    check_database_health, 
    backup_database, 
    restore_database,
    optimize_database,
    run_database_maintenance
)
from services.settings_service import settings_service
from config.settings import logger, enhanced_logger

router = APIRouter(prefix="/api/database", tags=["database"])


@router.get("/status")
async def get_database_status():
    """Get database status and health information"""
    try:
        health = check_database_health()
        db_settings = settings_service.get_database_settings()
        
        return {
            "status": health.get('status', 'unknown'),
            "health": health,
            "database_type": db_settings.get('type', 'sqlite'),
            "settings": {
                "host": db_settings.get('host'),
                "port": db_settings.get('port'),
                "name": db_settings.get('name'),
                "pool_size": db_settings.get('pool_size')
            },
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        enhanced_logger.error("Failed to get database status", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/stats")
async def get_database_statistics():
    """Get comprehensive database statistics"""
    try:
        stats = get_database_stats()
        
        return {
            "statistics": stats,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        enhanced_logger.error("Failed to get database stats", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/adapters")
async def list_available_adapters():
    """List available database adapters"""
    try:
        adapters = get_available_adapters()
        
        return {
            "adapters": adapters,
            "current_adapter": settings_service.get("database", "type", "sqlite")
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/test-connection")
async def test_database_connection(
    config: Dict[str, Any] = Body(None, description="Optional connection config to test")
):
    """Test database connection with optional configuration"""
    try:
        if config:
            # Test with provided config
            db_type = config.get('type', 'sqlite')
            adapter_class = get_adapter(db_type)
            adapter = adapter_class(config)
            result = await adapter.test_connection()
        else:
            # Test current connection
            health = check_database_health()
            result = {
                "status": "connected" if health.get('status') == 'healthy' else "error",
                "health": health
            }
        
        enhanced_logger.info("Database connection test", result=result.get('status'))
        return result
        
    except Exception as e:
        enhanced_logger.error("Database connection test failed", error=str(e))
        return {
            "status": "error",
            "error": str(e)
        }


@router.post("/backup")
async def create_database_backup(
    backup_name: str = Query(None, description="Optional backup name"),
    compress: bool = Query(True, description="Compress backup")
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
            "timestamp": datetime.now().isoformat()
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
            "timestamp": datetime.now().isoformat()
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
            "timestamp": datetime.now().isoformat()
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
            "timestamp": datetime.now().isoformat()
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
            if key.endswith('_count') and not key.startswith('recent_'):
                table_name = key.replace('_count', '')
                tables[table_name] = value
        
        return {
            "tables": tables,
            "timestamp": datetime.now().isoformat()
        }
        
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
                "note": "Restart may be required for changes to take effect"
            }
        
        raise HTTPException(status_code=400, detail="Failed to update config")
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/backups")
async def list_backups():
    """List available database backups"""
    try:
        import os
        from pathlib import Path
        
        backup_dir = Path("backups")
        backups = []
        
        if backup_dir.exists():
            for f in backup_dir.iterdir():
                if f.is_file():
                    stat = f.stat()
                    backups.append({
                        "name": f.name,
                        "path": str(f),
                        "size_bytes": stat.st_size,
                        "created_at": datetime.fromtimestamp(stat.st_mtime).isoformat()
                    })
        
        backups.sort(key=lambda x: x['created_at'], reverse=True)
        
        return {
            "backups": backups,
            "backup_directory": str(backup_dir),
            "total_count": len(backups)
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
        
        return {
            "status": "deleted",
            "backup_name": backup_name
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
