# database/adapters/mongodb_adapter.py
"""
MongoDB Database Adapter
NoSQL database support for flexible document storage
"""

from typing import Dict, Any, List, Optional
from datetime import datetime

from .base_adapter import BaseDatabaseAdapter

# Optional import - MongoDB support requires motor
try:
    import motor.motor_asyncio
    from pymongo import MongoClient
    MOTOR_AVAILABLE = True
except ImportError:
    MOTOR_AVAILABLE = False
    motor = None


class MongoDBAdapter(BaseDatabaseAdapter):
    """MongoDB database adapter with async support"""
    
    def __init__(self, config: Dict[str, Any]):
        if not MOTOR_AVAILABLE:
            raise ImportError("motor is required for MongoDB support. Install with: pip install motor")
        
        super().__init__(config)
        self.host = config.get('host', 'localhost')
        self.port = config.get('port', 27017)
        self.database = config.get('database', 'chat_system')
        self.username = config.get('username')
        self.password = config.get('password')
        self._client = None
        self._db = None
        self._version = "unknown"
    
    @property
    def db_type(self) -> str:
        return "mongodb"
    
    @property
    def db_version(self) -> str:
        return self._version
    
    def _get_connection_string(self) -> str:
        """Build MongoDB connection string"""
        if self.username and self.password:
            return f"mongodb://{self.username}:{self.password}@{self.host}:{self.port}"
        return f"mongodb://{self.host}:{self.port}"
    
    async def connect(self) -> bool:
        """Establish connection to MongoDB"""
        try:
            self._client = motor.motor_asyncio.AsyncIOMotorClient(
                self._get_connection_string()
            )
            self._db = self._client[self.database]
            
            # Test connection and get version
            server_info = await self._client.server_info()
            self._version = server_info.get('version', 'unknown')
            
            self._connected = True
            return True
        except Exception as e:
            self._connected = False
            raise ConnectionError(f"Failed to connect to MongoDB: {e}")
    
    async def disconnect(self) -> None:
        """Close MongoDB connection"""
        if self._client:
            self._client.close()
            self._client = None
            self._db = None
            self._connected = False
    
    async def health_check(self) -> Dict[str, Any]:
        """Perform MongoDB health check"""
        if not self._client:
            return {"status": "disconnected"}
        
        try:
            # Ping the server
            await self._client.admin.command('ping')
            
            # Get database stats
            stats = await self._db.command('dbStats')
            
            return {
                "status": "healthy",
                "database_size_bytes": stats.get('dataSize', 0),
                "storage_size_bytes": stats.get('storageSize', 0),
                "collections": stats.get('collections', 0),
                "indexes": stats.get('indexes', 0),
                "objects": stats.get('objects', 0)
            }
        except Exception as e:
            return {"status": "unhealthy", "error": str(e)}
    
    async def get_stats(self) -> Dict[str, Any]:
        """Get MongoDB statistics"""
        if not self._db:
            return {"error": "Not connected"}
        
        try:
            stats = await self._db.command('dbStats')
            
            # Get collection stats
            collections = await self._db.list_collection_names()
            collection_stats = {}
            
            for coll_name in collections:
                coll = self._db[coll_name]
                count = await coll.count_documents({})
                collection_stats[coll_name] = count
            
            return {
                "database_size_bytes": stats.get('dataSize', 0),
                "storage_size_bytes": stats.get('storageSize', 0),
                "collection_count": len(collections),
                "index_count": stats.get('indexes', 0),
                "collections": collection_stats
            }
        except Exception as e:
            return {"error": str(e)}
    
    async def execute(self, query: str, params: Optional[tuple] = None) -> Any:
        """Execute query - MongoDB uses collection-specific methods instead.
        This method is provided for compatibility but redirects to appropriate methods.
        """
        # For compatibility, we can interpret simple queries
        # In practice, use collection-specific methods like insert_one, find, etc.
        raise NotImplementedError(
            "MongoDB uses collection-specific methods. "
            "Use insert_one(), find_one(), find(), update_one(), delete_one() instead."
        )
    
    async def execute_many(self, query: str, params_list: List[tuple]) -> int:
        """Execute many - MongoDB uses insert_many for bulk operations."""
        raise NotImplementedError(
            "MongoDB uses collection-specific methods. "
            "Use insert_many() for bulk inserts instead."
        )
    
    async def fetch_one(self, query: str, params: Optional[tuple] = None) -> Optional[Dict[str, Any]]:
        """Fetch one - MongoDB uses find_one with filter dictionaries."""
        raise NotImplementedError(
            "MongoDB uses collection-specific methods. "
            "Use find_one(collection, filter) instead."
        )
    
    async def fetch_all(self, query: str, params: Optional[tuple] = None) -> List[Dict[str, Any]]:
        """Fetch all - MongoDB uses find with filter dictionaries."""
        raise NotImplementedError(
            "MongoDB uses collection-specific methods. "
            "Use find(collection, filter) instead."
        )
    
    # MongoDB-specific methods
    async def insert_one(self, collection: str, document: Dict[str, Any]) -> str:
        """Insert single document"""
        if not self._db:
            raise ConnectionError("Not connected to database")
        
        result = await self._db[collection].insert_one(document)
        return str(result.inserted_id)
    
    async def insert_many(self, collection: str, documents: List[Dict[str, Any]]) -> List[str]:
        """Insert multiple documents"""
        if not self._db:
            raise ConnectionError("Not connected to database")
        
        result = await self._db[collection].insert_many(documents)
        return [str(id) for id in result.inserted_ids]
    
    async def find_one(self, collection: str, filter: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Find single document"""
        if not self._db:
            raise ConnectionError("Not connected to database")
        
        return await self._db[collection].find_one(filter)
    
    async def find(self, collection: str, filter: Dict[str, Any], 
                   limit: int = 100, skip: int = 0) -> List[Dict[str, Any]]:
        """Find multiple documents"""
        if not self._db:
            raise ConnectionError("Not connected to database")
        
        cursor = self._db[collection].find(filter).skip(skip).limit(limit)
        return await cursor.to_list(length=limit)
    
    async def update_one(self, collection: str, filter: Dict[str, Any], 
                         update: Dict[str, Any]) -> int:
        """Update single document"""
        if not self._db:
            raise ConnectionError("Not connected to database")
        
        result = await self._db[collection].update_one(filter, {'$set': update})
        return result.modified_count
    
    async def delete_one(self, collection: str, filter: Dict[str, Any]) -> int:
        """Delete single document"""
        if not self._db:
            raise ConnectionError("Not connected to database")
        
        result = await self._db[collection].delete_one(filter)
        return result.deleted_count
    
    async def begin_transaction(self):
        """MongoDB transactions require replica set"""
        pass
    
    async def commit(self):
        """MongoDB auto-commits single operations"""
        pass
    
    async def rollback(self):
        """MongoDB transactions require replica set"""
        pass
    
    async def create_tables(self) -> bool:
        """Create collections and indexes"""
        if not self._db:
            raise ConnectionError("Not connected to database")
        
        # Create collections
        collections = ['messages', 'users', 'projects', 'tickets', 'files', 'chat_rooms']
        for coll in collections:
            try:
                await self._db.create_collection(coll)
            except Exception:
                pass  # Collection might already exist
        
        # Create indexes
        await self._db.messages.create_index('timestamp')
        await self._db.messages.create_index('username')
        await self._db.users.create_index('username', unique=True)
        await self._db.users.create_index('email', unique=True)
        await self._db.projects.create_index('created_by')
        await self._db.tickets.create_index('project_id')
        
        return True
    
    async def backup(self, backup_path: str) -> str:
        """Create database backup using mongodump"""
        import subprocess
        
        cmd = [
            'mongodump',
            '--host', f"{self.host}:{self.port}",
            '--db', self.database,
            '--out', backup_path
        ]
        
        if self.username and self.password:
            cmd.extend(['--username', self.username, '--password', self.password])
        
        result = subprocess.run(cmd, capture_output=True)
        
        if result.returncode != 0:
            raise RuntimeError(f"Backup failed: {result.stderr.decode()}")
        
        return backup_path
    
    async def restore(self, backup_path: str) -> bool:
        """Restore database from backup using mongorestore"""
        import subprocess
        
        cmd = [
            'mongorestore',
            '--host', f"{self.host}:{self.port}",
            '--db', self.database,
            '--drop',  # Drop existing collections
            f"{backup_path}/{self.database}"
        ]
        
        if self.username and self.password:
            cmd.extend(['--username', self.username, '--password', self.password])
        
        result = subprocess.run(cmd, capture_output=True)
        
        if result.returncode != 0:
            raise RuntimeError(f"Restore failed: {result.stderr.decode()}")
        
        return True


__all__ = ['MongoDBAdapter']
