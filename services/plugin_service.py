"""
🔌 Plugin Service - Extensibility System

Manages plugin lifecycle, sandboxed execution, and plugin registry.
Provides a safe environment for third-party extensions.

TODO:
- [ ] Implement Docker-based sandbox for plugin execution
- [ ] Add plugin permission system (filesystem, network, API access)
- [ ] Implement plugin marketplace/registry
- [ ] Add plugin versioning and dependency management
- [ ] Implement plugin hot-reloading
- [ ] Add resource limits (CPU, memory, execution time)
- [ ] Implement plugin health monitoring
- [ ] Add plugin analytics and telemetry
"""

import json
import os
import uuid
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional

from config.settings import logger


class PluginStatus(str, Enum):
    """Plugin lifecycle status"""

    INSTALLED = "installed"
    ENABLED = "enabled"
    DISABLED = "disabled"
    ERROR = "error"
    UNINSTALLED = "uninstalled"


class PluginPermission(str, Enum):
    """Plugin permissions"""

    FILESYSTEM_READ = "filesystem_read"
    FILESYSTEM_WRITE = "filesystem_write"
    NETWORK_ACCESS = "network_access"
    DATABASE_READ = "database_read"
    DATABASE_WRITE = "database_write"
    API_ACCESS = "api_access"
    CHAT_ACCESS = "chat_access"


