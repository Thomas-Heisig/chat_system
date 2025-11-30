# config/database_config.py
"""
Modular Database Configuration
Supports multiple database backends: SQLite, PostgreSQL, MySQL, MongoDB
"""

from typing import Dict, Any, Optional, List
from enum import Enum
from pydantic import BaseModel, Field
import os


class DatabaseType(str, Enum):
    """Supported database types"""
    SQLITE = "sqlite"
    POSTGRESQL = "postgresql"
    MYSQL = "mysql"
    MONGODB = "mongodb"


class DatabaseConfig(BaseModel):
    """Base database configuration"""
    db_type: DatabaseType = Field(default=DatabaseType.SQLITE)
    host: str = Field(default="localhost")
    port: int = Field(default=5432)
    database: str = Field(default="chat_system")
    username: Optional[str] = Field(default=None)
    password: Optional[str] = Field(default=None)
    
    # Connection pool settings
    pool_size: int = Field(default=10, ge=1, le=100)
    max_overflow: int = Field(default=20, ge=0, le=50)
    pool_timeout: int = Field(default=30, ge=5, le=120)
    pool_recycle: int = Field(default=3600, ge=60)
    
    # SQLite specific
    sqlite_path: str = Field(default="chat_system.db")
    
    # SSL/TLS settings
    ssl_enabled: bool = Field(default=False)
    ssl_ca_cert: Optional[str] = Field(default=None)
    ssl_client_cert: Optional[str] = Field(default=None)
    ssl_client_key: Optional[str] = Field(default=None)
    
    # Additional options
    echo: bool = Field(default=False)  # SQL query logging
    connect_timeout: int = Field(default=10)
    
    class Config:
        use_enum_values = True

    def get_connection_url(self) -> str:
        """Generate database connection URL"""
        if self.db_type == DatabaseType.SQLITE:
            return f"sqlite:///{self.sqlite_path}"
        elif self.db_type == DatabaseType.POSTGRESQL:
            auth = f"{self.username}:{self.password}@" if self.username else ""
            return f"postgresql://{auth}{self.host}:{self.port}/{self.database}"
        elif self.db_type == DatabaseType.MYSQL:
            auth = f"{self.username}:{self.password}@" if self.username else ""
            return f"mysql+pymysql://{auth}{self.host}:{self.port}/{self.database}"
        elif self.db_type == DatabaseType.MONGODB:
            auth = f"{self.username}:{self.password}@" if self.username else ""
            return f"mongodb://{auth}{self.host}:{self.port}/{self.database}"
        else:
            raise ValueError(f"Unsupported database type: {self.db_type}")

    def get_async_connection_url(self) -> str:
        """Generate async database connection URL"""
        if self.db_type == DatabaseType.SQLITE:
            return f"sqlite+aiosqlite:///{self.sqlite_path}"
        elif self.db_type == DatabaseType.POSTGRESQL:
            auth = f"{self.username}:{self.password}@" if self.username else ""
            return f"postgresql+asyncpg://{auth}{self.host}:{self.port}/{self.database}"
        elif self.db_type == DatabaseType.MYSQL:
            auth = f"{self.username}:{self.password}@" if self.username else ""
            return f"mysql+aiomysql://{auth}{self.host}:{self.port}/{self.database}"
        else:
            return self.get_connection_url()


class VectorDatabaseConfig(BaseModel):
    """Vector database configuration for RAG"""
    provider: str = Field(default="chromadb")  # chromadb, qdrant, pinecone, weaviate, milvus
    host: str = Field(default="localhost")
    port: int = Field(default=8000)
    api_key: Optional[str] = Field(default=None)
    collection_name: str = Field(default="chat_embeddings")
    
    # ChromaDB specific
    chroma_persist_directory: str = Field(default="./chroma_data")
    
    # Qdrant specific
    qdrant_grpc_port: int = Field(default=6334)
    
    # Pinecone specific
    pinecone_environment: Optional[str] = Field(default=None)
    pinecone_index_name: Optional[str] = Field(default=None)
    
    # Embedding settings
    embedding_model: str = Field(default="all-MiniLM-L6-v2")
    embedding_dimension: int = Field(default=384)


def load_database_config_from_env() -> DatabaseConfig:
    """Load database configuration from environment variables"""
    db_type_str = os.getenv("DATABASE_TYPE", "sqlite").lower()
    
    try:
        db_type = DatabaseType(db_type_str)
    except ValueError:
        db_type = DatabaseType.SQLITE
    
    return DatabaseConfig(
        db_type=db_type,
        host=os.getenv("DATABASE_HOST", "localhost"),
        port=int(os.getenv("DATABASE_PORT", "5432")),
        database=os.getenv("DATABASE_NAME", "chat_system"),
        username=os.getenv("DATABASE_USER"),
        password=os.getenv("DATABASE_PASSWORD"),
        pool_size=int(os.getenv("DATABASE_POOL_SIZE", "10")),
        max_overflow=int(os.getenv("DATABASE_MAX_OVERFLOW", "20")),
        pool_timeout=int(os.getenv("DATABASE_POOL_TIMEOUT", "30")),
        sqlite_path=os.getenv("DATABASE_SQLITE_PATH", "chat_system.db"),
        ssl_enabled=os.getenv("DATABASE_SSL_ENABLED", "false").lower() == "true",
        echo=os.getenv("DATABASE_ECHO", "false").lower() == "true"
    )


def load_vector_db_config_from_env() -> VectorDatabaseConfig:
    """Load vector database configuration from environment variables"""
    return VectorDatabaseConfig(
        provider=os.getenv("VECTOR_DB_PROVIDER", "chromadb"),
        host=os.getenv("VECTOR_DB_HOST", "localhost"),
        port=int(os.getenv("VECTOR_DB_PORT", "8000")),
        api_key=os.getenv("VECTOR_DB_API_KEY"),
        collection_name=os.getenv("VECTOR_DB_COLLECTION", "chat_embeddings"),
        chroma_persist_directory=os.getenv("CHROMA_PERSIST_DIR", "./chroma_data"),
        embedding_model=os.getenv("EMBEDDING_MODEL", "all-MiniLM-L6-v2"),
        embedding_dimension=int(os.getenv("EMBEDDING_DIMENSION", "384"))
    )


# Default configurations
database_config = load_database_config_from_env()
vector_db_config = load_vector_db_config_from_env()


__all__ = [
    'DatabaseType',
    'DatabaseConfig', 
    'VectorDatabaseConfig',
    'load_database_config_from_env',
    'load_vector_db_config_from_env',
    'database_config',
    'vector_db_config'
]
