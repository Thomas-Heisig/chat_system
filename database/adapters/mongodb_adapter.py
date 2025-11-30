# database/adapters/mongodb_adapter.py
"""
MongoDB Database Adapter
NoSQL database support for flexible document storage
"""

from typing import Dict, Any, List, Optional, Union, TYPE_CHECKING
from datetime import datetime
import logging

from .base_adapter import BaseDatabaseAdapter

# Type imports for better IDE support
if TYPE_CHECKING:
    from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase

# Optional import - MongoDB support requires motor
try:
    import motor.motor_asyncio
    from pymongo import MongoClient
    MOTOR_AVAILABLE = True
except ImportError:
    MOTOR_AVAILABLE = False
    motor = None
    MongoClient = None

logger = logging.getLogger(__name__)


class MongoDBAdapter(BaseDatabaseAdapter):
    """MongoDB database adapter with async support"""
    
    def __init__(self, config: Dict[str, Any]):
        if not MOTOR_AVAILABLE:
            raise ImportError(
                "motor is required for MongoDB support. "
                "Install with: pip install motor pymongo"
            )
        
        super().__init__(config)
        self.host = config.get('host', 'localhost')
        self.port = config.get('port', 27017)
        self.database = config.get('database', 'chat_system')
        self.username = config.get('username')
        self.password = config.get('password')
        self._client: Optional['AsyncIOMotorClient'] = None
        self._db: Optional['AsyncIOMotorDatabase'] = None
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
            return f"mongodb://{self.username}:{self.password}@{self.host}:{self.port}/{self.database}?authSource=admin"
        return f"mongodb://{self.host}:{self.port}/{self.database}"
    
    async def connect(self) -> bool:
        """Establish connection to MongoDB"""
        try:
            if not MOTOR_AVAILABLE:
                raise ImportError("MongoDB dependencies not available")
            
            self._client = motor.motor_asyncio.AsyncIOMotorClient(
                self._get_connection_string()
            ) if MOTOR_AVAILABLE else None
            if self._client is None:
                raise ConnectionError("Failed to initialize MongoDB client")
            self._db = self._client[self.database]
            
            # Test connection and get version
            server_info = await self._client.server_info()
            self._version = server_info.get('version', 'unknown')
            
            self._connected = True
            logger.info(f"Connected to MongoDB {self._version} at {self.host}:{self.port}")
            return True
        except Exception as e:
            self._connected = False
            logger.error(f"Failed to connect to MongoDB: {e}")
            raise ConnectionError(f"Failed to connect to MongoDB: {e}")
    
    async def disconnect(self) -> None:
        """Close MongoDB connection"""
        if self._client:
            self._client.close()
            self._client = None
            self._db = None
            self._connected = False
            logger.info("Disconnected from MongoDB")
    
    async def health_check(self) -> Dict[str, Any]:
        """Perform MongoDB health check"""
        if not self._client or not self._db:
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
        """Execute query - MongoDB uses collection-specific methods instead."""
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
    
    async def update_many(self, collection: str, filter: Dict[str, Any], 
                          update: Dict[str, Any]) -> int:
        """Update multiple documents"""
        if not self._db:
            raise ConnectionError("Not connected to database")
        
        result = await self._db[collection].update_many(filter, {'$set': update})
        return result.modified_count
    
    async def delete_one(self, collection: str, filter: Dict[str, Any]) -> int:
        """Delete single document"""
        if not self._db:
            raise ConnectionError("Not connected to database")
        
        result = await self._db[collection].delete_one(filter)
        return result.deleted_count
    
    async def delete_many(self, collection: str, filter: Dict[str, Any]) -> int:
        """Delete multiple documents"""
        if not self._db:
            raise ConnectionError("Not connected to database")
        
        result = await self._db[collection].delete_many(filter)
        return result.deleted_count
    
    async def count_documents(self, collection: str, filter: Optional[Dict[str, Any]] = None) -> int:
        """Count documents in collection"""
        if not self._db:
            raise ConnectionError("Not connected to database")
        
        if filter is None:
            filter = {}
        return await self._db[collection].count_documents(filter)
    
    async def begin_transaction(self):
        """MongoDB transactions require replica set"""
        # For MongoDB 4.0+ with replica set
        if self._client:
            async with await self._client.start_session() as session:
                async with session.start_transaction():
                    return session
        return None
    
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
        
        try:
            # Create collections if they don't exist
            collections = ['messages', 'users', 'projects', 'tickets', 'files', 'chat_rooms']
            existing_collections = await self._db.list_collection_names()
            
            for coll in collections:
                if coll not in existing_collections:
                    await self._db.create_collection(coll)
                    logger.info(f"Created collection: {coll}")
            
            # Create indexes
            index_operations = [
                ('messages', 'timestamp'),
                ('messages', 'username'), 
                ('messages', [('room_id', 1), ('timestamp', -1)]),
                ('users', 'username', {'unique': True}),
                ('users', 'email', {'unique': True}),
                ('projects', 'created_by'),
                ('projects', 'status'),
                ('tickets', 'project_id'),
                ('tickets', 'status'),
                ('tickets', 'assigned_to'),
                ('files', 'uploaded_by'),
                ('files', 'project_id')
            ]
            
            for index_spec in index_operations:
                if len(index_spec) == 2:
                    collection, field = index_spec
                    await self._db[collection].create_index(field)
                elif len(index_spec) == 3:
                    collection, field, options = index_spec
                    await self._db[collection].create_index(field, **options)
            
            logger.info("MongoDB collections and indexes created successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to create MongoDB collections: {e}")
            return False
    
    async def backup(self, backup_path: str) -> str:
        """Create database backup using mongodump"""
        import subprocess
        import os
        
        try:
            # Ensure backup directory exists
            os.makedirs(backup_path, exist_ok=True)
            
            cmd = [
                'mongodump',
                '--host', f"{self.host}:{self.port}",
                '--db', self.database,
                '--out', backup_path
            ]
            
            if self.username and self.password:
                cmd.extend(['--username', self.username, '--password', self.password])
            
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode != 0:
                raise RuntimeError(f"Backup failed: {result.stderr}")
            
            logger.info(f"Database backup created at: {backup_path}")
            return backup_path
            
        except Exception as e:
            logger.error(f"Backup failed: {e}")
            raise
    
    async def restore(self, backup_path: str) -> bool:
        """Restore database from backup using mongorestore"""
        import subprocess
        
        try:
            cmd = [
                'mongorestore',
                '--host', f"{self.host}:{self.port}",
                '--db', self.database,
                '--drop',  # Drop existing collections
                f"{backup_path}/{self.database}"
            ]
            
            if self.username and self.password:
                cmd.extend(['--username', self.username, '--password', self.password])
            
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode != 0:
                raise RuntimeError(f"Restore failed: {result.stderr}")
            
            logger.info(f"Database restored from: {backup_path}")
            return True
            
        except Exception as e:
            logger.error(f"Restore failed: {e}")
            raise


__all__ = ['MongoDBAdapter']