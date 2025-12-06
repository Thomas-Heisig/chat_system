# 🔌 Plugin System Documentation

**Version:** 1.0.0  
**Last Updated:** 2025-12-05  
**Status:** Feature Implementation Pending

## Overview

The Plugin System provides a secure, extensible framework for adding custom functionality to the chat system through third-party plugins. It supports sandboxed execution, permission management, and a complete plugin lifecycle.

## Table of Contents

- [Architecture](#architecture)
- [Features](#features)
- [Plugin Development](#plugin-development)
- [Security Model](#security-model)
- [API Reference](#api-reference)
- [Docker Integration](#docker-integration)
- [Best Practices](#best-practices)
- [Troubleshooting](#troubleshooting)

---

## Architecture

### Component Structure

```
services/
└── plugin_service.py       # Core plugin management

plugins/                    # Plugin directory
├── manifest.json          # Plugin registry
├── plugin_a/
│   ├── plugin.yaml       # Plugin metadata
│   ├── main.py           # Plugin entry point
│   ├── requirements.txt  # Dependencies
│   └── README.md         # Documentation
└── plugin_b/
    └── ...
```

### Plugin System Architecture

```
┌─────────────────────────────────────────────┐
│          Chat System Core                    │
└──────────────────┬──────────────────────────┘
                   │
         ┌─────────▼─────────┐
         │  Plugin Service   │
         │   (Manager)       │
         └────────┬──────────┘
                  │
     ┌────────────┼────────────┬──────────────┐
     │            │            │              │
     ▼            ▼            ▼              ▼
┌─────────┐  ┌─────────┐  ┌─────────┐  ┌─────────┐
│Plugin A │  │Plugin B │  │Plugin C │  │Plugin D │
│(Docker) │  │(Docker) │  │(Docker) │  │(Process)│
└─────────┘  └─────────┘  └─────────┘  └─────────┘
```

### Plugin Lifecycle

```
Install
   │
   ▼
┌──────────┐
│Validate  │
└────┬─────┘
     │
     ▼
┌──────────┐
│Register  │
└────┬─────┘
     │
     ▼
┌──────────┐      ┌──────────┐
│ Enable   │─────→│ Running  │
└────┬─────┘      └────┬─────┘
     │                 │
     ▼                 ▼
┌──────────┐      ┌──────────┐
│ Disable  │      │  Stop    │
└────┬─────┘      └────┬─────┘
     │                 │
     └────────┬────────┘
              ▼
         ┌──────────┐
         │Uninstall │
         └──────────┘
```

---

## Features

### Core Capabilities

1. **Plugin Management**
   - Install from file/URL/marketplace
   - Enable/disable plugins
   - Update plugins
   - Uninstall plugins
   - Plugin dependencies

2. **Sandboxed Execution**
   - Docker container isolation
   - Process-level sandboxing
   - Resource limits (CPU, memory)
   - Network isolation

3. **Permission System**
   - Filesystem access control
   - Network access control
   - Database access control
   - API access control
   - Chat integration permissions

4. **Plugin Registry**
   - Local plugin storage
   - Plugin marketplace (planned)
   - Version management
   - Dependency resolution

5. **Monitoring & Health**
   - Plugin health checks
   - Resource usage monitoring
   - Error tracking
   - Performance metrics

### Implementation Status

- ✅ Plugin data structures
- ✅ Permission model
- ✅ Plugin lifecycle states
- ⏸️ Docker container management
- ⏸️ Plugin installation
- ⏸️ Resource limiting
- ⏸️ Plugin marketplace
- ⏸️ Hot reloading

---

## Plugin Development

### Plugin Structure

```
my-plugin/
├── plugin.yaml           # Plugin metadata
├── main.py              # Entry point
├── requirements.txt     # Python dependencies
├── Dockerfile          # Optional custom container
├── config.yaml         # Default configuration
├── README.md           # Documentation
└── tests/              # Plugin tests
    └── test_plugin.py
```

### Plugin Metadata (plugin.yaml)

```yaml
name: my-plugin
version: 1.0.0
description: Example plugin for chat system
author: Your Name
email: your.email@example.com
license: MIT

# Plugin type
type: extension  # extension, integration, ai-model, workflow

# Entry point
main: main.py
class: MyPlugin

# Dependencies
dependencies:
  - requests>=2.31.0
  - beautifulsoup4>=4.12.0

# Required permissions
permissions:
  - network_access
  - chat_access
  - api_access

# Optional permissions
optional_permissions:
  - filesystem_read
  - database_read

# Resource limits
resources:
  memory_mb: 512
  cpu_shares: 1024
  timeout_seconds: 30

# Configuration schema
config_schema:
  api_key:
    type: string
    required: true
    description: API key for external service
  endpoint:
    type: string
    default: https://api.example.com
    description: API endpoint URL

# Hooks (when plugin should be triggered)
hooks:
  - on_message
  - on_file_upload
  - on_command

# Commands
commands:
  - name: /myplugin
    description: Run my plugin
    usage: /myplugin [args]
```

### Plugin Entry Point (main.py)

```python
from typing import Any, Dict, Optional
import logging

logger = logging.getLogger(__name__)


class MyPlugin:
    """
    Example plugin implementation.
    
    All plugins must implement these core methods:
    - initialize()
    - execute()
    - cleanup()
    """
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize plugin with configuration.
        
        Args:
            config: Plugin configuration from plugin.yaml and user settings
        """
        self.config = config
        self.api_key = config.get("api_key")
        self.endpoint = config.get("endpoint")
        logger.info(f"Plugin initialized: {self.__class__.__name__}")
    
    async def initialize(self) -> bool:
        """
        Initialize plugin resources.
        
        Called when plugin is enabled.
        
        Returns:
            True if initialization successful
        """
        try:
            # Setup connections, load models, etc.
            logger.info("Plugin initialization complete")
            return True
        except Exception as e:
            logger.error(f"Plugin initialization failed: {e}")
            return False
    
    async def execute(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute plugin functionality.
        
        Args:
            context: Execution context with message, user, etc.
            
        Returns:
            Result dictionary
        """
        try:
            message = context.get("message", "")
            user = context.get("user", "")
            
            # Plugin logic here
            result = await self.process(message)
            
            return {
                "success": True,
                "result": result,
                "message": "Plugin executed successfully"
            }
            
        except Exception as e:
            logger.error(f"Plugin execution failed: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def process(self, message: str) -> str:
        """Custom processing logic"""
        # Example: Call external API
        import aiohttp
        
        async with aiohttp.ClientSession() as session:
            async with session.post(
                self.endpoint,
                json={"text": message},
                headers={"Authorization": f"Bearer {self.api_key}"}
            ) as response:
                data = await response.json()
                return data.get("result", "")
    
    async def cleanup(self) -> None:
        """
        Cleanup plugin resources.
        
        Called when plugin is disabled or uninstalled.
        """
        try:
            # Close connections, release resources, etc.
            logger.info("Plugin cleanup complete")
        except Exception as e:
            logger.error(f"Plugin cleanup failed: {e}")
    
    def health_check(self) -> Dict[str, Any]:
        """
        Check plugin health.
        
        Returns:
            Health status dictionary
        """
        return {
            "status": "healthy",
            "version": "1.0.0",
            "uptime": self.get_uptime()
        }
    
    def get_uptime(self) -> float:
        """Get plugin uptime in seconds"""
        # Implementation
        return 0.0


# Optional: Hook handlers
async def on_message(message: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """
    Handle incoming chat messages.
    
    Args:
        message: Message dictionary
        
    Returns:
        Response message or None
    """
    # Check if plugin should handle this message
    if message.get("text", "").startswith("/myplugin"):
        return {
            "text": "Plugin response",
            "type": "plugin_response"
        }
    return None


async def on_file_upload(file_info: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """
    Handle file uploads.
    
    Args:
        file_info: File information
        
    Returns:
        Processing result or None
    """
    # Process file if applicable
    return None


async def on_command(command: str, args: list) -> Dict[str, Any]:
    """
    Handle custom commands.
    
    Args:
        command: Command name
        args: Command arguments
        
    Returns:
        Command result
    """
    if command == "/myplugin":
        return {"result": "Command executed"}
    return {"error": "Unknown command"}
```

### Plugin Development Workflow

1. **Create Plugin Structure**
   ```bash
   mkdir my-plugin
   cd my-plugin
   
   # Create files
   touch plugin.yaml main.py requirements.txt README.md
   ```

2. **Write Plugin Code**
   - Implement required methods
   - Add custom functionality
   - Handle errors gracefully

3. **Test Locally**
   ```bash
   # Install dependencies
   pip install -r requirements.txt
   
   # Run tests
   pytest tests/
   ```

4. **Package Plugin**
   ```bash
   # Create plugin archive
   tar -czf my-plugin-1.0.0.tar.gz my-plugin/
   ```

5. **Install in Chat System**
   ```bash
   # Via CLI
   python -m plugin install my-plugin-1.0.0.tar.gz
   
   # Via API
   curl -X POST http://localhost:8000/api/plugins/install \
     -F "file=@my-plugin-1.0.0.tar.gz"
   ```

---

## Security Model

### Permission Levels

```python
class PluginPermission(str, Enum):
    """Plugin permissions"""
    
    # Filesystem
    FILESYSTEM_READ = "filesystem_read"      # Read files
    FILESYSTEM_WRITE = "filesystem_write"    # Write files
    
    # Network
    NETWORK_ACCESS = "network_access"        # Internet access
    
    # Database
    DATABASE_READ = "database_read"          # Read database
    DATABASE_WRITE = "database_write"        # Write database
    
    # API
    API_ACCESS = "api_access"                # Call chat system APIs
    
    # Chat
    CHAT_ACCESS = "chat_access"              # Read/send messages
    
    # Admin
    ADMIN_ACCESS = "admin_access"            # Admin operations
```

### Permission Requests

Plugins must declare required permissions in `plugin.yaml`:

```yaml
permissions:
  - network_access      # Required
  - chat_access         # Required

optional_permissions:
  - filesystem_read     # Optional, user can deny
  - database_read       # Optional, user can deny
```

### Security Sandbox

**Docker Isolation:**
```yaml
# Automatic Docker sandbox configuration
sandbox:
  type: docker
  image: python:3.9-slim
  network: restricted          # No internet unless network_access granted
  volumes:
    - /tmp/plugin:/workspace:ro  # Read-only workspace
  security_opt:
    - no-new-privileges:true
  cap_drop:
    - ALL
  memory: 512m
  cpu_shares: 1024
```

**Process Isolation (Fallback):**
```python
# If Docker unavailable, use process isolation
sandbox:
  type: process
  user: plugin-user          # Dedicated user
  working_dir: /tmp/plugin
  env_whitelist:
    - PATH
    - PYTHONPATH
```

---

## API Reference

### Plugin Service API

#### Install Plugin

```python
from services.plugin_service import PluginService

service = PluginService()

# Install from file
plugin_id = await service.install_plugin(
    plugin_path="/path/to/plugin.tar.gz"
)

# Install from URL
plugin_id = await service.install_plugin(
    plugin_url="https://plugins.example.com/my-plugin-1.0.0.tar.gz"
)
```

#### Enable/Disable Plugin

```python
# Enable plugin
await service.enable_plugin(plugin_id)

# Disable plugin
await service.disable_plugin(plugin_id)
```

#### Execute Plugin

```python
# Execute plugin
result = await service.execute_plugin(
    plugin_id=plugin_id,
    context={
        "message": "Hello plugin!",
        "user": "john_doe",
        "channel": "#general"
    }
)
```

#### Manage Plugins

```python
# List plugins
plugins = await service.list_plugins(
    status="enabled"  # enabled, disabled, all
)

# Get plugin info
info = await service.get_plugin_info(plugin_id)

# Update plugin
await service.update_plugin(
    plugin_id=plugin_id,
    plugin_path="/path/to/plugin-2.0.0.tar.gz"
)

# Uninstall plugin
await service.uninstall_plugin(plugin_id)
```

### REST API Endpoints

#### POST /api/plugins/install

Install a new plugin.

**Request:** Multipart form data
- `file`: Plugin archive (.tar.gz or .zip)

**Response:**
```json
{
  "plugin_id": "plugin_123",
  "name": "my-plugin",
  "version": "1.0.0",
  "status": "installed"
}
```

#### POST /api/plugins/{plugin_id}/enable

Enable a plugin.

**Response:**
```json
{
  "plugin_id": "plugin_123",
  "status": "enabled",
  "message": "Plugin enabled successfully"
}
```

#### POST /api/plugins/{plugin_id}/disable

Disable a plugin.

#### POST /api/plugins/{plugin_id}/execute

Execute a plugin.

**Request:**
```json
{
  "context": {
    "message": "Hello",
    "user": "john_doe"
  }
}
```

**Response:**
```json
{
  "success": true,
  "result": {...},
  "execution_time": 0.245
}
```

#### GET /api/plugins

List all plugins.

**Response:**
```json
{
  "plugins": [
    {
      "id": "plugin_123",
      "name": "my-plugin",
      "version": "1.0.0",
      "status": "enabled",
      "author": "Your Name",
      "description": "Example plugin"
    }
  ],
  "total": 1
}
```

#### DELETE /api/plugins/{plugin_id}

Uninstall a plugin.

---

## Docker Integration

### Docker Container Management

**File:** `services/plugin_service.py`

#### Starting Plugin Container

```python
import docker

async def _start_docker_container(self, plugin_id: str, 
                                 plugin_config: Dict) -> str:
    """Start plugin in Docker container"""
    try:
        client = docker.from_env()
        
        # Build or pull image
        image = plugin_config.get("docker_image", "python:3.9-slim")
        
        # Container configuration
        container = client.containers.run(
            image=image,
            name=f"plugin_{plugin_id}",
            detach=True,
            mem_limit=plugin_config.get("memory_mb", 512) * 1024 * 1024,
            cpu_shares=plugin_config.get("cpu_shares", 1024),
            network_mode="bridge" if plugin_config.get("network_access") else "none",
            volumes={
                f"/tmp/plugins/{plugin_id}": {
                    "bind": "/workspace",
                    "mode": "ro"
                }
            },
            environment={
                "PLUGIN_ID": plugin_id,
                "PLUGIN_CONFIG": json.dumps(plugin_config)
            },
            security_opt=["no-new-privileges"],
            cap_drop=["ALL"]
        )
        
        logger.info(f"✅ Container started: {container.id}")
        return container.id
        
    except Exception as e:
        logger.error(f"❌ Failed to start container: {e}")
        raise
```

#### Stopping Plugin Container

```python
async def _stop_docker_container(self, container_id: str) -> bool:
    """Stop and remove Docker container"""
    try:
        client = docker.from_env()
        container = client.containers.get(container_id)
        
        # Stop gracefully
        container.stop(timeout=10)
        
        # Remove container
        container.remove(force=True)
        
        logger.info(f"✅ Container stopped and removed: {container_id}")
        return True
        
    except Exception as e:
        logger.error(f"❌ Failed to stop container: {e}")
        return False
```

#### Monitoring Container

```python
async def _monitor_container(self, container_id: str) -> Dict[str, Any]:
    """Monitor container health and resource usage"""
    try:
        client = docker.from_env()
        container = client.containers.get(container_id)
        
        # Get stats
        stats = container.stats(stream=False)
        
        return {
            "status": container.status,
            "cpu_usage": self._calculate_cpu_percent(stats),
            "memory_usage_mb": stats["memory_stats"]["usage"] / 1024 / 1024,
            "network_rx_bytes": stats["networks"]["eth0"]["rx_bytes"],
            "network_tx_bytes": stats["networks"]["eth0"]["tx_bytes"]
        }
        
    except Exception as e:
        logger.error(f"❌ Failed to monitor container: {e}")
        return {}
```

### Custom Dockerfile

Plugins can provide custom Dockerfile:

```dockerfile
# plugins/my-plugin/Dockerfile
FROM python:3.9-slim

# Install dependencies
WORKDIR /workspace
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy plugin code
COPY . .

# Run plugin
CMD ["python", "main.py"]
```

---

## Best Practices

### 1. Plugin Design

**Single Responsibility:**
```python
# Good: One clear purpose
class WeatherPlugin:
    async def get_weather(self, location: str):
        pass

# Bad: Multiple unrelated features
class MegaPlugin:
    async def get_weather(self, location: str):
        pass
    async def send_email(self, recipient: str):
        pass
    async def generate_image(self, prompt: str):
        pass
```

### 2. Error Handling

**Always Handle Errors:**
```python
async def execute(self, context: Dict) -> Dict:
    try:
        result = await self.process(context)
        return {"success": True, "result": result}
    except APIError as e:
        logger.error(f"API error: {e}")
        return {"success": False, "error": "API temporarily unavailable"}
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        return {"success": False, "error": "Plugin error"}
```

### 3. Resource Management

**Cleanup Resources:**
```python
async def cleanup(self):
    """Properly cleanup resources"""
    # Close connections
    if self.db_connection:
        await self.db_connection.close()
    
    # Cancel tasks
    for task in self.background_tasks:
        task.cancel()
    
    # Release memory
    self.cache.clear()
```

### 4. Configuration

**Validate Configuration:**
```python
def __init__(self, config: Dict):
    # Validate required fields
    required = ["api_key", "endpoint"]
    missing = [f for f in required if f not in config]
    if missing:
        raise ValueError(f"Missing required config: {missing}")
    
    self.api_key = config["api_key"]
    self.endpoint = config["endpoint"]
```

---

## Testing

### Unit Tests

```python
# tests/test_plugin.py
import pytest
from plugins.my_plugin.main import MyPlugin

@pytest.fixture
def plugin():
    config = {
        "api_key": "test_key",
        "endpoint": "https://test.example.com"
    }
    return MyPlugin(config)

@pytest.mark.asyncio
async def test_initialize(plugin):
    success = await plugin.initialize()
    assert success is True

@pytest.mark.asyncio
async def test_execute(plugin):
    context = {"message": "Test", "user": "testuser"}
    result = await plugin.execute(context)
    assert result["success"] is True

@pytest.mark.asyncio
async def test_cleanup(plugin):
    await plugin.cleanup()
    # Verify resources released
```

### Integration Tests

```python
@pytest.mark.asyncio
async def test_plugin_lifecycle():
    service = PluginService()
    
    # Install
    plugin_id = await service.install_plugin("test-plugin.tar.gz")
    assert plugin_id is not None
    
    # Enable
    await service.enable_plugin(plugin_id)
    info = await service.get_plugin_info(plugin_id)
    assert info["status"] == "enabled"
    
    # Execute
    result = await service.execute_plugin(plugin_id, {})
    assert result["success"] is True
    
    # Disable
    await service.disable_plugin(plugin_id)
    
    # Uninstall
    await service.uninstall_plugin(plugin_id)
```

---

## Troubleshooting

### Plugin Won't Install

**Solutions:**
1. Verify plugin archive format (.tar.gz or .zip)
2. Check plugin.yaml is valid
3. Ensure all required fields present
4. Verify Python version compatibility

### Plugin Fails to Start

**Solutions:**
1. Check plugin logs
2. Verify dependencies installed
3. Check permissions granted
4. Test plugin locally first

### Docker Container Issues

**Solutions:**
1. Verify Docker is running
2. Check Docker permissions
3. Ensure image can be pulled
4. Check resource limits

### High Resource Usage

**Solutions:**
1. Reduce resource limits in plugin.yaml
2. Optimize plugin code
3. Add caching
4. Use async operations

---

## Roadmap

### Phase 1: Core Implementation
- [x] Plugin data structures
- [x] Permission model
- [ ] Docker container management
- [ ] Plugin installation
- [ ] Enable/disable functionality

### Phase 2: Advanced Features
- [ ] Plugin marketplace
- [ ] Hot reloading
- [ ] Plugin dependencies
- [ ] Version management
- [ ] Automatic updates

### Phase 3: Developer Tools
- [ ] Plugin SDK
- [ ] Plugin generator CLI
- [ ] Testing framework
- [ ] Documentation generator
- [ ] Plugin debugger

### Phase 4: Enterprise
- [ ] Plugin signing/verification
- [ ] Plugin audit logs
- [ ] Multi-tenancy support
- [ ] Plugin analytics
- [ ] Compliance features

---

**Last Updated:** 2025-12-05  
**Version:** 1.0.0  
**Status:** Documentation Complete - Implementation Pending
