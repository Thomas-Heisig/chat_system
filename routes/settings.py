# routes/settings.py
"""
Settings API Routes
CRUD endpoints for application settings management
"""

from fastapi import APIRouter, HTTPException, Depends, Body
from typing import Dict, Any, Optional
from datetime import datetime

from services.settings_service import settings_service
from config.settings import logger, enhanced_logger

router = APIRouter(prefix="/api/settings", tags=["settings"])


@router.get("")
async def get_all_settings():
    """Get all application settings"""
    try:
        settings = settings_service.get_all()
        enhanced_logger.info("All settings retrieved")
        return {
            "settings": settings,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Failed to get settings: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve settings")


@router.get("/categories")
async def get_available_categories():
    """Get list of available settings categories"""
    return {
        "categories": settings_service.get_available_categories()
    }


# General Settings
@router.get("/general")
async def get_general_settings():
    """Get general settings"""
    try:
        return settings_service.get_general_settings()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/general")
async def update_general_settings(settings_data: Dict[str, Any] = Body(...)):
    """Update general settings"""
    try:
        success = settings_service.update_general_settings(**settings_data)
        if success:
            enhanced_logger.info("General settings updated", keys=list(settings_data.keys()))
            return {"status": "updated", "settings": settings_service.get_general_settings()}
        raise HTTPException(status_code=400, detail="Failed to update settings")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# AI Settings
@router.get("/ai")
async def get_ai_settings():
    """Get AI configuration settings"""
    try:
        return settings_service.get_ai_settings()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/ai")
async def update_ai_settings(settings_data: Dict[str, Any] = Body(...)):
    """Update AI configuration settings"""
    try:
        success = settings_service.update_ai_settings(**settings_data)
        if success:
            enhanced_logger.info("AI settings updated", keys=list(settings_data.keys()))
            return {"status": "updated", "settings": settings_service.get_ai_settings()}
        raise HTTPException(status_code=400, detail="Failed to update settings")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# Security Settings
@router.get("/security")
async def get_security_settings():
    """Get security settings"""
    try:
        return settings_service.get_security_settings()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/security")
async def update_security_settings(settings_data: Dict[str, Any] = Body(...)):
    """Update security settings"""
    try:
        success = settings_service.update_security_settings(**settings_data)
        if success:
            enhanced_logger.info("Security settings updated", keys=list(settings_data.keys()))
            return {"status": "updated", "settings": settings_service.get_security_settings()}
        raise HTTPException(status_code=400, detail="Failed to update settings")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# Database Settings
@router.get("/database")
async def get_database_settings():
    """Get database configuration settings"""
    try:
        return settings_service.get_database_settings()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/database")
async def update_database_settings(settings_data: Dict[str, Any] = Body(...)):
    """Update database configuration settings"""
    try:
        success = settings_service.update_database_settings(**settings_data)
        if success:
            enhanced_logger.info("Database settings updated", keys=list(settings_data.keys()))
            return {"status": "updated", "settings": settings_service.get_database_settings()}
        raise HTTPException(status_code=400, detail="Failed to update settings")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# RAG Settings
@router.get("/rag")
async def get_rag_settings():
    """Get RAG configuration settings"""
    try:
        return settings_service.get_rag_settings()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/rag")
async def update_rag_settings(settings_data: Dict[str, Any] = Body(...)):
    """Update RAG configuration settings"""
    try:
        success = settings_service.update_rag_settings(**settings_data)
        if success:
            enhanced_logger.info("RAG settings updated", keys=list(settings_data.keys()))
            return {"status": "updated", "settings": settings_service.get_rag_settings()}
        raise HTTPException(status_code=400, detail="Failed to update settings")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# Feature Settings
@router.get("/features")
async def get_feature_settings():
    """Get feature flags"""
    try:
        return settings_service.get_feature_settings()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/features")
async def update_feature_settings(settings_data: Dict[str, Any] = Body(...)):
    """Update feature flags"""
    try:
        success = settings_service.update_feature_settings(**settings_data)
        if success:
            enhanced_logger.info("Feature settings updated", keys=list(settings_data.keys()))
            return {"status": "updated", "settings": settings_service.get_feature_settings()}
        raise HTTPException(status_code=400, detail="Failed to update settings")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# UI Settings
@router.get("/ui")
async def get_ui_settings():
    """Get UI settings"""
    try:
        return settings_service.get_ui_settings()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/ui")
async def update_ui_settings(settings_data: Dict[str, Any] = Body(...)):
    """Update UI settings"""
    try:
        success = settings_service.update_ui_settings(**settings_data)
        if success:
            enhanced_logger.info("UI settings updated", keys=list(settings_data.keys()))
            return {"status": "updated", "settings": settings_service.get_ui_settings()}
        raise HTTPException(status_code=400, detail="Failed to update settings")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# Export/Import
@router.get("/export")
async def export_settings():
    """Export all settings as JSON"""
    try:
        return {
            "settings_json": settings_service.export_settings(),
            "exported_at": datetime.now().isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/import")
async def import_settings(settings_json: str = Body(..., embed=True)):
    """Import settings from JSON"""
    try:
        success = settings_service.import_settings(settings_json)
        if success:
            enhanced_logger.info("Settings imported successfully")
            return {"status": "imported", "settings": settings_service.get_all()}
        raise HTTPException(status_code=400, detail="Failed to import settings")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# Reset Operations
@router.post("/reset/{category}")
async def reset_category_settings(category: str):
    """Reset settings for a specific category to defaults"""
    try:
        success = settings_service.reset_category(category)
        if success:
            enhanced_logger.info("Category settings reset", category=category)
            return {"status": "reset", "category": category}
        raise HTTPException(status_code=404, detail=f"Category '{category}' not found")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/reset")
async def reset_all_settings():
    """Reset all settings to defaults"""
    try:
        success = settings_service.reset_all()
        if success:
            enhanced_logger.info("All settings reset to defaults")
            return {"status": "reset", "settings": settings_service.get_all()}
        raise HTTPException(status_code=400, detail="Failed to reset settings")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
