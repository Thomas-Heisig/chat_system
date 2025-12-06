"""
Sentry Error Tracking Configuration

This module configures Sentry for error tracking and performance monitoring.
Sentry provides:
- Error tracking and aggregation
- Performance monitoring
- Release tracking
- User context
- Breadcrumbs for debugging

Author: Chat System Team
Date: 2025-12-06
"""

import logging
from typing import Optional

from config.settings import settings

# Try to import sentry_sdk
try:
    import sentry_sdk
    from sentry_sdk.integrations.fastapi import FastApiIntegration
    from sentry_sdk.integrations.logging import LoggingIntegration
    from sentry_sdk.integrations.redis import RedisIntegration
    from sentry_sdk.integrations.sqlalchemy import SqlalchemyIntegration

    SENTRY_AVAILABLE = True
except ImportError:
    SENTRY_AVAILABLE = False
    sentry_sdk = None


def init_sentry(
    dsn: Optional[str] = None,
    environment: Optional[str] = None,
    traces_sample_rate: float = 0.1,
    profiles_sample_rate: float = 0.1,
) -> bool:
    """
    Initialize Sentry SDK for error and performance tracking

    Args:
        dsn: Sentry DSN (Data Source Name). If None, uses SENTRY_DSN from settings
        environment: Environment name (development, staging, production).
                    If None, uses APP_ENVIRONMENT from settings
        traces_sample_rate: Percentage of transactions to sample (0.0 to 1.0)
        profiles_sample_rate: Percentage of transactions to profile (0.0 to 1.0)

    Returns:
        True if Sentry was initialized successfully, False otherwise
    """
    if not SENTRY_AVAILABLE:
        logging.warning(
            "Sentry SDK not installed. Error tracking disabled. "
            "Install with: pip install sentry-sdk"
        )
        return False

    # Get DSN from parameter or settings
    sentry_dsn = dsn or getattr(settings, "SENTRY_DSN", None)

    if not sentry_dsn:
        logging.info("Sentry DSN not configured. Error tracking disabled.")
        return False

    # Get environment
    env = environment or settings.APP_ENVIRONMENT

    # Configure logging integration
    logging_integration = LoggingIntegration(
        level=logging.INFO,  # Capture info and above as breadcrumbs
        event_level=logging.ERROR,  # Send errors as events
    )

    # Initialize Sentry
    try:
        sentry_sdk.init(
            dsn=sentry_dsn,
            environment=env,
            release=f"{settings.APP_NAME}@{settings.APP_VERSION}",
            # Integrations
            integrations=[
                FastApiIntegration(
                    transaction_style="url",  # Use URL path as transaction name
                    failed_request_status_codes=[500, 599],  # Report 5xx as errors
                ),
                logging_integration,
                SqlalchemyIntegration(),
                RedisIntegration(),
            ],
            # Performance Monitoring
            traces_sample_rate=traces_sample_rate,
            # Profiling (CPU, memory)
            profiles_sample_rate=profiles_sample_rate,
            # Options
            send_default_pii=False,  # Don't send PII by default
            attach_stacktrace=True,  # Attach stack traces to messages
            debug=settings.APP_DEBUG,  # Enable debug mode in development
            # Set max_breadcrumbs
            max_breadcrumbs=50,
            # Set before_send callback to filter events
            before_send=before_send_filter,
        )

        # Set tags for context
        sentry_sdk.set_tag("app.name", settings.APP_NAME)
        sentry_sdk.set_tag("app.version", settings.APP_VERSION)

        logging.info(
            f"Sentry initialized successfully for environment: {env}, "
            f"traces_sample_rate: {traces_sample_rate}"
        )
        return True

    except Exception as e:
        logging.error(f"Failed to initialize Sentry: {e}")
        return False


def before_send_filter(event, hint):
    """
    Filter events before sending to Sentry

    This function can be used to:
    - Filter out certain errors
    - Modify events before sending
    - Add additional context

    Args:
        event: The event dictionary
        hint: Additional information about the event

    Returns:
        Modified event or None to drop the event
    """
    # Filter out common expected errors that shouldn't be reported
    if "exc_info" in hint:
        exc_type, exc_value, tb = hint["exc_info"]

        # Don't report validation errors
        if exc_type.__name__ in ["ValidationError", "RequestValidationError"]:
            return None

        # Don't report 404 errors
        if exc_type.__name__ == "HTTPException":
            if hasattr(exc_value, "status_code") and exc_value.status_code == 404:
                return None

    return event


def set_user_context(user_id: Optional[str] = None, username: Optional[str] = None):
    """
    Set user context for Sentry events

    Args:
        user_id: User ID
        username: Username
    """
    if not SENTRY_AVAILABLE or not sentry_sdk:
        return

    user_data = {}
    if user_id:
        user_data["id"] = user_id
    if username:
        user_data["username"] = username

    if user_data:
        sentry_sdk.set_user(user_data)


def add_breadcrumb(
    message: str,
    category: str = "default",
    level: str = "info",
    data: Optional[dict] = None,
):
    """
    Add a breadcrumb for debugging

    Breadcrumbs are trail of events that happened before an error.

    Args:
        message: Breadcrumb message
        category: Category (e.g., "auth", "query", "http")
        level: Level (debug, info, warning, error)
        data: Additional data dictionary
    """
    if not SENTRY_AVAILABLE or not sentry_sdk:
        return

    sentry_sdk.add_breadcrumb(
        message=message, category=category, level=level, data=data or {}
    )


def capture_exception(error: Exception, **kwargs):
    """
    Manually capture an exception

    Args:
        error: The exception to capture
        **kwargs: Additional context
    """
    if not SENTRY_AVAILABLE or not sentry_sdk:
        logging.error(f"Error: {error}", exc_info=True)
        return

    # Add tags from kwargs
    with sentry_sdk.push_scope() as scope:
        for key, value in kwargs.items():
            scope.set_tag(key, value)

        sentry_sdk.capture_exception(error)


def capture_message(message: str, level: str = "info", **kwargs):
    """
    Capture a message (not an exception)

    Args:
        message: The message to capture
        level: Severity level (debug, info, warning, error, fatal)
        **kwargs: Additional context
    """
    if not SENTRY_AVAILABLE or not sentry_sdk:
        logging.log(getattr(logging, level.upper()), message)
        return

    with sentry_sdk.push_scope() as scope:
        for key, value in kwargs.items():
            scope.set_tag(key, value)

        sentry_sdk.capture_message(message, level=level)


# Initialize Sentry if DSN is configured
if settings.SENTRY_DSN:
    # Auto-initialize in production
    if settings.APP_ENVIRONMENT == "production":
        init_sentry(traces_sample_rate=0.2, profiles_sample_rate=0.1)
    elif settings.APP_ENVIRONMENT == "staging":
        init_sentry(traces_sample_rate=0.5, profiles_sample_rate=0.2)
    # Don't auto-initialize in development to avoid noise
