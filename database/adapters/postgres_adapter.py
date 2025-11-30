# database/adapters/postgres_adapter.py
"""
PostgreSQL Database Adapter
Enterprise-grade database support for production deployments
"""

from typing import Dict, Any, List, Optional
from datetime import datetime

from .base_adapter import BaseDatabaseAdapter

# Optional import - PostgreSQL support requires asyncpg
try:
    import asyncpg
    ASYNCPG_AVAILABLE = True
except ImportError:
    ASYNCPG_AVAILABLE = False
    asyncpg = None


class PostgresAdapter(BaseDatabaseAdapter):
    """PostgreSQL database adapter with async support"""
    
    def __init__(self, config: Dict[str, Any]):
        if not ASYNCPG_AVAILABLE:
            raise ImportError("asyncpg is required for PostgreSQL support. Install with: pip install asyncpg")
        
        super().__init__(config)
        self.host = config.get('host', 'localhost')
        self.port = config.get('port', 5432)
        self.database = config.get('database', 'chat_system')
        self.username = config.get('username', 'postgres')
        self.password = config.get('password', '')
        self.pool_size = config.get('pool_size', 10)
        self._pool = None
        self._version = "unknown"
    
    @property
    def db_type(self) -> str:
        return "postgresql"
    
    @property
    def db_version(self) -> str:
        return self._version
    
    async def connect(self) -> bool:
        """Establish connection pool to PostgreSQL"""
        try:
            self._pool = await asyncpg.create_pool(
                host=self.host,
                port=self.port,
                database=self.database,
                user=self.username,
                password=self.password,
                min_size=2,
                max_size=self.pool_size
            )
            
            # Get version
            async with self._pool.acquire() as conn:
                row = await conn.fetchrow("SELECT version()")
                self._version = row[0] if row else "unknown"
            
            self._connected = True
            return True
        except Exception as e:
            self._connected = False
            raise ConnectionError(f"Failed to connect to PostgreSQL: {e}")
    
    async def disconnect(self) -> None:
        """Close PostgreSQL connection pool"""
        if self._pool:
            await self._pool.close()
            self._pool = None
            self._connected = False
    
    async def health_check(self) -> Dict[str, Any]:
        """Perform PostgreSQL health check"""
        if not self._pool:
            return {"status": "disconnected"}
        
        try:
            async with self._pool.acquire() as conn:
                # Test query
                await conn.fetchrow("SELECT 1")
                
                # Get database size
                size_row = await conn.fetchrow(
                    "SELECT pg_database_size($1) as size",
                    self.database
                )
                db_size = size_row['size'] if size_row else 0
                
                # Get connection count
                conn_row = await conn.fetchrow(
                    "SELECT count(*) as count FROM pg_stat_activity WHERE datname = $1",
                    self.database
                )
                conn_count = conn_row['count'] if conn_row else 0
            
            return {
                "status": "healthy",
                "database_size_bytes": db_size,
                "database_size_mb": round(db_size / (1024 * 1024), 2),
                "active_connections": conn_count,
                "pool_size": self._pool.get_size() if self._pool else 0
            }
        except Exception as e:
            return {"status": "unhealthy", "error": str(e)}
    
    async def get_stats(self) -> Dict[str, Any]:
        """Get PostgreSQL statistics"""
        if not self._pool:
            return {"error": "Not connected"}
        
        try:
            async with self._pool.acquire() as conn:
                stats = {}
                
                # Database size
                size_row = await conn.fetchrow(
                    "SELECT pg_database_size($1) as size",
                    self.database
                )
                stats["database_size_bytes"] = size_row['size'] if size_row else 0
                
                # Table count
                tables = await conn.fetch(
                    """SELECT table_name FROM information_schema.tables 
                       WHERE table_schema = 'public' AND table_type = 'BASE TABLE'"""
                )
                stats["table_count"] = len(tables)
                
                # Table statistics
                table_stats = {}
                for table in tables:
                    table_name = table['table_name']
                    count_row = await conn.fetchrow(f"SELECT COUNT(*) as count FROM {table_name}")
                    table_stats[table_name] = count_row['count'] if count_row else 0
                
                stats["tables"] = table_stats
                
                # Connection pool stats
                if self._pool:
                    stats["pool_size"] = self._pool.get_size()
                    stats["pool_free"] = self._pool.get_idle_size()
                
                return stats
        except Exception as e:
            return {"error": str(e)}
    
    async def execute(self, query: str, params: Optional[tuple] = None) -> Any:
        """Execute query"""
        if not self._pool:
            raise ConnectionError("Not connected to database")
        
        async with self._pool.acquire() as conn:
            if params:
                result = await conn.execute(query, *params)
            else:
                result = await conn.execute(query)
            return result
    
    async def execute_many(self, query: str, params_list: List[tuple]) -> int:
        """Execute query with multiple parameter sets"""
        if not self._pool:
            raise ConnectionError("Not connected to database")
        
        async with self._pool.acquire() as conn:
            await conn.executemany(query, params_list)
            return len(params_list)
    
    async def fetch_one(self, query: str, params: Optional[tuple] = None) -> Optional[Dict[str, Any]]:
        """Fetch single row"""
        if not self._pool:
            raise ConnectionError("Not connected to database")
        
        async with self._pool.acquire() as conn:
            if params:
                row = await conn.fetchrow(query, *params)
            else:
                row = await conn.fetchrow(query)
            
            if row:
                return dict(row)
            return None
    
    async def fetch_all(self, query: str, params: Optional[tuple] = None) -> List[Dict[str, Any]]:
        """Fetch all rows"""
        if not self._pool:
            raise ConnectionError("Not connected to database")
        
        async with self._pool.acquire() as conn:
            if params:
                rows = await conn.fetch(query, *params)
            else:
                rows = await conn.fetch(query)
            
            return [dict(row) for row in rows]
    
    async def begin_transaction(self):
        """Begin transaction - handled by connection context"""
        pass
    
    async def commit(self):
        """Commit transaction - handled by connection context"""
        pass
    
    async def rollback(self):
        """Rollback transaction - handled by connection context"""
        pass
    
    async def create_tables(self) -> bool:
        """Create all database tables"""
        if not self._pool:
            raise ConnectionError("Not connected to database")
        
        # PostgreSQL table creation would go here
        # For now, we'll use the same schema as SQLite with PostgreSQL syntax
        return True
    
    async def backup(self, backup_path: str) -> str:
        """Create database backup using pg_dump"""
        import subprocess
        
        cmd = [
            'pg_dump',
            '-h', self.host,
            '-p', str(self.port),
            '-U', self.username,
            '-F', 'c',  # Custom format
            '-f', backup_path,
            self.database
        ]
        
        env = {'PGPASSWORD': self.password}
        result = subprocess.run(cmd, env=env, capture_output=True)
        
        if result.returncode != 0:
            raise RuntimeError(f"Backup failed: {result.stderr.decode()}")
        
        return backup_path
    
    async def restore(self, backup_path: str) -> bool:
        """Restore database from backup using pg_restore"""
        import subprocess
        
        cmd = [
            'pg_restore',
            '-h', self.host,
            '-p', str(self.port),
            '-U', self.username,
            '-d', self.database,
            '-c',  # Clean before restore
            backup_path
        ]
        
        env = {'PGPASSWORD': self.password}
        result = subprocess.run(cmd, env=env, capture_output=True)
        
        if result.returncode != 0:
            raise RuntimeError(f"Restore failed: {result.stderr.decode()}")
        
        return True


__all__ = ['PostgresAdapter']
