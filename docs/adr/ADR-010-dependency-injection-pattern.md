# ADR-010: Dependency Injection Pattern

**Status:** Accepted  
**Date:** 2025-12-06  
**Decision Makers:** System Architects  
**Tags:** #architecture #patterns #dependency-injection

---

## Context

The chat system previously instantiated services and repositories directly in route handlers, leading to:

1. **Tight coupling** between routes and service implementations
2. **Difficult testing** - hard to mock dependencies
3. **Code duplication** - similar service initialization in multiple places
4. **Resource management issues** - unclear service lifecycle
5. **Unclear dependencies** - implicit rather than explicit dependencies

Example of previous pattern:
```python
# routes/messages.py
message_repository = MessageRepository()
message_service = MessageService(message_repository)

@router.get("/messages")
async def get_messages():
    # Tightly coupled to specific implementations
    return message_service.get_messages()
```

### Requirements

1. **Testability:** Easy to mock dependencies for unit testing
2. **Explicit Dependencies:** Clear what each endpoint needs
3. **Lifecycle Management:** Proper resource allocation/cleanup
4. **Type Safety:** Maintain strong typing for IDE support
5. **Simplicity:** No complex external frameworks
6. **Performance:** Minimal overhead

---

## Decision

We will use **FastAPI's native dependency injection** system with these patterns:

### 1. Dependency Functions

Create provider functions in `core/dependencies.py`:

```python
from functools import lru_cache
from fastapi import Depends

# Per-request dependencies (stateless)
def get_message_repository() -> MessageRepository:
    return MessageRepository()

# Singleton dependencies (stateful)
@lru_cache()
def get_auth_service() -> AuthService:
    return AuthService()
```

### 2. Dependency Injection in Routes

Use `Depends()` to inject dependencies:

```python
from fastapi import Depends
from core.dependencies import get_message_service

@router.get("/messages")
async def get_messages(
    service: MessageService = Depends(get_message_service)
):
    return service.get_messages()
```

### 3. Singleton Pattern for Stateful Services

Services with shared state use `@lru_cache()`:

- **AuthService** - JWT keys, token cache
- **PluginService** - Plugin registry
- **AIService** - AI model connections
- **SettingsService** - Configuration cache

### 4. Per-Request Pattern for Stateless Services

Services created fresh per request:

- **MessageService** - Business logic
- **FileService** - File operations
- **ProjectService** - Project management

### 5. Repository Pattern

Repositories wrap database access:

```python
def get_message_service(
    repository: MessageRepository = Depends(get_message_repository)
) -> MessageService:
    return MessageService(repository)
```

---

## Consequences

### Positive

✅ **Explicit Dependencies**
- Clear what each endpoint needs
- Better documentation through type hints
- IDE autocomplete and type checking

✅ **Easy Testing**
- Simple to override dependencies in tests
- No need for complex mocking frameworks
- Isolated unit tests

✅ **Resource Management**
- Automatic cleanup with context managers
- Database sessions properly closed
- Connection pooling handled correctly

✅ **Type Safety**
- Full type checking support
- IDE IntelliSense works correctly
- Catch errors at development time

✅ **Performance**
- Lazy initialization of expensive resources
- Singleton pattern for shared state
- No external framework overhead

✅ **Maintainability**
- Centralized service configuration
- Easy to refactor service implementations
- Clear lifecycle management

### Negative

❌ **Learning Curve**
- Developers must understand Depends()
- Difference between singleton vs per-request
- Proper use of @lru_cache()

❌ **Boilerplate**
- Need to define provider functions
- More files in project structure
- Explicit imports required

❌ **Testing Setup**
- Need to override dependencies for tests
- Requires understanding of override mechanism
- More test setup code

### Neutral

⚪ **Migration Effort**
- Existing routes need updating
- Services remain unchanged
- Gradual migration possible

---

## Alternatives Considered

### 1. dependency-injector Library

**Pros:**
- More features (containers, providers)
- Sophisticated scope management
- Configuration via YAML/JSON

**Cons:**
- External dependency
- More complex setup
- Overkill for our needs
- Learning curve

