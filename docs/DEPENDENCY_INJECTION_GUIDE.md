# Dependency Injection Guide

**Status:** Active  
**Created:** 2025-12-06  
**Last Updated:** 2025-12-06

---

## Overview

This guide explains how to use the dependency injection (DI) system in the chat application. The DI system provides:

- ✅ **Explicit dependencies** - Clear what each endpoint needs
- ✅ **Easy testing** - Simple to mock dependencies
- ✅ **Resource management** - Automatic cleanup
- ✅ **Type safety** - Full IDE support
- ✅ **Performance** - Singleton pattern for expensive resources

See [ADR-010](adr/ADR-010-dependency-injection-pattern.md) for architecture decisions.

---

## Quick Start

### Before (Manual Instantiation)

```python
# routes/messages.py - OLD PATTERN
from database.repositories import MessageRepository
from services.message_service import MessageService

# Manual instantiation at module level
message_repository = MessageRepository()
message_service = MessageService(message_repository)

@router.get("/messages")
async def get_messages():
    # Tightly coupled to global instances
    messages = message_service.get_messages()
    return messages
```

**Problems:**
- ❌ Tight coupling
- ❌ Hard to test
- ❌ No resource cleanup
- ❌ Code duplication

### After (Dependency Injection)

```python
# routes/messages.py - NEW PATTERN
from fastapi import Depends
from core.dependencies import get_message_service
from services.message_service import MessageService

@router.get("/messages")
async def get_messages(
    service: MessageService = Depends(get_message_service)
):
    # Dependency injected, easy to test, properly managed
    messages = service.get_messages()
    return messages
```

**Benefits:**
- ✅ Loose coupling
- ✅ Easy to mock for testing
- ✅ Automatic resource cleanup
- ✅ Centralized configuration

---

## Core Concepts

### 1. Dependency Provider Functions

Defined in `core/dependencies.py`:

```python
def get_message_repository() -> MessageRepository:
    """Provider function for MessageRepository"""
    return MessageRepository()
```

### 2. Dependency Injection

Used in route handlers with `Depends()`:

```python
from fastapi import Depends

@router.get("/messages")
async def get_messages(
    repo: MessageRepository = Depends(get_message_repository)
):
    return repo.get_all_messages()
```

### 3. Dependency Chains

Dependencies can have their own dependencies:

```python
def get_message_service(
    repo: MessageRepository = Depends(get_message_repository)
) -> MessageService:
    return MessageService(repo)

@router.get("/messages")
async def get_messages(
    service: MessageService = Depends(get_message_service)
):
    # FastAPI automatically resolves the dependency chain:
    # get_message_service -> get_message_repository
    return service.get_messages()
```

---

## Dependency Types

### Per-Request Dependencies (Stateless)

Created fresh for each request:

```python
def get_message_repository() -> MessageRepository:
    """New instance per request"""
    return MessageRepository()

def get_message_service(
    repo: MessageRepository = Depends(get_message_repository)
) -> MessageService:
    """New instance per request with injected repository"""
    return MessageService(repo)
```

**Use for:**
- Repositories (database access)
- Business logic services
- Request-specific operations

### Singleton Dependencies (Stateful)

Single instance shared across all requests:

```python
from functools import lru_cache

@lru_cache()
def get_auth_service() -> AuthService:
    """Singleton instance shared across requests"""
    return AuthService()

@lru_cache()
def get_settings_service() -> SettingsService:
    """Singleton instance shared across requests"""
    return SettingsService()
```

**Use for:**
- Configuration services
- Connection pools
- Expensive-to-create resources
- Services with shared state

---

## Common Patterns

### Pattern 1: Simple Repository Injection

```python
from fastapi import Depends
from core.dependencies import get_message_repository
from database.repositories import MessageRepository

@router.get("/messages/{message_id}")
async def get_message(
    message_id: int,
    repo: MessageRepository = Depends(get_message_repository)
):
    message = repo.get_by_id(message_id)
    if not message:
        raise HTTPException(status_code=404, detail="Message not found")
    return message
```

### Pattern 2: Service with Dependencies

```python
from fastapi import Depends
from core.dependencies import get_message_service
from services.message_service import MessageService

@router.post("/messages")
async def create_message(
    content: str,
    service: MessageService = Depends(get_message_service)
):
    message = service.create_message(content)
    return message
```

