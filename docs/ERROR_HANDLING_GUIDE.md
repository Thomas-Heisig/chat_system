# Error Handling Guide

**Status:** Active  
**Created:** 2025-12-06  
**Last Updated:** 2025-12-06

---

## Overview

This guide explains how to handle errors consistently in the chat application. The system provides:

- ✅ **Standardized error responses** across all endpoints
- ✅ **Security-safe** error messages (no information leakage)
- ✅ **Comprehensive logging** for debugging
- ✅ **Client-friendly** error codes and messages
- ✅ **Monitoring integration** for error tracking

See [ADR-012](adr/ADR-012-error-handling-centralization.md) for architecture decisions.

---

## Quick Start

### Raising Errors in Routes

```python
from fastapi import APIRouter
from services.exceptions import ResourceNotFoundError, ValidationError

router = APIRouter()

@router.get("/users/{user_id}")
async def get_user(user_id: int):
    user = await fetch_user(user_id)
    
    # If resource not found, raise appropriate exception
    if not user:
        raise ResourceNotFoundError("User", str(user_id))
    
    return user

@router.post("/users")
async def create_user(username: str, email: str):
    # Validate input
    if not email or "@" not in email:
        raise ValidationError(
            "Invalid email address",
            field_errors={"email": "Must be a valid email"}
        )
    
    # ... create user
```

**That's it!** The global error handler will:
1. Catch the exception
2. Format it consistently
3. Log appropriately
4. Return proper HTTP response

---

## Error Response Format

All errors return this consistent structure:

```json
{
    "error": true,
    "status_code": 404,
    "error_code": "RESOURCE_NOT_FOUND",
    "message": "User with ID '123' not found",
    "timestamp": "2024-01-01T12:00:00Z",
    "timestamp_unix": 1704110400.0,
    "request": {
        "method": "GET",
        "path": "/api/users/123",
        "query": null
    },
    "details": {
        "resource_type": "User",
        "resource_id": "123"
    },
    "help_url": "/docs/errors/resource_not_found"
}
```

### Debug Mode

In development (`APP_DEBUG=true`), additional fields are included:

```json
{
    ...
    "debug": {
        "exception_type": "ResourceNotFoundError",
        "exception_module": "services.exceptions",
        "traceback": "Traceback (most recent call last):\n..."
    }
}
```

---

## Available Exceptions

### Import from `services.exceptions`

All exceptions inherit from `ServiceException` and map to appropriate HTTP status codes.

### Client Errors (4xx)

#### 400 Bad Request

```python
from services.exceptions import BadRequestError, InvalidInputError

# Generic bad request
raise BadRequestError("Request cannot be processed")

# Invalid input
raise InvalidInputError("Invalid date format")
```

#### 401 Unauthorized

```python
from services.exceptions import (
    AuthenticationError,
    InvalidCredentialsError,
    TokenExpiredError
)

# Generic authentication failure
raise AuthenticationError("Authentication required")

# Specific cases
raise InvalidCredentialsError()  # Wrong username/password
raise TokenExpiredError()  # JWT expired
```

#### 403 Forbidden

```python
from services.exceptions import (
    AuthorizationError,
    InsufficientPermissionsError
)

# Generic authorization failure
raise AuthorizationError("Access denied")

# Specific permission missing
raise InsufficientPermissionsError("admin")
```

#### 404 Not Found

```python
from services.exceptions import (
    ResourceNotFoundError,
    UserNotFoundError,
    ProjectNotFoundError,
    MessageNotFoundError
)

# Generic resource
raise ResourceNotFoundError("Document", "doc_123")

# Specific resources
raise UserNotFoundError("user_456")
raise ProjectNotFoundError("proj_789")
raise MessageNotFoundError("msg_abc")
```

#### 409 Conflict

```python
from services.exceptions import (
    ConflictError,
    DuplicateResourceError
)

# Generic conflict
raise ConflictError("Operation conflicts with current state")

# Duplicate resource
raise DuplicateResourceError("User", "username: john")
```

#### 422 Validation Error

```python
from services.exceptions import ValidationError

# Simple validation error
raise ValidationError("Username must be at least 3 characters")

# With field-level errors
raise ValidationError(
    "Validation failed",
    field_errors={
        "username": "Must be at least 3 characters",
        "email": "Invalid email format",
        "age": "Must be at least 18"
    }
)
```

#### 429 Rate Limit

```python
from services.exceptions import RateLimitExceededError

# Simple rate limit
raise RateLimitExceededError()

# With retry-after header
raise RateLimitExceededError(
    "Too many requests",
    retry_after=60  # seconds
)
```

