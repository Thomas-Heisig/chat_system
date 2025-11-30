# database/adapters/__init__.py
"""
Modular Database Adapters
Provides uniform interface for different database backends
"""

from typing import Type, Dict
from .base_adapter import BaseDatabaseAdapter
from .sqlite_adapter import SQLiteAdapter

# Registry of available adapters
ADAPTER_REGISTRY: Dict[str, Type[BaseDatabaseAdapter]] = {
    "sqlite": SQLiteAdapter,
}

# Try to import optional adapters
try:
    from .postgres_adapter import PostgresAdapter
    ADAPTER_REGISTRY["postgresql"] = PostgresAdapter
except ImportError:
    pass

try:
    from .mongodb_adapter import MongoDBAdapter
    ADAPTER_REGISTRY["mongodb"] = MongoDBAdapter
except ImportError:
    pass


def get_adapter(db_type: str) -> Type[BaseDatabaseAdapter]:
    """Get database adapter class by type"""
    adapter = ADAPTER_REGISTRY.get(db_type.lower())
    if not adapter:
        raise ValueError(f"Unsupported database type: {db_type}. Available: {list(ADAPTER_REGISTRY.keys())}")
    return adapter


def get_available_adapters() -> Dict[str, bool]:
    """Get list of available database adapters"""
    return {
        "sqlite": "sqlite" in ADAPTER_REGISTRY,
        "postgresql": "postgresql" in ADAPTER_REGISTRY,
        "mysql": "mysql" in ADAPTER_REGISTRY,
        "mongodb": "mongodb" in ADAPTER_REGISTRY
    }


__all__ = [
    'BaseDatabaseAdapter',
    'SQLiteAdapter',
    'get_adapter',
    'get_available_adapters',
    'ADAPTER_REGISTRY'
]
