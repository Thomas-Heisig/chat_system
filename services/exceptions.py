"""
Exception classes for the chat system services.

This module provides a centralized exception hierarchy that maps to HTTP status codes
and provides consistent error handling across the application.
"""

from typing import Any, Dict, Optional


class ServiceException(Exception):
    """
    Base exception for all service-related errors.
    
    Attributes:
        message: Human-readable error message
        status_code: HTTP status code to return
        error_code: Application-specific error code
        details: Additional error details
    """
    
    status_code: int = 500
    error_code: str = "INTERNAL_ERROR"
    
    def __init__(
        self,
        message: str = "An internal error occurred",
        details: Optional[Dict[str, Any]] = None
    ):
        self.message = message
        self.details = details or {}
        super().__init__(message)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert exception to dictionary for JSON response."""
        result = {
            "error": True,
            "error_code": self.error_code,
            "message": self.message,
            "status_code": self.status_code,
        }
        if self.details:
            result["details"] = self.details
        return result


# 400 Bad Request Errors
class BadRequestError(ServiceException):
    """Raised when client sends invalid request."""
    status_code = 400
    error_code = "BAD_REQUEST"


class ValidationError(ServiceException):
    """Raised when input validation fails."""
    status_code = 400
    error_code = "VALIDATION_ERROR"
    
    def __init__(self, message: str = "Validation failed", field_errors: Optional[Dict[str, str]] = None):
        details = {"field_errors": field_errors} if field_errors else {}
        super().__init__(message, details)


class InvalidInputError(ServiceException):
    """Raised when input data is invalid."""
    status_code = 400
    error_code = "INVALID_INPUT"


# 401 Unauthorized Errors
class AuthenticationError(ServiceException):
    """Raised when authentication fails."""
    status_code = 401
    error_code = "AUTHENTICATION_FAILED"
    
    def __init__(self, message: str = "Authentication failed"):
        super().__init__(message)


class InvalidCredentialsError(AuthenticationError):
    """Raised when credentials are invalid."""
    error_code = "INVALID_CREDENTIALS"
    
    def __init__(self, message: str = "Invalid username or password"):
        super().__init__(message)


class TokenExpiredError(AuthenticationError):
    """Raised when authentication token has expired."""
    error_code = "TOKEN_EXPIRED"
    
    def __init__(self, message: str = "Authentication token has expired"):
        super().__init__(message)


# 403 Forbidden Errors
class AuthorizationError(ServiceException):
    """Raised when user is not authorized for an action."""
    status_code = 403
    error_code = "AUTHORIZATION_FAILED"
    
    def __init__(self, message: str = "You are not authorized to perform this action"):
        super().__init__(message)


class InsufficientPermissionsError(AuthorizationError):
    """Raised when user lacks required permissions."""
    error_code = "INSUFFICIENT_PERMISSIONS"
    
    def __init__(self, required_permission: str = None):
        message = f"Insufficient permissions. Required: {required_permission}" if required_permission else "Insufficient permissions"
        super().__init__(message)


# 404 Not Found Errors
class ResourceNotFoundError(ServiceException):
    """Raised when a requested resource is not found."""
    status_code = 404
    error_code = "RESOURCE_NOT_FOUND"
    
    def __init__(self, resource_type: str, resource_id: str = None):
        self.resource_type = resource_type
        self.resource_id = resource_id
        
        if resource_id:
            message = f"{resource_type} with ID '{resource_id}' not found"
        else:
            message = f"{resource_type} not found"
        
        details = {"resource_type": resource_type}
        if resource_id:
            details["resource_id"] = resource_id
        
        super().__init__(message, details)


class UserNotFoundError(ResourceNotFoundError):
    """Raised when a user is not found."""
    def __init__(self, user_id: str = None):
        super().__init__("User", user_id)


class ProjectNotFoundError(ResourceNotFoundError):
    """Raised when a project is not found."""
    def __init__(self, project_id: str = None):
        super().__init__("Project", project_id)


class MessageNotFoundError(ResourceNotFoundError):
    """Raised when a message is not found."""
    def __init__(self, message_id: str = None):
        super().__init__("Message", message_id)


# 409 Conflict Errors
class ConflictError(ServiceException):
    """Raised when operation conflicts with current state."""
    status_code = 409
    error_code = "CONFLICT"


class DuplicateResourceError(ConflictError):
    """Raised when attempting to create a duplicate resource."""
    error_code = "DUPLICATE_RESOURCE"
    
    def __init__(self, resource_type: str, identifier: str = None):
        message = f"{resource_type} already exists"
        if identifier:
            message += f": {identifier}"
        super().__init__(message)


# 422 Unprocessable Entity
class UnprocessableEntityError(ServiceException):
    """Raised when request is well-formed but semantically incorrect."""
    status_code = 422
    error_code = "UNPROCESSABLE_ENTITY"


# 429 Too Many Requests
class RateLimitExceededError(ServiceException):
    """Raised when rate limit is exceeded."""
    status_code = 429
    error_code = "RATE_LIMIT_EXCEEDED"
    
    def __init__(self, message: str = "Rate limit exceeded", retry_after: int = None):
        details = {"retry_after": retry_after} if retry_after else {}
        super().__init__(message, details)


# 500 Internal Server Errors
class InternalServerError(ServiceException):
    """Raised for generic internal server errors."""
    status_code = 500
    error_code = "INTERNAL_ERROR"


class DatabaseError(ServiceException):
    """Raised when database operation fails."""
    status_code = 500
    error_code = "DATABASE_ERROR"


class DatabaseConnectionError(DatabaseError):
    """Raised when database connection fails."""
    error_code = "DATABASE_CONNECTION_ERROR"
    
    def __init__(self, message: str = "Failed to connect to database"):
        super().__init__(message)


# 502 Bad Gateway
class ExternalServiceError(ServiceException):
    """Raised when external service fails."""
    status_code = 502
    error_code = "EXTERNAL_SERVICE_ERROR"
    
    def __init__(self, service_name: str = None, message: str = None):
        self.service_name = service_name
        msg = message or f"External service failed: {service_name}" if service_name else "External service failed"
        details = {"service_name": service_name} if service_name else {}
        super().__init__(msg, details)


class ExternalAIUnavailableError(ExternalServiceError):
    """
    Raised when external AI service (Ollama, OpenAI, etc.) is unavailable.

    This exception is used to trigger fallback mechanisms like Elyza service
    when the primary AI service cannot be reached.

    Example:
        try:
            response = await ai_service.generate_response(prompt)
        except ExternalAIUnavailableError:
            # Fallback to Elyza or other simple response
            if ENABLE_ELYZA_FALLBACK:
                response = elyza_service.generate_response(prompt)
    """
    error_code = "AI_SERVICE_UNAVAILABLE"
    
    def __init__(self, service_name: str = None):
        message = f"AI service is unavailable: {service_name}" if service_name else "AI service is unavailable"
        super().__init__(service_name, message)


# 503 Service Unavailable
class ServiceUnavailableError(ServiceException):
    """Raised when service is temporarily unavailable."""
    status_code = 503
    error_code = "SERVICE_UNAVAILABLE"
    
    def __init__(self, message: str = "Service is temporarily unavailable", retry_after: int = None):
        details = {"retry_after": retry_after} if retry_after else {}
        super().__init__(message, details)


# Feature-specific errors
class FeatureDisabledError(ServiceException):
    """Raised when attempting to use a disabled feature."""
    status_code = 403
    error_code = "FEATURE_DISABLED"
    
    def __init__(self, feature_name: str):
        message = f"Feature is disabled: {feature_name}"
        super().__init__(message, {"feature_name": feature_name})


class ConfigurationError(ServiceException):
    """Raised when configuration is invalid."""
    status_code = 500
    error_code = "CONFIGURATION_ERROR"