### Server Errors (5xx)

#### 500 Internal Server Error

```python
from services.exceptions import (
    InternalServerError,
    DatabaseError,
    DatabaseConnectionError
)

# Generic internal error
raise InternalServerError("Something went wrong")

# Database errors
raise DatabaseError("Failed to save data")
raise DatabaseConnectionError()
```

#### 502 Bad Gateway

```python
from services.exceptions import (
    ExternalServiceError,
    ExternalAIUnavailableError
)

# External service failure
raise ExternalServiceError("Slack", "Failed to send notification")

# AI service unavailable (triggers fallback)
raise ExternalAIUnavailableError("Ollama")
```

#### 503 Service Unavailable

```python
from services.exceptions import ServiceUnavailableError

# Temporary unavailability
raise ServiceUnavailableError(
    "Service is under maintenance",
    retry_after=300  # 5 minutes
)
```

### Feature-Specific Errors

```python
from services.exceptions import (
    FeatureDisabledError,
    ConfigurationError
)

# Feature not enabled
raise FeatureDisabledError("RAG System")

# Configuration issue
raise ConfigurationError("Missing OPENAI_API_KEY")
```

---

## Convenience Functions

For quick error raising, use convenience functions from `core.error_handlers`:

```python
from core.error_handlers import (
    raise_not_found,
    raise_validation_error,
    raise_unauthorized,
    raise_forbidden
)

# Shorter syntax
user = get_user(user_id)
if not user:
    raise_not_found("User", user_id)

# Instead of:
if not user:
    from services.exceptions import ResourceNotFoundError
    raise ResourceNotFoundError("User", user_id)
```

---

## Best Practices

### DO ✅

#### 1. Use Specific Exceptions

```python
# Good
raise UserNotFoundError(user_id)

# Less specific
raise ResourceNotFoundError("User", user_id)

# Too generic
raise HTTPException(status_code=404, detail="Not found")
```

#### 2. Provide Context

```python
# Good - includes helpful details
raise ValidationError(
    "Registration failed",
    field_errors={
        "email": "Email already registered",
        "password": "Must be at least 8 characters"
    }
)

# Bad - vague
raise ValidationError("Invalid input")
```

#### 3. Let Global Handler Format

```python
# Good - raise exception, handler formats it
raise ResourceNotFoundError("User", user_id)

# Bad - manual formatting
return JSONResponse(
    status_code=404,
    content={"error": "User not found"}
)
```

#### 4. Log Before Raising (When Needed)

```python
# Good - log context before raising
try:
    result = complex_operation()
except Exception as e:
    logger.error(f"Complex operation failed: {e}", extra_context=data)
    raise InternalServerError("Operation failed")
```

### DON'T ❌

#### 1. Don't Catch and Re-raise HTTPException

```python
# Bad
try:
    something()
except Exception as e:
    raise HTTPException(status_code=500, detail=str(e))

# Good
try:
    something()
except SomeSpecificError:
    raise InternalServerError("Failed to do something")
```

#### 2. Don't Expose Internal Details

```python
# Bad - exposes database schema
raise ValidationError(f"Column 'usr_email' violates constraint")

# Good - user-friendly message
raise ValidationError("Email address is already in use")
```

#### 3. Don't Return Errors

```python
# Bad - inconsistent format
return {"error": "Something went wrong"}

# Good - raise exception
raise InternalServerError("Something went wrong")
```

#### 4. Don't Swallow Errors

```python
# Bad - silently fails
try:
    important_operation()
except Exception:
    pass  # ERROR: Silent failure!

# Good - log and raise
try:
    important_operation()
except Exception as e:
    logger.error(f"Important operation failed: {e}")
    raise InternalServerError("Operation failed")
```

---

## Client-Side Handling

### JavaScript/TypeScript

```typescript
async function fetchUser(userId: number): Promise<User> {
    try {
        const response = await fetch(`/api/users/${userId}`);
        const data = await response.json();
        
        // Check if error
        if (data.error) {
            handleError(data);
            throw new Error(data.message);
        }
        
        return data;
    } catch (error) {
        console.error('Failed to fetch user:', error);
        throw error;
    }
}

function handleError(error: ApiError) {
    switch (error.error_code) {
        case 'RESOURCE_NOT_FOUND':
            showNotification('User not found', 'warning');
            break;
        case 'UNAUTHORIZED':
            redirectToLogin();
            break;
        case 'VALIDATION_ERROR':
            showValidationErrors(error.details.validation_errors);
            break;
        case 'RATE_LIMIT_EXCEEDED':
            showNotification(
                `Too many requests. Retry in ${error.details.retry_after}s`,
                'error'
            );
            break;
        default:
            showNotification(error.message, 'error');
    }
}
```

