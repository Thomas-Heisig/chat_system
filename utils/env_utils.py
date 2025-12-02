"""
Environment variable parsing utilities
"""

import os
from typing import Optional


def parse_bool_env(key: str, default: bool = False) -> bool:
    """
    Parse environment variable as boolean.
    
    Args:
        key: Environment variable key
        default: Default value if not set
        
    Returns:
        Boolean value
    """
    value = os.getenv(key)
    if value is None:
        return default
    return value.lower() in ('true', '1', 'yes', 'on')


def parse_int_env(key: str, default: int = 0) -> int:
    """
    Parse environment variable as integer.
    
    Args:
        key: Environment variable key
        default: Default value if not set or invalid
        
    Returns:
        Integer value
    """
    value = os.getenv(key)
    if value is None:
        return default
    try:
        return int(value)
    except ValueError:
        return default
