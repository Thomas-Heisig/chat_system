"""
Service Utilities

Common utility functions used across multiple services.
Reduces code duplication and provides consistent implementations.

See: docs/SERVICE_CONSOLIDATION_ANALYSIS.md
"""

import asyncio
import json
from datetime import datetime
from functools import wraps
from typing import Any, Dict, Optional

import requests

from config.settings import enhanced_logger


def check_endpoint_health(
    url: str, timeout: int = 5, method: str = "GET", expected_status: int = 200
) -> bool:
    """
    Check if an HTTP endpoint is healthy.

    Args:
        url: Endpoint URL to check
        timeout: Request timeout in seconds
        method: HTTP method to use
        expected_status: Expected successful status code

    Returns:
        True if endpoint responds with expected status, False otherwise

    Example:
        is_healthy = check_endpoint_health("http://localhost:11434/api/tags")
    """
    try:
        if method.upper() == "GET":
            response = requests.get(url, timeout=timeout)
        elif method.upper() == "POST":
            response = requests.post(url, timeout=timeout, json={})
        elif method.upper() == "HEAD":
            response = requests.head(url, timeout=timeout)
        else:
            raise ValueError(f"Unsupported HTTP method: {method}")

        return response.status_code == expected_status

    except requests.exceptions.Timeout:
        enhanced_logger.warning("Endpoint health check timeout", url=url, timeout=timeout)
        return False
    except requests.exceptions.ConnectionError:
        enhanced_logger.warning("Endpoint health check connection error", url=url)
        return False
    except Exception as e:
        enhanced_logger.error("Endpoint health check failed", url=url, error=str(e))
        return False


