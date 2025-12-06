# ADR-012: Error Handling Centralization

**Status:** Accepted  
**Date:** 2025-12-06  
**Decision Makers:** Backend Team, Security Team  
**Tags:** #architecture #error-handling #api #security

---

## Context

### Current State

The chat system's error handling is inconsistent across the codebase:

**Problems Identified:**

1. **Inconsistent Error Responses**
   ```python
   # Route A
   raise HTTPException(status_code=500, detail=str(e))
   
   # Route B
   return {"error": "Something went wrong"}
   
   # Route C
   raise ServiceException(...)
   ```

2. **Information Leakage**
   - Stack traces exposed in production
   - Internal error details visible to clients
   - Database schema revealed in error messages
   - Security risk: helps attackers understand system

3. **Poor Error Tracking**
   - No consistent error logging
   - Difficult to monitor error rates
   - No correlation between errors
   - Hard to debug production issues

4. **Client Confusion**
   - Different error formats per endpoint
   - Unclear error messages
   - No error codes for handling
   - Missing request context

5. **Code Duplication**
   - Similar try-catch patterns everywhere
   - Repeated error formatting logic
   - Duplicate logging code

### Requirements

1. **Consistency:** Uniform error response format
2. **Security:** No sensitive data leakage
3. **Debuggability:** Comprehensive logging for developers
4. **Client-Friendly:** Clear, actionable error messages
5. **Monitoring:** Easy to track and analyze errors
6. **Maintainability:** Centralized error logic

---

## Decision

We will implement a **centralized error handling system** with:

### 1. Standardized Error Response Format

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
        "path": "/api/users/123"
    },
    "details": {
        "resource_type": "User",
        "resource_id": "123"
    },
    "help_url": "/docs/errors/resource_not_found"
}
```

### 2. Exception Hierarchy

**Existing:** `services/exceptions.py` with:
- `ServiceException` - Base class
- Specific exceptions (e.g., `ValidationError`, `ResourceNotFoundError`)
- HTTP status code mapping
- Structured error details

**Enhancement:** Use existing hierarchy consistently

### 3. Global Exception Handlers

**File:** `core/error_handlers.py`

Handler priority:
1. `ServiceException` - Application errors (expected)
2. `HTTPException` - FastAPI standard exceptions
3. `ValidationError` - Pydantic validation errors
4. `Exception` - Catch-all for unexpected errors

### 4. Error Response Builder

```python
class ErrorResponse:
    @staticmethod
    def create(
        status_code: int,
        message: str,
        error_code: Optional[str] = None,
        details: Optional[Dict] = None,
        request: Optional[Request] = None,
        exception: Optional[Exception] = None
    ) -> Dict[str, Any]:
        # Standardized error structure
        ...
```

### 5. Security Considerations

**Production Mode:**
- Generic error messages
- No stack traces
- Sanitized details
- No internal paths

**Debug Mode:**
- Detailed error messages
- Full stack traces
- Complete exception info
- Request/response data

---

## Consequences

### Positive

✅ **Consistent API**
- All endpoints return same error format
- Clients can handle errors uniformly
- Better developer experience

✅ **Improved Security**
- No sensitive data leakage
- Production-safe error messages
- Controlled information disclosure
- GDPR compliance support

✅ **Better Monitoring**
- Centralized error logging
- Error metrics collection
- Easy integration with monitoring tools
- Error rate tracking

✅ **Enhanced Debugging**
- Comprehensive error context
- Full stack traces in debug mode
- Request/response correlation
- Error categorization

✅ **Reduced Code Duplication**
- Single error handling logic
- Reusable error builders
- Consistent logging patterns

✅ **Client-Friendly**
- Clear error messages
- Error codes for programmatic handling
- Help URLs for documentation
- Actionable error details

### Negative

❌ **Migration Effort**
- Need to update existing error handling
- Replace HTTPException with ServiceException
- Update tests
- Time investment

❌ **Learning Curve**
- Team needs to learn new exception types
- Understanding error hierarchy
- Knowing which exception to raise

❌ **Slight Overhead**
- Additional processing for error responses
- More detailed logging
- Negligible performance impact

### Neutral

⚪ **Breaking Changes**
- Error response format changes
- May affect existing clients
- Need migration guide

**Mitigation:** Version API or provide transition period

---

## Alternatives Considered

### 1. Status Quo (Current System)

**Pros:**
- No changes needed
- Team familiar with it

**Cons:**
- All current problems persist
- Technical debt increases
- Security risks remain

**Why Rejected:** Not sustainable long-term

### 2. Third-Party Error Handling Library

**Examples:** `fastapi-error-handler`, `starlette-errors`

**Pros:**
- Battle-tested
- Community support
- Feature-rich

**Cons:**
- External dependency
- May not fit our needs
- Less control
- Learning curve

**Why Rejected:** Our requirements are specific, custom solution is better

### 3. Logging Only (No Format Changes)

**Pros:**
- Minimal changes
- Easy to implement
- No API changes

**Cons:**
- Doesn't solve consistency issues
- Still confusing for clients
- Doesn't improve security

**Why Rejected:** Doesn't address core problems

### 4. Microservices-Style Error Service

**Pros:**
- Complete separation
- Independent scaling
- Advanced features

**Cons:**
- Over-engineering
- Network overhead
- Added complexity
- Overkill for current scale

**Why Rejected:** Too complex for current needs

---

## Implementation

### Phase 1: Core Infrastructure (Week 1)

**Tasks:**
1. ✅ Create `core/error_handlers.py`
2. ✅ Implement `ErrorResponse` class
3. ✅ Create exception handlers
4. ✅ Add registration function

**Code:**
```python
from core.error_handlers import register_exception_handlers

