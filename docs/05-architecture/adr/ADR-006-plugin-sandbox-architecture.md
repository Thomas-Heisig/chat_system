# ADR-006: Docker-Based Plugin Sandbox Architecture

## Status
Accepted

## Date
2025-12-06

## Context
The Universal Chat System provides a plugin system to extend functionality with third-party code. However, executing untrusted code poses significant security risks:
- Malicious plugins could access sensitive data
- Buggy plugins could crash the main application
- Plugins could consume excessive resources (CPU, memory, disk)
- Plugins could make unauthorized network requests
- Plugins could interfere with each other

We need a secure isolation mechanism that:
- Prevents plugins from accessing system resources without permission
- Limits resource consumption
- Isolates plugins from each other
- Allows controlled communication with the main application
- Is easy to deploy and maintain

## Decision
We decided to use **Docker containers** for plugin sandboxing with the following design:

1. **Container-Based Isolation**: Each plugin runs in its own Docker container
2. **Permission System**: Explicit permissions for filesystem, network, database, and API access
3. **Resource Limits**: CPU, memory, and execution time constraints via Docker
4. **Controlled Communication**: REST API over internal network for plugin-to-system communication
5. **Security by Default**: Plugins run with minimal privileges unless explicitly granted

Implementation:
- `services/plugin_service.py` - Plugin management and lifecycle
- `PluginSandbox` class - Container orchestration and execution
- `PluginPermission` enum - Fine-grained permission model
- Docker SDK for Python - Container management

## Consequences

### Positive
- **Strong Isolation**: Docker provides OS-level isolation via namespaces and cgroups
- **Resource Control**: Can limit CPU, memory, and disk I/O per plugin
- **Portability**: Works on any system with Docker
- **Easy Cleanup**: Containers can be destroyed completely
- **Standard Technology**: Docker is well-understood and widely deployed
- **Network Isolation**: Can control network access per container
- **Development Flexibility**: Plugin developers can use any language

### Negative
- **Docker Dependency**: Requires Docker runtime on the host system
- **Performance Overhead**: Container startup and IPC overhead
- **Complexity**: More complex than in-process execution
- **Resource Usage**: Each container has base overhead
- **Development Experience**: Plugin developers need Docker knowledge

### Neutral
- **API-Based Communication**: Plugins communicate via HTTP/REST
- **Persistence**: Container state is ephemeral unless volumes are mounted
- **Logging**: Container logs need separate collection and management

## Alternatives Considered

### Alternative 1: Process-Based Isolation (subprocess)
- **Description**: Run plugins as separate Python processes with restricted imports
- **Pros**: 
  - Simpler implementation
  - Lower overhead
  - No external dependencies
- **Cons**: 
  - Weaker isolation (same OS user)
  - Harder to enforce resource limits
  - Can't isolate filesystem or network access easily
  - Python-only
- **Why Rejected**: Insufficient security guarantees

### Alternative 2: Virtual Machines (VMs)
- **Description**: Run each plugin in a full virtual machine
- **Pros**: 
  - Strongest isolation
  - Complete OS separation
- **Cons**: 
  - Very high overhead (GB of RAM per VM)
  - Slow startup times (minutes)
  - Complex management
  - Not practical for many plugins
- **Why Rejected**: Too heavyweight and slow

### Alternative 3: WebAssembly (WASM)
- **Description**: Compile plugins to WebAssembly and run in a WASM runtime
- **Pros**: 
  - Very lightweight
  - Fast startup
  - Language-agnostic (compile from many languages)
  - Strong sandboxing built-in
- **Cons**: 
  - Limited ecosystem for plugin development
  - Restrictions on system calls and I/O
  - WASI (WebAssembly System Interface) still maturing
  - Limited library support
- **Why Rejected**: Too early in maturity, would limit plugin capabilities

### Alternative 4: gVisor or Firecracker
- **Description**: Use lightweight virtualization technologies
- **Pros**: 
  - Stronger isolation than containers
  - Better performance than full VMs
  - Security-focused
- **Cons**: 
  - Additional dependencies
  - More complex setup
  - Less common/standard than Docker
  - Steeper learning curve
- **Why Rejected**: Adds complexity without sufficient benefit over Docker

### Alternative 5: Python Security Features (RestrictedPython)
- **Description**: Use Python's restricted execution features
- **Pros**: 
  - Native to Python
  - Low overhead
  - Simple integration
- **Cons**: 
  - History of security bypasses
  - Can't prevent resource exhaustion
  - Python-only
  - Not recommended by security experts
- **Why Rejected**: Known security issues and limitations

## References
- [Docker Security](https://docs.docker.com/engine/security/)
- [Docker Python SDK](https://docker-py.readthedocs.io/)
- Plugin System implementation: `services/plugin_service.py`
- Plugin System documentation: `docs/PLUGIN_SYSTEM.md`
- Security best practices: `SECURITY.md`
- Plugin permissions: `PluginPermission` enum in `services/plugin_service.py`
