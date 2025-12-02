# routes/plugins.py
"""
🔌 Plugin Management Routes
API endpoints for plugin management and lifecycle control.

Provides endpoints for:
- Plugin installation and uninstallation
- Plugin enabling/disabling
- Plugin execution
- Hook management

TODO:
- [ ] Add plugin authentication/authorization
- [ ] Implement plugin marketplace integration
- [ ] Add plugin analytics endpoints
- [ ] Implement plugin configuration UI
"""

from fastapi import APIRouter, HTTPException, Depends, UploadFile, File
from typing import Dict, Any, List, Optional

from config.settings import settings, logger
from services.plugin_service import get_plugin_service, PluginStatus
from core.auth import get_current_active_user, require_permission, Permission, User

router = APIRouter(prefix="/api/plugins", tags=["plugins"])


@router.get("/status")
async def plugins_status() -> Dict[str, Any]:
    """Get plugin service status"""
    plugin_service = get_plugin_service()
    return plugin_service.get_status()


@router.get("/")
async def list_plugins(
    status: Optional[PluginStatus] = None
) -> Dict[str, Any]:
    """
    List all plugins, optionally filtered by status
    
    Args:
        status: Optional status filter (installed, enabled, disabled, error)
    """
    plugin_service = get_plugin_service()
    plugins = plugin_service.list_plugins(status=status)
    return {
        "items": plugins,
        "total": len(plugins),
        "filter": status.value if status else "all"
    }


@router.get("/{plugin_id}")
async def get_plugin(plugin_id: str) -> Dict[str, Any]:
    """Get plugin details by ID"""
    plugin_service = get_plugin_service()
    plugin = plugin_service.get_plugin(plugin_id)
    if not plugin:
        raise HTTPException(status_code=404, detail=f"Plugin {plugin_id} not found")
    return plugin


@router.post("/install")
async def install_plugin(
    plugin_package: str,
    auto_enable: bool = False,
    user: User = Depends(require_permission(Permission.MANAGE_PLUGINS))
) -> Dict[str, Any]:
    """
    Install a plugin from package
    
    Args:
        plugin_package: Path or URL to plugin package
        auto_enable: Automatically enable after installation
        
    Requires: MANAGE_PLUGINS permission
    """
    plugin_service = get_plugin_service()
    result = await plugin_service.install_plugin(plugin_package, auto_enable)
    
    if not result.get("success"):
        raise HTTPException(status_code=400, detail=result.get("message", "Installation failed"))
    
    logger.info(f"Plugin installed by user {user.username}")
    return result


@router.post("/{plugin_id}/enable")
async def enable_plugin(
    plugin_id: str,
    user: User = Depends(require_permission(Permission.MANAGE_PLUGINS))
) -> Dict[str, Any]:
    """Enable a plugin"""
    plugin_service = get_plugin_service()
    result = await plugin_service.enable_plugin(plugin_id)
    
    if not result.get("success"):
        raise HTTPException(status_code=400, detail=result.get("error", "Enable failed"))
    
    logger.info(f"Plugin {plugin_id} enabled by user {user.username}")
    return result


@router.post("/{plugin_id}/disable")
async def disable_plugin(
    plugin_id: str,
    user: User = Depends(require_permission(Permission.MANAGE_PLUGINS))
) -> Dict[str, Any]:
    """Disable a plugin"""
    plugin_service = get_plugin_service()
    result = await plugin_service.disable_plugin(plugin_id)
    
    if not result.get("success"):
        raise HTTPException(status_code=400, detail=result.get("error", "Disable failed"))
    
    logger.info(f"Plugin {plugin_id} disabled by user {user.username}")
    return result


@router.delete("/{plugin_id}")
async def uninstall_plugin(
    plugin_id: str,
    user: User = Depends(require_permission(Permission.MANAGE_PLUGINS))
) -> Dict[str, Any]:
    """Uninstall a plugin"""
    plugin_service = get_plugin_service()
    result = await plugin_service.uninstall_plugin(plugin_id)
    
    if not result.get("success"):
        raise HTTPException(status_code=400, detail=result.get("error", "Uninstall failed"))
    
    logger.info(f"Plugin {plugin_id} uninstalled by user {user.username}")
    return result


@router.post("/{plugin_id}/execute")
async def execute_plugin_function(
    plugin_id: str,
    function_name: str,
    args: Optional[List[Any]] = None,
    kwargs: Optional[Dict[str, Any]] = None,
    user: User = Depends(get_current_active_user)
) -> Dict[str, Any]:
    """
    Execute a plugin function
    
    Args:
        plugin_id: Plugin identifier
        function_name: Function to execute
        args: Optional positional arguments
        kwargs: Optional keyword arguments
    """
    plugin_service = get_plugin_service()
    result = await plugin_service.execute_plugin(
        plugin_id, function_name, args, kwargs
    )
    
    if not result.get("success"):
        raise HTTPException(status_code=400, detail=result.get("error", "Execution failed"))
    
    return result


@router.get("/hooks/list")
async def list_hooks() -> Dict[str, Any]:
    """List all registered hooks"""
    plugin_service = get_plugin_service()
    return {
        "hooks": list(plugin_service.hooks.keys()),
        "total": len(plugin_service.hooks),
        "details": {
            name: len(callbacks) 
            for name, callbacks in plugin_service.hooks.items()
        }
    }


@router.post("/hooks/{hook_name}/trigger")
async def trigger_hook(
    hook_name: str,
    args: Optional[List[Any]] = None,
    kwargs: Optional[Dict[str, Any]] = None,
    user: User = Depends(require_permission(Permission.MANAGE_PLUGINS))
) -> Dict[str, Any]:
    """
    Manually trigger a hook
    
    Args:
        hook_name: Hook name (e.g., "on_message", "on_user_join")
        args: Optional positional arguments
        kwargs: Optional keyword arguments
        
    Requires: MANAGE_PLUGINS permission
    """
    plugin_service = get_plugin_service()
    
    try:
        await plugin_service.trigger_hook(
            hook_name,
            *(args or []),
            **(kwargs or {})
        )
        return {
            "success": True,
            "hook_name": hook_name,
            "message": "Hook triggered successfully"
        }
    except Exception as e:
        logger.error(f"Failed to trigger hook {hook_name}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Hook trigger failed: {str(e)}")