### Pattern 3: Multiple Dependencies

```python
from fastapi import Depends
from core.dependencies import (
    get_message_service,
    get_auth_service
)

@router.post("/messages")
async def create_message(
    content: str,
    message_service: MessageService = Depends(get_message_service),
    auth_service: AuthService = Depends(get_auth_service),
    current_user: User = Depends(get_current_user)
):
    # Verify authentication
    auth_service.verify_token(current_user.token)
    
    # Create message
    message = message_service.create_message(
        content=content,
        user_id=current_user.id
    )
    return message
```

### Pattern 4: Optional Dependencies

```python
from typing import Optional
from fastapi import Depends

@router.get("/messages")
async def get_messages(
    service: MessageService = Depends(get_message_service),
    current_user: Optional[User] = Depends(get_current_user_optional)
):
    # current_user is None if not authenticated
    if current_user:
        return service.get_user_messages(current_user.id)
    return service.get_public_messages()
```

---

## Testing with Dependency Injection

### Unit Testing

```python
import pytest
from fastapi.testclient import TestClient
from core.dependencies import get_message_service
from main import app

# Mock service
class MockMessageService:
    def get_messages(self):
        return [{"id": 1, "content": "Test message"}]

def test_get_messages():
    # Override dependency
    app.dependency_overrides[get_message_service] = lambda: MockMessageService()
    
    # Test
    client = TestClient(app)
    response = client.get("/messages")
    
    assert response.status_code == 200
    assert len(response.json()) == 1
    
    # Cleanup
    app.dependency_overrides.clear()
```

### Integration Testing

```python
import pytest
from core.dependencies import get_message_repository
from database.repositories import MessageRepository

class TestMessageRepository(MessageRepository):
    """Test repository with in-memory storage"""
    def __init__(self):
        self.messages = []
    
    def get_all_messages(self):
        return self.messages

def test_integration():
    # Override with test repository
    app.dependency_overrides[get_message_repository] = TestMessageRepository
    
    # Test actual service logic with test database
    client = TestClient(app)
    response = client.post("/messages", json={"content": "Test"})
    
    assert response.status_code == 200
    
    # Cleanup
    app.dependency_overrides.clear()
```

### Pytest Fixtures

```python
import pytest
from fastapi.testclient import TestClient
from main import app

@pytest.fixture
def client():
    """Test client with dependency overrides"""
    # Setup
    app.dependency_overrides[get_message_service] = lambda: MockMessageService()
    
    yield TestClient(app)
    
    # Cleanup
    app.dependency_overrides.clear()

def test_with_fixture(client):
    response = client.get("/messages")
    assert response.status_code == 200
```

---

## Migration Guide

### Step 1: Identify Dependencies

Find manual instantiations in route files:

```bash
grep -n "= MessageRepository()" routes/*.py
grep -n "= MessageService(" routes/*.py
```

### Step 2: Add Dependency Providers

If not already in `core/dependencies.py`, add:

```python
def get_message_repository() -> MessageRepository:
    return MessageRepository()

def get_message_service(
    repo: MessageRepository = Depends(get_message_repository)
) -> MessageService:
    return MessageService(repo)
```

### Step 3: Update Route

Replace:

```python
# Old
message_repository = MessageRepository()
message_service = MessageService(message_repository)

@router.get("/messages")
async def get_messages():
    return message_service.get_messages()
```

With:

```python
# New
from fastapi import Depends
from core.dependencies import get_message_service

@router.get("/messages")
async def get_messages(
    service: MessageService = Depends(get_message_service)
):
    return service.get_messages()
```

### Step 4: Test

Run tests to ensure functionality unchanged:

```bash
pytest tests/routes/test_messages.py -v
```

### Step 5: Remove Module-Level Instantiations

Clean up old instantiations:

```python
# Remove these lines:
message_repository = MessageRepository()
message_service = MessageService(message_repository)
```

---

## Best Practices

### ✅ DO

1. **Use type hints** for all dependencies
   ```python
   def get_service(repo: Repository = Depends(get_repo)) -> Service:
   ```

2. **Keep providers simple** - just instantiation
   ```python
   def get_repository() -> MessageRepository:
       return MessageRepository()
   ```

3. **Use singleton for expensive resources**
   ```python
   @lru_cache()
   def get_connection_pool() -> ConnectionPool:
       return ConnectionPool()
   ```