def format_service_error(
    service_name: str, operation: str, error: Exception, context: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Format a service error into a consistent structure.

    Args:
        service_name: Name of the service
        operation: Operation that failed
        error: Exception that occurred
        context: Additional context information

    Returns:
        Formatted error dictionary

    Example:
        error_dict = format_service_error(
            "MessageService",
            "create_message",
            ValueError("Invalid content"),
            {"user_id": 123}
        )
    """
    error_dict = {
        "status": "error",
        "service": service_name,
        "operation": operation,
        "error": {
            "type": error.__class__.__name__,
            "message": str(error),
        },
        "timestamp": datetime.now().isoformat(),
    }

    if context:
        error_dict["context"] = context

    # Log the error
    enhanced_logger.error(
        f"Service error in {operation}",
        service=service_name,
        error_type=error.__class__.__name__,
        error_message=str(error),
        context=context,
    )

    return error_dict


def validate_required_fields(
    data: Dict[str, Any], required_fields: list, service_name: str = "Unknown"
) -> tuple[bool, Optional[str]]:
    """
    Validate that required fields are present in data.

    Args:
        data: Dictionary to validate
        required_fields: List of required field names
        service_name: Name of service for error messages

    Returns:
        Tuple of (is_valid, error_message)

    Example:
        is_valid, error = validate_required_fields(
            {"username": "john"},
            ["username", "email"],
            "UserService"
        )
        if not is_valid:
            raise ValueError(error)
    """
    missing_fields = [
        field for field in required_fields if field not in data or data[field] is None
    ]

    if missing_fields:
        error_msg = f"{service_name}: Missing required fields: " f"{', '.join(missing_fields)}"
        enhanced_logger.warning(
            "Validation failed: missing required fields",
            service=service_name,
            missing_fields=missing_fields,
        )
        return False, error_msg

    return True, None


def create_success_response(
    operation: str,
    data: Any,
    service_name: Optional[str] = None,
    metadata: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    Create a consistent success response structure.

    Args:
        operation: Operation that succeeded
        data: Response data
        service_name: Name of the service
        metadata: Additional metadata

    Returns:
        Formatted success response

    Example:
        response = create_success_response(
            "create_message",
            {"id": 123, "content": "Hello"},
            "MessageService",
            {"execution_time_ms": 45}
        )
    """
    response = {
        "status": "success",
        "operation": operation,
        "data": data,
        "timestamp": datetime.now().isoformat(),
    }

    if service_name:
        response["service"] = service_name

    if metadata:
        response["metadata"] = metadata

    return response


def safe_json_parse(
    json_string: str, default: Any = None, service_name: Optional[str] = None
) -> Any:
    """
    Safely parse JSON string with error handling.

    Args:
        json_string: JSON string to parse
        default: Default value if parsing fails
        service_name: Service name for logging

    Returns:
        Parsed JSON or default value

    Example:
        data = safe_json_parse('{"key": "value"}', default={})
    """
    try:
        return json.loads(json_string)
    except (json.JSONDecodeError, TypeError, ValueError) as e:
        if service_name:
            enhanced_logger.warning("JSON parsing failed", service=service_name, error=str(e))
        return default


def calculate_service_uptime(start_time: datetime) -> Dict[str, Any]:
    """
    Calculate service uptime statistics.

    Args:
        start_time: Service start timestamp

    Returns:
        Dictionary with uptime information

    Example:
        stats = calculate_service_uptime(service.initialized_at)
        print(f"Uptime: {stats['uptime_human']}")
    """
    now = datetime.now()
    uptime_seconds = (now - start_time).total_seconds()

    hours = int(uptime_seconds // 3600)
    minutes = int((uptime_seconds % 3600) // 60)
    seconds = int(uptime_seconds % 60)

    return {
        "uptime_seconds": uptime_seconds,
        "uptime_human": f"{hours}h {minutes}m {seconds}s",
        "started_at": start_time.isoformat(),
        "current_time": now.isoformat(),
    }


def retry_with_backoff(
    func,
    max_retries: int = 3,
    initial_delay: float = 1.0,
    backoff_factor: float = 2.0,
    service_name: Optional[str] = None,
):
    """
    Decorator to retry a function with exponential backoff.

    Args:
        func: Function to retry
        max_retries: Maximum number of retries
        initial_delay: Initial delay in seconds
        backoff_factor: Backoff multiplier
        service_name: Service name for logging

    Example:
        @retry_with_backoff(max_retries=3)
        async def fetch_data():
            return await external_api.get_data()
    """

    @wraps(func)
    async def wrapper(*args, **kwargs):
        delay = initial_delay
        last_exception = None

        for attempt in range(max_retries):
            try:
                return await func(*args, **kwargs)
            except Exception as e:
                last_exception = e

                if service_name:
                    enhanced_logger.warning(
                        f"Retry attempt {attempt + 1}/{max_retries}",
                        service=service_name,
                        function=func.__name__,
                        error=str(e),
                        next_retry_delay=delay,
                    )

                if attempt < max_retries - 1:
                    await asyncio.sleep(delay)
                    delay *= backoff_factor

        # All retries failed
        if service_name:
            enhanced_logger.error(
                f"All retries failed after {max_retries} attempts",
                service=service_name,
                function=func.__name__,
                error=str(last_exception),
            )

        raise last_exception

    return wrapper


def truncate_for_logging(data: Any, max_length: int = 200, placeholder: str = "...") -> str:
    """
    Truncate data for safe logging.

    Args:
        data: Data to truncate
        max_length: Maximum length
        placeholder: Placeholder for truncated content

    Returns:
        Truncated string representation

    Example:
        log_data = truncate_for_logging(large_text, max_length=100)
    """
    data_str = str(data)

    if len(data_str) <= max_length:
        return data_str

    truncate_point = max_length - len(placeholder)
    return data_str[:truncate_point] + placeholder


def batch_items(items: list, batch_size: int):
    """
    Split items into batches.

    Args:
        items: List of items to batch
        batch_size: Size of each batch

    Yields:
        Batches of items

    Example:
        for batch in batch_items(large_list, batch_size=100):
            process_batch(batch)
    """
    for i in range(0, len(items), batch_size):
        yield items[i : i + batch_size]


def merge_configs(
    default_config: Dict[str, Any], user_config: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Merge user configuration with defaults.

    Args:
        default_config: Default configuration
        user_config: User-provided configuration

    Returns:
        Merged configuration (user config overrides defaults)

    Example:
        config = merge_configs(
            {"timeout": 5, "retries": 3},
            {"timeout": 10}  # Override timeout, keep retries
        )
    """
    merged = default_config.copy()

    if user_config:
        merged.update(user_config)

    return merged
