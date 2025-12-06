"""
Centralized Error Handling for FastAPI Application

This module provides consistent error handling across the application:
- Unified error response format
- Comprehensive logging
- Production-safe error messages
- Request context tracking
- Error categorization

See: ADR-012-error-handling-centralization.md
"""

import time
import traceback
from datetime import datetime
from typing import Any, Dict, Optional, Union

from fastapi import HTTPException, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pydantic import ValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException

from config.settings import enhanced_logger, logger, settings
from services.exceptions import ServiceException


# ============================================================================
# Error Response Models
# ============================================================================


class ErrorResponse:
    """
    Standardized error response structure.

    Provides consistent format for all API errors with:
    - Clear error identification
    - Request context
    - Helpful debugging information (when appropriate)
    - Security considerations (no sensitive data leakage)
    """

    @staticmethod
    def create(
        status_code: int,
        message: str,
        error_code: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
        request: Optional[Request] = None,
        exception: Optional[Exception] = None,
        include_trace: bool = False,
    ) -> Dict[str, Any]:
        """
        Create standardized error response.

        Args:
            status_code: HTTP status code
            message: Human-readable error message
            error_code: Application-specific error code
            details: Additional error details
            request: FastAPI request object
            exception: Original exception (for logging)
            include_trace: Include stack trace (only in debug mode)

        Returns:
            Dictionary with standardized error structure
        """
        timestamp = datetime.now()

        # Base response structure
        response = {
            "error": True,
            "status_code": status_code,
            "error_code": error_code or ErrorResponse._get_default_error_code(status_code),
            "message": message,
            "timestamp": timestamp.isoformat(),
            "timestamp_unix": time.time(),
        }

        # Add request context if available
        if request:
            response["request"] = {
                "method": request.method,
                "path": request.url.path,
                "query": str(request.url.query) if request.url.query else None,
            }

            # Add client info (be cautious with IP logging for GDPR)
            if request.client:
                response["request"]["client_host"] = request.client.host

        # Add additional details if provided
        if details:
            response["details"] = details

        # Add stack trace in debug mode only
        if include_trace and settings.APP_DEBUG and exception:
            response["debug"] = {
                "exception_type": exception.__class__.__name__,
                "exception_module": exception.__class__.__module__,
                "traceback": traceback.format_exc(),
            }

        # Add help URL for documentation
        if error_code:
            response["help_url"] = f"/docs/errors/{error_code.lower()}"

        return response

    @staticmethod
    def _get_default_error_code(status_code: int) -> str:
        """Get default error code based on HTTP status code"""
        error_codes = {
            400: "BAD_REQUEST",
            401: "UNAUTHORIZED",
            403: "FORBIDDEN",
            404: "NOT_FOUND",
            405: "METHOD_NOT_ALLOWED",
            409: "CONFLICT",
            422: "VALIDATION_ERROR",
            429: "RATE_LIMIT_EXCEEDED",
            500: "INTERNAL_ERROR",
            502: "BAD_GATEWAY",
            503: "SERVICE_UNAVAILABLE",
            504: "GATEWAY_TIMEOUT",
        }
        return error_codes.get(status_code, "UNKNOWN_ERROR")


# ============================================================================
# Exception Handlers
# ============================================================================


async def service_exception_handler(request: Request, exc: ServiceException) -> JSONResponse:
    """
    Handle ServiceException (custom application exceptions).

    These are expected errors that are part of the application's business logic.
    They should be logged at WARNING level and return appropriate HTTP responses.
    """
    enhanced_logger.warning(
        "Service exception occurred",
        error_code=exc.error_code,
        error_message=exc.message,
        status_code=exc.status_code,
        method=request.method,
        url=str(request.url),
        details=exc.details,
    )

    response = ErrorResponse.create(
        status_code=exc.status_code,
        message=exc.message,
        error_code=exc.error_code,
        details=exc.details,
        request=request,
    )

    return JSONResponse(
        status_code=exc.status_code,
        content=response,
        headers={"X-Error-Code": exc.error_code, "X-Error-Type": "ServiceException"},
    )


async def http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
    """
    Handle FastAPI HTTPException.

    These are standard HTTP exceptions raised by FastAPI or manually in routes.
    """
    enhanced_logger.warning(
        "HTTP exception",
        status_code=exc.status_code,
        detail=exc.detail,
        method=request.method,
        url=str(request.url),
        client_host=request.client.host if request.client else "unknown",
    )

    response = ErrorResponse.create(
        status_code=exc.status_code, message=exc.detail, request=request
    )

    return JSONResponse(
        status_code=exc.status_code, content=response, headers={"X-Error-Type": "HTTPException"}
    )


async def validation_exception_handler(
    request: Request, exc: Union[RequestValidationError, ValidationError]
) -> JSONResponse:
    """
    Handle Pydantic validation errors.

    These occur when request data doesn't match expected schema.
    Provide detailed field-level validation errors to help clients.
    """
    # Extract validation errors
    errors = []
    for error in exc.errors():
        errors.append(
            {
                "field": ".".join(str(loc) for loc in error["loc"]),
                "message": error["msg"],
                "type": error["type"],
            }
        )

    enhanced_logger.warning(
        "Validation error",
        error_count=len(errors),
        errors=errors,
        method=request.method,
        url=str(request.url),
    )

    response = ErrorResponse.create(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        message="Request validation failed",
        error_code="VALIDATION_ERROR",
        details={"validation_errors": errors},
        request=request,
    )

    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content=response,
        headers={"X-Error-Type": "ValidationError", "X-Validation-Error-Count": str(len(errors))},
    )