class Plugin:
    """Plugin metadata and configuration"""

    def __init__(
        self,
        plugin_id: str,
        name: str,
        version: str,
        description: str,
        author: str,
        permissions: List[PluginPermission],
        entry_point: str,
        config: Optional[Dict[str, Any]] = None,
    ):
        self.plugin_id = plugin_id
        self.name = name
        self.version = version
        self.description = description
        self.author = author
        self.permissions = permissions
        self.entry_point = entry_point
        self.config = config or {}
        self.status = PluginStatus.INSTALLED
        self.installed_at = datetime.now()
        self.enabled_at: Optional[datetime] = None
        self.error_message: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert plugin to dictionary"""
        return {
            "plugin_id": self.plugin_id,
            "name": self.name,
            "version": self.version,
            "description": self.description,
            "author": self.author,
            "permissions": [p.value for p in self.permissions],
            "entry_point": self.entry_point,
            "config": self.config,
            "status": self.status.value,
            "installed_at": self.installed_at.isoformat(),
            "enabled_at": self.enabled_at.isoformat() if self.enabled_at else None,
            "error_message": self.error_message,
        }


class PluginSandbox:
    """
    Sandbox environment for plugin execution

    TODO:
    - [ ] Implement Docker container-based isolation
    - [ ] Add resource limits (CPU, memory, timeout)
    - [ ] Implement network isolation
    - [ ] Add filesystem restrictions
    - [ ] Implement syscall filtering (seccomp)
    """

    def __init__(self, plugin: Plugin):
        self.plugin = plugin
        self.container_id: Optional[str] = None
        logger.info(f"Plugin sandbox created for {plugin.name} (stub implementation)")

    async def execute(
        self,
        function_name: str,
        args: Optional[List[Any]] = None,
        kwargs: Optional[Dict[str, Any]] = None,
        timeout: int = 30,
    ) -> Dict[str, Any]:
        """
        Execute plugin function in sandbox

        Args:
            function_name: Name of the function to execute
            args: Positional arguments
            kwargs: Keyword arguments
            timeout: Execution timeout in seconds

        Returns:
            Execution result

        TODO:
        - [ ] Implement actual sandboxed execution
        - [ ] Add timeout enforcement
        - [ ] Implement permission checks
        - [ ] Add output sanitization

        SECURITY: This is a stub. Raises NotImplementedError to prevent
        accidental execution without proper sandboxing.
        """
        # Prevent execution in stub mode for security
        if os.getenv("ENABLE_PLUGIN_EXECUTION", "false").lower() != "true":
            raise NotImplementedError(
                "Plugin execution is not implemented. "
                "This is a stub and requires Docker-based sandboxing."
            )

        logger.warning(
            f"Plugin sandbox execution is a stub - "
            f"plugin={self.plugin.name}, function={function_name}"
        )

        return {
            "success": False,
            "result": None,
            "error": "Plugin sandbox execution not yet implemented",
            "plugin_id": self.plugin.plugin_id,
            "function": function_name,
            "timestamp": datetime.now().isoformat(),
            "stub": True,
        }

    def cleanup(self):
        """Clean up sandbox resources"""
        if self.container_id:
            container_id = self.container_id  # Keep reference for logging
            logger.info(f"Cleaning up sandbox container {container_id}")
            cleanup_successful = False
            
            try:
                import docker

                client = docker.from_env()
                try:
                    container = client.containers.get(container_id)
                    container.stop(timeout=10)
                    container.remove()
                    logger.info(f"✅ Sandbox container {container_id} stopped and removed")
                    cleanup_successful = True
                except docker.errors.NotFound:
                    logger.warning(f"⚠️ Container {container_id} not found, may already be removed")
                    cleanup_successful = True  # Container already gone
                except docker.errors.APIError as e:
                    logger.error(f"❌ Docker API error cleaning up container {container_id}: {e}")
            except ImportError:
                logger.warning(f"⚠️ Docker SDK not installed, cannot cleanup container {container_id}")
            except Exception as e:
                logger.error(f"❌ Failed to cleanup sandbox container {container_id}: {e}")
            
            # Clear container_id if cleanup was successful or container not found
            if cleanup_successful:
                self.container_id = None
            else:
                logger.error(
                    f"Container {container_id} may still be running, "
                    f"manual cleanup may be required. Container ID preserved for debugging."
                )


class PluginService:
    """
    Plugin management service

    Handles plugin installation, lifecycle, and execution.
    """

    def __init__(self, plugin_dir: Optional[str] = None):
        self.plugin_dir = Path(plugin_dir or "./plugins")
        self.plugin_dir.mkdir(exist_ok=True)

        self.plugins: Dict[str, Plugin] = {}
        self.sandboxes: Dict[str, PluginSandbox] = {}
        self.hooks: Dict[str, List[Callable]] = {}

        logger.info(f"🔌 Plugin Service initialized (plugin_dir={self.plugin_dir})")

        # Load installed plugins
        self._load_plugins()

    def _load_plugins(self):
        """Load plugins from plugin directory"""
        try:
            for plugin_path in self.plugin_dir.glob("*/plugin.json"):
                with open(plugin_path, "r") as f:
                    plugin_data = json.load(f)
                    plugin = Plugin(
                        plugin_id=plugin_data.get("id", str(uuid.uuid4())),
                        name=plugin_data["name"],
                        version=plugin_data["version"],
                        description=plugin_data.get("description", ""),
                        author=plugin_data.get("author", "Unknown"),
                        permissions=[
                            PluginPermission(p) for p in plugin_data.get("permissions", [])
                        ],
                        entry_point=plugin_data.get("entry_point", "main.py"),
                        config=plugin_data.get("config", {}),
                    )
                    self.plugins[plugin.plugin_id] = plugin
                    logger.info(f"Loaded plugin: {plugin.name} v{plugin.version}")
        except Exception as e:
            logger.error(f"Failed to load plugins: {str(e)}")

    async def install_plugin(
        self, plugin_package: str, auto_enable: bool = False
    ) -> Dict[str, Any]:
        """
        Install a plugin from package

        Args:
            plugin_package: Path to plugin package or URL
            auto_enable: Automatically enable after installation

        Returns:
            Installation result

        TODO:
        - [ ] Implement plugin package extraction
        - [ ] Add plugin validation
        - [ ] Implement dependency resolution
        - [ ] Add security scanning
        """
        logger.warning("Plugin installation is a stub")

        return {
            "success": False,
            "message": "Plugin installation not yet implemented",
            "plugin_package": plugin_package,
            "stub": True,
        }

    async def enable_plugin(self, plugin_id: str) -> Dict[str, Any]:
        """
        Enable a plugin

        Args:
            plugin_id: Plugin identifier

        Returns:
            Enable result
        """
        if plugin_id not in self.plugins:
            return {"success": False, "error": f"Plugin {plugin_id} not found"}

        plugin = self.plugins[plugin_id]

        try:
            # Create sandbox
            sandbox = PluginSandbox(plugin)
            self.sandboxes[plugin_id] = sandbox

            # Update status
            plugin.status = PluginStatus.ENABLED
            plugin.enabled_at = datetime.now()
            plugin.error_message = None

            logger.info(f"Plugin enabled: {plugin.name}")

            return {
                "success": True,
                "plugin": plugin.to_dict(),
                "message": f"Plugin {plugin.name} enabled successfully (sandbox is stub)",
            }

        except Exception as e:
            plugin.status = PluginStatus.ERROR
            plugin.error_message = str(e)
            logger.error(f"Failed to enable plugin {plugin.name}: {str(e)}")

            return {"success": False, "error": str(e), "plugin_id": plugin_id}

    async def disable_plugin(self, plugin_id: str) -> Dict[str, Any]:
        """
        Disable a plugin

        Args:
            plugin_id: Plugin identifier

        Returns:
            Disable result
        """
        if plugin_id not in self.plugins:
            return {"success": False, "error": f"Plugin {plugin_id} not found"}

        plugin = self.plugins[plugin_id]

        # Cleanup sandbox
        if plugin_id in self.sandboxes:
            self.sandboxes[plugin_id].cleanup()
            del self.sandboxes[plugin_id]

        # Update status
        plugin.status = PluginStatus.DISABLED
        plugin.enabled_at = None

        logger.info(f"Plugin disabled: {plugin.name}")

        return {
            "success": True,
            "plugin": plugin.to_dict(),
            "message": f"Plugin {plugin.name} disabled successfully",
        }

    async def uninstall_plugin(self, plugin_id: str) -> Dict[str, Any]:
        """
        Uninstall a plugin

        Args:
            plugin_id: Plugin identifier

        Returns:
            Uninstall result

        TODO:
        - [ ] Implement plugin file cleanup
        - [ ] Add data cleanup option
        """
        if plugin_id not in self.plugins:
            return {"success": False, "error": f"Plugin {plugin_id} not found"}

        # Disable first if enabled
        if self.plugins[plugin_id].status == PluginStatus.ENABLED:
            await self.disable_plugin(plugin_id)

        plugin = self.plugins[plugin_id]
        plugin.status = PluginStatus.UNINSTALLED

        # Remove from registry
        del self.plugins[plugin_id]

        logger.info(f"Plugin uninstalled: {plugin.name}")

        return {
            "success": True,
            "message": f"Plugin {plugin.name} uninstalled successfully (file cleanup is stub)",
        }

    async def execute_plugin(
        self,
        plugin_id: str,
        function_name: str,
        args: Optional[List[Any]] = None,
        kwargs: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Execute a plugin function

        Args:
            plugin_id: Plugin identifier
            function_name: Function to execute
            args: Positional arguments
            kwargs: Keyword arguments

        Returns:
            Execution result
        """
        if plugin_id not in self.plugins:
            return {"success": False, "error": f"Plugin {plugin_id} not found"}

        plugin = self.plugins[plugin_id]

        if plugin.status != PluginStatus.ENABLED:
            return {
                "success": False,
                "error": f"Plugin {plugin.name} is not enabled (status: {plugin.status})",
            }

        if plugin_id not in self.sandboxes:
            return {"success": False, "error": f"Plugin {plugin.name} has no active sandbox"}

        sandbox = self.sandboxes[plugin_id]
        return await sandbox.execute(function_name, args, kwargs)

    def list_plugins(self, status: Optional[PluginStatus] = None) -> List[Dict[str, Any]]:
        """
        List all plugins

        Args:
            status: Optional status filter

        Returns:
            List of plugins
        """
        plugins = self.plugins.values()

        if status:
            plugins = [p for p in plugins if p.status == status]

        return [p.to_dict() for p in plugins]

    def get_plugin(self, plugin_id: str) -> Optional[Dict[str, Any]]:
        """Get plugin by ID"""
        if plugin_id in self.plugins:
            return self.plugins[plugin_id].to_dict()
        return None

    def register_hook(self, hook_name: str, callback: Callable):
        """
        Register a hook callback

        Args:
            hook_name: Name of the hook (e.g., "on_message", "on_user_join")
            callback: Callback function
        """
        if hook_name not in self.hooks:
            self.hooks[hook_name] = []
        self.hooks[hook_name].append(callback)
        logger.debug(f"Hook registered: {hook_name}")

    async def trigger_hook(self, hook_name: str, *args, **kwargs):
        """
        Trigger all callbacks for a hook

        Args:
            hook_name: Name of the hook
            args: Positional arguments to pass to callbacks
            kwargs: Keyword arguments to pass to callbacks
        """
        if hook_name in self.hooks:
            for callback in self.hooks[hook_name]:
                try:
                    await callback(*args, **kwargs)
                except Exception as e:
                    logger.error(f"Hook callback failed: {hook_name} - {str(e)}")

    def get_status(self) -> Dict[str, Any]:
        """Get service status"""
        return {
            "service": "plugin",
            "plugin_dir": str(self.plugin_dir),
            "total_plugins": len(self.plugins),
            "enabled_plugins": len(
                [p for p in self.plugins.values() if p.status == PluginStatus.ENABLED]
            ),
            "active_sandboxes": len(self.sandboxes),
            "hooks": {name: len(callbacks) for name, callbacks in self.hooks.items()},
            "status": "online",
        }


# Singleton instance
_plugin_service: Optional[PluginService] = None


def get_plugin_service() -> PluginService:
    """
    Get or create the Plugin service singleton

    Returns:
        PluginService instance
    """
    global _plugin_service
    if _plugin_service is None:
        _plugin_service = PluginService()
    return _plugin_service
