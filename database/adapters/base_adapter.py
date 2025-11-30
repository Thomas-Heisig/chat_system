# database/adapters/base_adapter.py
"""
Base Database Adapter Interface
Abstract base class for all database adapters
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
from datetime import datetime


class BaseDatabaseAdapter(ABC):
    """
    Abstract base class for database adapters.
    All database adapters must implement this interface.
    """
    
    def __init__(self, config: Dict[str, Any]):
        """Initialize adapter with configuration"""
        self.config = config
        self._connected = False
        self._connection = None
    
    @abstractmethod
    async def connect(self) -> bool:
        """
        Establish connection to the database.
        Returns True if connection successful.
        """
        pass
    
    @abstractmethod
    async def disconnect(self) -> None:
        """Close database connection and cleanup resources"""
        pass
    
    @abstractmethod
    async def health_check(self) -> Dict[str, Any]:
        """
        Perform health check on database connection.
        Returns dict with status and details.
        """
        pass
    
    @abstractmethod
    async def get_stats(self) -> Dict[str, Any]:
        """
        Get database statistics.
        Returns dict with various metrics.
        """
        pass
    
    @abstractmethod
    async def execute(self, query: str, params: Optional[tuple] = None) -> Any:
        """Execute a query and return results"""
        pass
    
    @abstractmethod
    async def execute_many(self, query: str, params_list: List[tuple]) -> int:
        """Execute a query with multiple parameter sets"""
        pass
    
    @abstractmethod
    async def fetch_one(self, query: str, params: Optional[tuple] = None) -> Optional[Dict[str, Any]]:
        """Fetch single row from database"""
        pass
    
    @abstractmethod
    async def fetch_all(self, query: str, params: Optional[tuple] = None) -> List[Dict[str, Any]]:
        """Fetch all rows from database"""
        pass
    
    @abstractmethod
    async def begin_transaction(self):
        """Begin a database transaction"""
        pass
    
    @abstractmethod
    async def commit(self):
        """Commit the current transaction"""
        pass
    
    @abstractmethod
    async def rollback(self):
        """Rollback the current transaction"""
        pass
    
    @abstractmethod
    async def create_tables(self) -> bool:
        """Create all necessary database tables"""
        pass
    
    @abstractmethod
    async def backup(self, backup_path: str) -> str:
        """Create database backup and return backup file path"""
        pass
    
    @abstractmethod
    async def restore(self, backup_path: str) -> bool:
        """Restore database from backup"""
        pass
    
    @property
    def is_connected(self) -> bool:
        """Check if adapter is connected to database"""
        return self._connected
    
    @property
    @abstractmethod
    def db_type(self) -> str:
        """Return the database type identifier"""
        pass
    
    @property
    @abstractmethod
    def db_version(self) -> str:
        """Return the database version"""
        pass
    
    def get_config(self) -> Dict[str, Any]:
        """Return sanitized configuration (without passwords)"""
        safe_config = self.config.copy()
        if 'password' in safe_config:
            safe_config['password'] = '***'
        return safe_config
    
    async def test_connection(self) -> Dict[str, Any]:
        """Test database connection and return status"""
        start_time = datetime.now()
        try:
            if not self._connected:
                await self.connect()
            
            health = await self.health_check()
            duration = (datetime.now() - start_time).total_seconds() * 1000
            
            return {
                "status": "connected",
                "db_type": self.db_type,
                "db_version": self.db_version,
                "response_time_ms": duration,
                "health": health
            }
        except Exception as e:
            duration = (datetime.now() - start_time).total_seconds() * 1000
            return {
                "status": "error",
                "db_type": self.db_type,
                "error": str(e),
                "response_time_ms": duration
            }


__all__ = ['BaseDatabaseAdapter']
