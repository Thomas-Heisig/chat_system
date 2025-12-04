"""
ID generation utilities
"""

import uuid
from datetime import datetime


def generate_id(prefix: str = "") -> str:
    """
    Generate a unique ID with optional prefix.

    Args:
        prefix: Optional prefix for the ID

    Returns:
        Unique ID string
    """
    unique_id = str(uuid.uuid4())
    if prefix:
        return f"{prefix}_{unique_id}"
    return unique_id


def generate_timestamp_id(prefix: str = "") -> str:
    """
    Generate ID with timestamp component.

    Args:
        prefix: Optional prefix for the ID

    Returns:
        ID string with timestamp
    """
    timestamp = int(datetime.now().timestamp() * 1000)
    unique_suffix = str(uuid.uuid4())[:8]

    if prefix:
        return f"{prefix}_{timestamp}_{unique_suffix}"
    return f"{timestamp}_{unique_suffix}"