async def global_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """
    Handle unexpected exceptions.

    These are genuine errors that shouldn't happen in normal operation.
    Log at ERROR level with full stack trace and return generic error to client.
    """
    # Log the full exception with stack trace
    enhanced_logger.error(
        "Unhandled exception",
        error=str(exc),
        error_type=type(exc).__name__,
        error_module=exc.__class__.__module__,
        method=request.method,
        url=str(request.url),
        client_host=request.client.host if request.client else "unknown",
        stack_trace=traceback.format_exc(),
    )

    # In production, don't expose internal error details
    if settings.APP_DEBUG:
        error_message = f"{exc.__class__.__name__}: {str(exc)}"
        include_trace = True
    else:
        error_message = "An internal server error occurred. Please try again later."
        include_trace = False

    response = ErrorResponse.create(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        message=error_message,
        request=request,
        exception=exc,
        include_trace=include_trace,
    )

    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content=response,
        headers={
            "X-Error-Type": "UnhandledException",
            "X-Error-ID": f"err_{int(time.time())}",  # For support tracking
        },
    )


# ============================================================================
# Exception Handler Registration
# ============================================================================


def register_exception_handlers(app):
    """
    Register all exception handlers with FastAPI application.

    Call this function during application startup:
        app = FastAPI()
        register_exception_handlers(app)

    Args:
        app: FastAPI application instance
    """
    # Custom service exceptions (highest priority)
    app.add_exception_handler(ServiceException, service_exception_handler)

    # FastAPI built-in exceptions
    app.add_exception_handler(HTTPException, http_exception_handler)
    app.add_exception_handler(StarletteHTTPException, http_exception_handler)

    # Validation errors
    app.add_exception_handler(RequestValidationError, validation_exception_handler)
    app.add_exception_handler(ValidationError, validation_exception_handler)

    # Catch-all for unexpected exceptions (lowest priority)
    app.add_exception_handler(Exception, global_exception_handler)

    logger.info("✅ Exception handlers registered successfully")


# ============================================================================
# Error Logging Utilities
# ============================================================================


def log_error_with_context(error: Exception, context: Dict[str, Any], level: str = "error") -> None:
    """
    Log error with additional context.

    Args:
        error: Exception that occurred
        context: Additional context information
        level: Log level (error, warning, info)
    """
    log_func = getattr(enhanced_logger, level, enhanced_logger.error)

    log_func(
        f"Error occurred: {error.__class__.__name__}",
        error_message=str(error),
        error_type=error.__class__.__name__,
        **context,
    )


def sanitize_error_for_logging(error_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Remove sensitive information from error data before logging.

    Args:
        error_data: Error data dictionary

    Returns:
        Sanitized error data
    """
    sensitive_keys = [
        "password",
        "token",
        "api_key",
        "secret",
        "authorization",
        "credit_card",
        "ssn",
    ]

    sanitized = error_data.copy()

    for key in sanitized:
        if any(sensitive in key.lower() for sensitive in sensitive_keys):
            sanitized[key] = "***REDACTED***"

    return sanitized


# ============================================================================
# Error Monitoring Helpers
# ============================================================================


class ErrorMetrics:
    """
    Track error metrics for monitoring.

    Can be integrated with Prometheus or other monitoring systems.
    """

    def __init__(self):
        self.error_counts = {}
        self.last_errors = []
        self.max_history = 100

    def record_error(self, error_type: str, error_code: str, status_code: int) -> None:
        """Record an error occurrence"""
        key = f"{error_type}:{error_code}"
        self.error_counts[key] = self.error_counts.get(key, 0) + 1

        self.last_errors.append(
            {
                "error_type": error_type,
                "error_code": error_code,
                "status_code": status_code,
                "timestamp": datetime.now().isoformat(),
            }
        )

        # Keep only recent errors
        if len(self.last_errors) > self.max_history:
            self.last_errors = self.last_errors[-self.max_history :]

    def get_metrics(self) -> Dict[str, Any]:
        """Get current error metrics"""
        return {
            "total_errors": sum(self.error_counts.values()),
            "error_counts": self.error_counts,
            "recent_errors": self.last_errors[-10:],
        }


# Global error metrics instance
error_metrics = ErrorMetrics()


# ============================================================================
# Convenience Functions
# ============================================================================


def raise_not_found(resource_type: str, resource_id: Optional[str] = None) -> None:
    """
    Convenience function to raise ResourceNotFoundError.

    Example:
        user = get_user(user_id)
        if not user:
            raise_not_found("User", user_id)
    """
    from services.exceptions import ResourceNotFoundError

    raise ResourceNotFoundError(resource_type, resource_id)


def raise_validation_error(message: str, field_errors: Optional[Dict[str, str]] = None) -> None:
    """
    Convenience function to raise ValidationError.

    Example:
        if not email:
            raise_validation_error("Email is required", {"email": "Required field"})
    """
    from services.exceptions import ValidationError

    raise ValidationError(message, field_errors)


def raise_unauthorized(message: str = "Authentication required") -> None:
    """
    Convenience function to raise AuthenticationError.

    Example:
        if not token:
            raise_unauthorized("Missing authentication token")
    """
    from services.exceptions import AuthenticationError

    raise AuthenticationError(message)


def raise_forbidden(message: str = "Access denied") -> None:
    """
    Convenience function to raise AuthorizationError.

    Example:
        if user.role != "admin":
            raise_forbidden("Admin access required")
    """
    from services.exceptions import AuthorizationError

    raise AuthorizationError(message)