app = FastAPI()
register_exception_handlers(app)
```

### Phase 2: Update Routes (Week 2)

**Migration Pattern:**

```python
# Before
try:
    user = get_user(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
except Exception as e:
    raise HTTPException(status_code=500, detail=str(e))

# After
from services.exceptions import ResourceNotFoundError

user = get_user(user_id)
if not user:
    raise ResourceNotFoundError("User", user_id)
# Global handler catches and formats error
```

**Priority:**
1. High-traffic endpoints (messages, chat)
2. Authentication endpoints
3. Admin endpoints
4. Remaining endpoints

### Phase 3: Testing & Documentation (Week 3)

**Tasks:**
1. Update tests for new error format
2. Document error codes
3. Create error handling guide
4. Update API documentation

---

## Error Codes Reference

### Client Errors (4xx)

| Code | Status | Description |
|------|--------|-------------|
| BAD_REQUEST | 400 | Invalid request format |
| VALIDATION_ERROR | 422 | Input validation failed |
| UNAUTHORIZED | 401 | Authentication required |
| FORBIDDEN | 403 | Insufficient permissions |
| NOT_FOUND | 404 | Resource not found |
| CONFLICT | 409 | Resource conflict |
| RATE_LIMIT_EXCEEDED | 429 | Too many requests |

### Server Errors (5xx)

| Code | Status | Description |
|------|--------|-------------|
| INTERNAL_ERROR | 500 | Internal server error |
| DATABASE_ERROR | 500 | Database operation failed |
| EXTERNAL_SERVICE_ERROR | 502 | External service failed |
| SERVICE_UNAVAILABLE | 503 | Service temporarily down |

---

## Usage Examples

### Raising Errors

```python
# Resource not found
from services.exceptions import ResourceNotFoundError
raise ResourceNotFoundError("User", user_id)

# Validation error
from services.exceptions import ValidationError
raise ValidationError("Invalid email", {"email": "Must be valid email"})

# Using convenience functions
from core.error_handlers import raise_not_found, raise_forbidden
raise_not_found("Project", project_id)
raise_forbidden("Admin access required")
```

### Testing Errors

```python
def test_user_not_found():
    response = client.get("/users/999")
    assert response.status_code == 404
    error = response.json()
    assert error["error"] is True
    assert error["error_code"] == "RESOURCE_NOT_FOUND"
    assert "User" in error["message"]
```

### Client Error Handling (JavaScript)

```javascript
try {
    const response = await fetch('/api/users/123');
    const data = await response.json();
    
    if (data.error) {
        // Handle error based on error_code
        switch (data.error_code) {
            case 'RESOURCE_NOT_FOUND':
                showNotFoundMessage();
                break;
            case 'UNAUTHORIZED':
                redirectToLogin();
                break;
            default:
                showGenericError(data.message);
        }
    }
} catch (error) {
    showNetworkError();
}
```

---

## Monitoring & Alerting

### Metrics to Track

```python
# Error rates by endpoint
errors_by_endpoint = {
    "/api/messages": {"count": 10, "rate": 0.01},
    "/api/users": {"count": 5, "rate": 0.005}
}

# Error rates by type
errors_by_type = {
    "VALIDATION_ERROR": 50,
    "RESOURCE_NOT_FOUND": 30,
    "INTERNAL_ERROR": 2  # Alert if > 5!
}

# Error response times
error_response_time_p95 = 120  # ms
```

### Alerts

1. **Critical:** 500 errors > 1% of requests
2. **Warning:** 404 errors > 5% of requests
3. **Info:** New error type detected
4. **Warning:** Error rate spike (2x normal)

---

## Security Best Practices

### DO ✅

1. **Log all errors** with full context (server-side only)
2. **Sanitize responses** in production
3. **Use error codes** instead of detailed messages
4. **Rate limit** error responses (prevent DoS)
5. **Monitor** for suspicious error patterns

### DON'T ❌

1. **Don't expose** internal paths or structure
2. **Don't leak** database schemas
3. **Don't include** stack traces in production
4. **Don't reveal** system versions
5. **Don't expose** user existence (timing attacks)

---

## Migration Checklist

- [x] Create error handling infrastructure
- [x] Document error codes and patterns
- [ ] Update high-priority routes
- [ ] Update tests
- [ ] Update API documentation
- [ ] Deploy to staging
- [ ] Monitor for issues
- [ ] Deploy to production
- [ ] Update client libraries

---

## References

- [FastAPI Exception Handling](https://fastapi.tiangolo.com/tutorial/handling-errors/)
- [OWASP Error Handling](https://cheatsheetseries.owasp.org/cheatsheets/Error_Handling_Cheat_Sheet.html)
- [HTTP Status Codes](https://developer.mozilla.org/en-US/docs/Web/HTTP/Status)
- [REST API Error Handling](https://www.baeldung.com/rest-api-error-handling-best-practices)

---

## Related ADRs

- [ADR-010: Dependency Injection Pattern](ADR-010-dependency-injection-pattern.md)
- [ADR-011: Service Consolidation Strategy](ADR-011-service-consolidation-strategy.md)
- [ADR-013: Logging Standards](ADR-013-logging-standards.md) (future)

---

## Approval

- [x] Backend Team
- [x] Security Team
- [x] Frontend Team
- [x] DevOps Team

**Approved by:** Technical Lead  
**Date:** 2025-12-06  
**Status:** ✅ Approved for implementation

---

**End of ADR-012**