4. **Document why using singleton**
   ```python
   @lru_cache()
   def get_auth_service() -> AuthService:
       """Singleton: JWT keys expensive to generate"""
       return AuthService()
   ```

### ❌ DON'T

1. **Don't put business logic in providers**
   ```python
   # Bad
   def get_service() -> Service:
       service = Service()
       service.initialize()
       service.load_data()
       return service
   ```

2. **Don't use singleton for request-specific data**
   ```python
   # Bad - leaks data between requests
   @lru_cache()
   def get_request_context() -> RequestContext:
       return RequestContext()
   ```

3. **Don't mix sync/async incorrectly**
   ```python
   # Bad - async provider for sync dependency
   async def get_repository() -> Repository:
       return Repository()
   ```

4. **Don't override dependencies in production code**
   ```python
   # Bad - only override in tests
   if testing:
       app.dependency_overrides[get_service] = mock_service
   ```

---

## Troubleshooting

### Issue: "TypeError: X() takes no arguments"

**Problem:** Missing `Depends()` wrapper

```python
# Wrong
@router.get("/")
async def endpoint(service: Service = get_service()):
    pass

# Correct
@router.get("/")
async def endpoint(service: Service = Depends(get_service)):
    pass
```

### Issue: "RuntimeError: no running event loop"

**Problem:** Async dependency in sync context

```python
# Wrong
async def get_service() -> Service:
    return Service()

# Correct (if service is sync)
def get_service() -> Service:
    return Service()
```

### Issue: Dependencies created multiple times per request

**Problem:** Not using singleton pattern

```python
# Wrong - creates new instance each time
def get_expensive_service() -> ExpensiveService:
    return ExpensiveService()  # Expensive!

# Correct - singleton pattern
@lru_cache()
def get_expensive_service() -> ExpensiveService:
    return ExpensiveService()
```

### Issue: Tests interfering with each other

**Problem:** Not clearing dependency overrides

```python
# Always clear in teardown
@pytest.fixture
def client():
    app.dependency_overrides[get_service] = mock_service
    yield TestClient(app)
    app.dependency_overrides.clear()  # Important!
```

---

## Performance Considerations

### Singleton Pattern Impact

```python
# Without singleton: ~50ms per request (connection overhead)
def get_db_pool() -> DBPool:
    return DBPool()  # Expensive!

# With singleton: ~1ms per request
@lru_cache()
def get_db_pool() -> DBPool:
    return DBPool()  # Created once
```

### Dependency Resolution Overhead

FastAPI's dependency injection has minimal overhead:
- Simple injection: < 0.1ms
- Nested dependencies (3 levels): < 0.5ms
- Async dependencies: < 0.2ms

### Memory Considerations

Singleton services persist for application lifetime:

```python
@lru_cache()
def get_cache_service() -> CacheService:
    # This instance lives forever
    # Ensure proper memory management
    return CacheService(max_size=1000)
```

---

## Reference

### Available Dependencies

See `core/dependencies.py` for complete list:

**Repositories (per-request):**
- `get_user_repository()`
- `get_message_repository()`
- `get_project_repository()`
- `get_ticket_repository()`
- `get_file_repository()`
- `get_statistics_repository()`

**Services (singleton):**
- `get_auth_service()`
- `get_settings_service()`
- `get_plugin_service()`
- `get_ai_service()`

**Services (per-request):**
- `get_message_service()`
- `get_file_service()`
- `get_project_service()`

### Health Check

Check dependency health:

```bash
curl http://localhost:8000/health/dependencies
```

Response:
```json
{
    "database": "healthy",
    "auth_service": "healthy",
    "ai_service": "healthy",
    "plugin_service": "healthy"
}
```

---

## Additional Resources

- [ADR-010: Dependency Injection Pattern](adr/ADR-010-dependency-injection-pattern.md)
- [FastAPI Dependencies](https://fastapi.tiangolo.com/tutorial/dependencies/)
- [Testing Guide](TESTING_GUIDE.md)
- [Architecture Overview](ARCHITECTURE.md)

---

## Support

For questions or issues:

1. Check this guide and ADR-010
2. Review `core/dependencies.py` implementation
3. Look at migrated routes for examples
4. Ask in #backend-development channel

---

**Last Updated:** 2025-12-06  
**Maintainer:** Backend Team