**Why Rejected:** FastAPI's native system is sufficient and simpler.

### 2. Manual Instantiation (Current)

**Pros:**
- Simple and direct
- No framework knowledge needed
- Easy to understand

**Cons:**
- Tight coupling
- Hard to test
- Resource management issues
- Code duplication

**Why Rejected:** Doesn't scale well and makes testing difficult.

### 3. Service Locator Pattern

**Pros:**
- Centralized service registry
- Flexible service resolution
- Runtime configuration

**Cons:**
- Hidden dependencies
- Runtime errors instead of compile-time
- Considered anti-pattern
- Hard to test

**Why Rejected:** Anti-pattern that hides dependencies.

### 4. Constructor Injection (Pure DI)

**Pros:**
- Very explicit
- No framework needed
- Easy to understand

**Cons:**
- Manual wiring required
- Complex initialization code
- Doesn't work well with FastAPI

**Why Rejected:** Doesn't integrate with FastAPI's async nature.

---

## Implementation Guide

### Step 1: Define Dependencies

Create `core/dependencies.py`:

```python
from functools import lru_cache
from fastapi import Depends
from database.repositories import MessageRepository
from services.message_service import MessageService

# Repository provider
def get_message_repository() -> MessageRepository:
    return MessageRepository()

# Service provider with dependency
def get_message_service(
    repo: MessageRepository = Depends(get_message_repository)
) -> MessageService:
    return MessageService(repo)
```

### Step 2: Update Routes

Replace manual instantiation:

```python
# Before
message_repository = MessageRepository()
message_service = MessageService(message_repository)

@router.get("/messages")
async def get_messages():
    return message_service.get_messages()

# After
from core.dependencies import get_message_service

@router.get("/messages")
async def get_messages(
    service: MessageService = Depends(get_message_service)
):
    return service.get_messages()
```

### Step 3: Testing

Override dependencies in tests:

```python
from fastapi.testclient import TestClient
from core.dependencies import get_message_service

def mock_message_service():
    return MockMessageService()

app.dependency_overrides[get_message_service] = mock_message_service

# Run tests
client = TestClient(app)
response = client.get("/messages")

# Cleanup
app.dependency_overrides.clear()
```

---

## Migration Strategy

### Phase 1: Core Infrastructure (Week 1)
- Create `core/dependencies.py`
- Define repository providers
- Define service providers
- Document patterns

### Phase 2: High-Traffic Routes (Week 2)
- Migrate messages endpoints
- Migrate auth endpoints
- Migrate chat endpoints
- Add tests

### Phase 3: Remaining Routes (Week 3)
- Migrate admin endpoints
- Migrate file endpoints
- Migrate project endpoints
- Update documentation

### Phase 4: Cleanup (Week 4)
- Remove old instantiation code
- Verify all routes use DI
- Complete test coverage
- Final documentation review

---

## Monitoring and Validation

### Success Metrics

1. **Test Coverage:** Should remain at or above current levels
2. **Performance:** No degradation in response times
3. **Code Quality:** Reduced coupling scores
4. **Developer Feedback:** Positive reception from team

### Health Checks

Dependency health check endpoint:

```python
@router.get("/health/dependencies")
async def check_dependencies():
    from core.dependencies import check_dependencies_health
    return check_dependencies_health()
```

---

## References

- [FastAPI Dependencies Documentation](https://fastapi.tiangolo.com/tutorial/dependencies/)
- [Dependency Injection Principles](https://martinfowler.com/articles/injection.html)
- [Python Design Patterns](https://refactoring.guru/design-patterns/python)
- [Clean Architecture](https://blog.cleancoder.com/uncle-bob/2012/08/13/the-clean-architecture.html)

---

## Related ADRs

- ADR-001: FastAPI Framework Choice
- ADR-002: SQLAlchemy ORM Choice
- ADR-011: Service Consolidation Strategy (future)
- ADR-012: Error Handling Centralization (future)

---

## Approval

- [x] Architecture Team
- [x] Backend Lead
- [x] QA Lead

**Approved by:** System Architect  
**Date:** 2025-12-06