### Python Client

```python
import requests

def get_user(user_id: int) -> dict:
    response = requests.get(f"/api/users/{user_id}")
    data = response.json()
    
    if data.get("error"):
        error_code = data.get("error_code")
        
        if error_code == "RESOURCE_NOT_FOUND":
            raise ValueError(f"User {user_id} not found")
        elif error_code == "UNAUTHORIZED":
            raise PermissionError("Authentication required")
        else:
            raise Exception(data.get("message"))
    
    return data
```

---

## Testing Error Handling

### Unit Tests

```python
import pytest
from fastapi.testclient import TestClient
from services.exceptions import ResourceNotFoundError

def test_user_not_found_error():
    """Test that ResourceNotFoundError returns proper format"""
    response = client.get("/api/users/99999")
    
    assert response.status_code == 404
    
    error = response.json()
    assert error["error"] is True
    assert error["error_code"] == "RESOURCE_NOT_FOUND"
    assert "User" in error["message"]
    assert error["details"]["resource_type"] == "User"
    assert error["details"]["resource_id"] == "99999"

def test_validation_error():
    """Test validation error format"""
    response = client.post("/api/users", json={
        "username": "ab",  # Too short
        "email": "invalid"  # Invalid email
    })
    
    assert response.status_code == 422
    
    error = response.json()
    assert error["error_code"] == "VALIDATION_ERROR"
    assert "validation_errors" in error["details"]
    
    validation_errors = error["details"]["validation_errors"]
    assert any(e["field"] == "username" for e in validation_errors)
    assert any(e["field"] == "email" for e in validation_errors)
```

### Integration Tests

```python
def test_error_logging(caplog):
    """Test that errors are logged properly"""
    with caplog.at_level(logging.WARNING):
        response = client.get("/api/users/99999")
    
    assert response.status_code == 404
    assert "Service exception occurred" in caplog.text
    assert "RESOURCE_NOT_FOUND" in caplog.text
```

---

## Monitoring & Debugging

### View Error Metrics

```python
GET /api/health/errors

Response:
{
    "total_errors": 150,
    "error_counts": {
        "ServiceException:RESOURCE_NOT_FOUND": 100,
        "ServiceException:VALIDATION_ERROR": 45,
        "Exception:INTERNAL_ERROR": 5
    },
    "recent_errors": [
        {
            "error_type": "ResourceNotFoundError",
            "error_code": "RESOURCE_NOT_FOUND",
            "status_code": 404,
            "timestamp": "2024-01-01T12:00:00Z"
        }
    ]
}
```

### Log Analysis

Errors are logged with structured data:

```python
# Search logs for specific error
grep "error_code=RESOURCE_NOT_FOUND" app.log

# Count errors by type
grep "Service exception occurred" app.log | \
  jq -r '.error_code' | sort | uniq -c | sort -rn

# Find errors from specific endpoint
grep "url=/api/users" app.log | grep "error=True"
```

---

## Troubleshooting

### Common Issues

#### Issue: Errors not formatted correctly

**Symptom:** Error response doesn't match standard format

**Solution:** Ensure `register_exception_handlers()` is called:

```python
from core.error_handlers import register_exception_handlers

app = FastAPI()
register_exception_handlers(app)
```

#### Issue: Stack traces exposed in production

**Symptom:** Full stack traces visible to clients

**Solution:** Set `APP_DEBUG=false` in production:

```bash
# .env
APP_DEBUG=false
```

#### Issue: Custom exceptions not caught

**Symptom:** Custom exception returns generic 500 error

**Solution:** Ensure exception inherits from `ServiceException`:

```python
from services.exceptions import ServiceException

class MyCustomError(ServiceException):
    status_code = 400
    error_code = "CUSTOM_ERROR"
```

---

## Error Code Reference

Complete list of error codes: See [ADR-012](adr/ADR-012-error-handling-centralization.md#error-codes-reference)

---

## Additional Resources

- [ADR-012: Error Handling Centralization](adr/ADR-012-error-handling-centralization.md)
- [API Documentation](/docs/api)
- [Testing Guide](TESTING_GUIDE.md)
- [Security Guidelines](../SECURITY.md)

---

**Last Updated:** 2025-12-06  
**Maintainer:** Backend Team
