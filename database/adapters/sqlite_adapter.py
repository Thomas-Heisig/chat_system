# database/adapters/sqlite_adapter.py
"""
SQLite Database Adapter
Default database adapter for the chat system
"""

import sqlite3
import aiosqlite
import os
import shutil
from typing import Dict, Any, List, Optional
from datetime import datetime
from pathlib import Path

from .base_adapter import BaseDatabaseAdapter


class SQLiteAdapter(BaseDatabaseAdapter):
    """SQLite database adapter with async support"""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.db_path = config.get('sqlite_path', 'chat_system.db')
        self._db: Optional[aiosqlite.Connection] = None
        self._version = sqlite3.sqlite_version
    
    @property
    def db_type(self) -> str:
        return "sqlite"
    
    @property
    def db_version(self) -> str:
        return self._version
    
    async def connect(self) -> bool:
        """Establish connection to SQLite database"""
        try:
            self._db = await aiosqlite.connect(self.db_path)
            self._db.row_factory = aiosqlite.Row
            
            # Enable WAL mode for better concurrency
            await self._db.execute("PRAGMA journal_mode = WAL")
            await self._db.execute("PRAGMA foreign_keys = ON")
            await self._db.execute("PRAGMA synchronous = NORMAL")
            await self._db.execute("PRAGMA cache_size = -64000")  # 64MB cache
            await self._db.execute("PRAGMA temp_store = MEMORY")
            
            self._connected = True
            return True
        except Exception as e:
            self._connected = False
            raise ConnectionError(f"Failed to connect to SQLite: {e}")
    
    async def disconnect(self) -> None:
        """Close SQLite connection"""
        if self._db:
            await self._db.close()
            self._db = None
            self._connected = False
    
    async def health_check(self) -> Dict[str, Any]:
        """Perform SQLite health check"""
        if not self._db:
            return {"status": "disconnected"}
        
        try:
            # Test query
            async with self._db.execute("SELECT 1") as cursor:
                await cursor.fetchone()
            
            # Integrity check
            async with self._db.execute("PRAGMA integrity_check") as cursor:
                integrity = (await cursor.fetchone())[0]
            
            # Get database size
            db_size = os.path.getsize(self.db_path) if os.path.exists(self.db_path) else 0
            
            return {
                "status": "healthy",
                "integrity": integrity,
                "database_size_bytes": db_size,
                "database_size_mb": round(db_size / (1024 * 1024), 2),
                "path": self.db_path
            }
        except Exception as e:
            return {"status": "unhealthy", "error": str(e)}
    
    async def get_stats(self) -> Dict[str, Any]:
        """Get SQLite statistics"""
        if not self._db:
            return {"error": "Not connected"}
        
        try:
            stats = {}
            
            # Page statistics
            async with self._db.execute("PRAGMA page_count") as cursor:
                stats["page_count"] = (await cursor.fetchone())[0]
            
            async with self._db.execute("PRAGMA page_size") as cursor:
                stats["page_size"] = (await cursor.fetchone())[0]
            
            async with self._db.execute("PRAGMA freelist_count") as cursor:
                stats["freelist_count"] = (await cursor.fetchone())[0]
            
            stats["database_size_bytes"] = stats["page_count"] * stats["page_size"]
            
            # Table counts
            async with self._db.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'"
            ) as cursor:
                tables = await cursor.fetchall()
                stats["table_count"] = len(tables)
                
                table_stats = {}
                for table in tables:
                    table_name = table[0]
                    async with self._db.execute(f"SELECT COUNT(*) FROM {table_name}") as count_cursor:
                        table_stats[table_name] = (await count_cursor.fetchone())[0]
                
                stats["tables"] = table_stats
            
            return stats
        except Exception as e:
            return {"error": str(e)}
    
    async def execute(self, query: str, params: Optional[tuple] = None) -> Any:
        """Execute query"""
        if not self._db:
            raise ConnectionError("Not connected to database")
        
        async with self._db.execute(query, params or ()) as cursor:
            await self._db.commit()
            return cursor.lastrowid
    
    async def execute_many(self, query: str, params_list: List[tuple]) -> int:
        """Execute query with multiple parameter sets"""
        if not self._db:
            raise ConnectionError("Not connected to database")
        
        await self._db.executemany(query, params_list)
        await self._db.commit()
        return len(params_list)
    
    async def fetch_one(self, query: str, params: Optional[tuple] = None) -> Optional[Dict[str, Any]]:
        """Fetch single row"""
        if not self._db:
            raise ConnectionError("Not connected to database")
        
        async with self._db.execute(query, params or ()) as cursor:
            row = await cursor.fetchone()
            if row:
                return dict(row)
            return None
    
    async def fetch_all(self, query: str, params: Optional[tuple] = None) -> List[Dict[str, Any]]:
        """Fetch all rows"""
        if not self._db:
            raise ConnectionError("Not connected to database")
        
        async with self._db.execute(query, params or ()) as cursor:
            rows = await cursor.fetchall()
            return [dict(row) for row in rows]
    
    async def begin_transaction(self):
        """Begin transaction"""
        if self._db:
            await self._db.execute("BEGIN TRANSACTION")
    
    async def commit(self):
        """Commit transaction"""
        if self._db:
            await self._db.commit()
    
    async def rollback(self):
        """Rollback transaction"""
        if self._db:
            await self._db.rollback()
    
    async def create_tables(self) -> bool:
        """Create all database tables"""
        if not self._db:
            raise ConnectionError("Not connected to database")
        
        try:
            # Import table definitions from connection module
            from database.connection import init_database
            init_database()
            return True
        except Exception as e:
            raise RuntimeError(f"Failed to create tables: {e}")
    
    async def backup(self, backup_path: str) -> str:
        """Create database backup"""
        if not os.path.exists(self.db_path):
            raise FileNotFoundError(f"Database file not found: {self.db_path}")
        
        # Ensure backup directory exists
        Path(backup_path).parent.mkdir(parents=True, exist_ok=True)
        
        # Create backup
        if self._db:
            # Use SQLite backup API
            backup_conn = await aiosqlite.connect(backup_path)
            await self._db.backup(backup_conn)
            await backup_conn.close()
        else:
            # Simple file copy if not connected
            shutil.copy2(self.db_path, backup_path)
        
        return backup_path
    
    async def restore(self, backup_path: str) -> bool:
        """Restore database from backup"""
        if not os.path.exists(backup_path):
            raise FileNotFoundError(f"Backup file not found: {backup_path}")
        
        # Close connection if open
        if self._db:
            await self.disconnect()
        
        # Replace current database with backup
        shutil.copy2(backup_path, self.db_path)
        
        # Reconnect
        await self.connect()
        return True
    
    async def optimize(self) -> Dict[str, Any]:
        """Optimize SQLite database"""
        if not self._db:
            raise ConnectionError("Not connected to database")
        
        start_size = os.path.getsize(self.db_path)
        
        await self._db.execute("PRAGMA optimize")
        await self._db.execute("VACUUM")
        await self._db.execute("ANALYZE")
        
        end_size = os.path.getsize(self.db_path)
        
        return {
            "status": "optimized",
            "size_before": start_size,
            "size_after": end_size,
            "size_saved": start_size - end_size
        }


__all__ = ['SQLiteAdapter']
