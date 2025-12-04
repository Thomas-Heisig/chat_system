from pydantic import Field, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import List, Optional, Dict, Any, Union
import os
import secrets
from pathlib import Path
import urllib.parse
from ipaddress import ip_address

class EnvironmentSettings(BaseSettings):
    """Enhanced environment settings with comprehensive validation"""
    
    # Application
    APP_NAME: str = "Advanced Chat System"
    APP_VERSION: str = "2.0.0"
    APP_ENVIRONMENT: str = "development"
    APP_DEBUG: bool = True
    APP_SECRET_KEY: str = Field(default_factory=lambda: secrets.token_urlsafe(64))
    APP_URL: str = "http://localhost:8000"
    APP_TIMEZONE: str = "Europe/Berlin"
    
    # Server
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    RELOAD: bool = True
    WORKERS: int = 1
    SERVER_NAME: Optional[str] = None
    
    # Database
    DATABASE_URL: str = "sqlite:///chat.db"
    DATABASE_TIMEOUT: int = 30
    DATABASE_POOL_SIZE: int = 5
    DATABASE_MAX_OVERFLOW: int = 10
    DATABASE_ECHO: bool = False
    
    # CORS
    CORS_ORIGINS: List[str] = ["http://localhost:3000", "http://127.0.0.1:3000"]
    CORS_ALLOW_CREDENTIALS: bool = True
    CORS_ALLOW_METHODS: List[str] = ["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH"]
    CORS_ALLOW_HEADERS: List[str] = ["Authorization", "Content-Type", "X-Requested-With"]
    CORS_EXPOSE_HEADERS: List[str] = ["X-Total-Count", "X-Error-Message"]
    
    # AI Configuration
    AI_ENABLED: bool = True
    OLLAMA_BASE_URL: str = "http://localhost:11434"
    OLLAMA_DEFAULT_MODEL: str = "llama2"
    OLLAMA_TIMEOUT: int = 30
    OLLAMA_MAX_RETRIES: int = 3
    
    # Custom Model Configuration
    CUSTOM_MODEL_ENABLED: bool = False
    CUSTOM_MODEL_PATH: str = "./models/custom_model"
    CUSTOM_MODEL_TYPE: str = "transformers"  # transformers, onnx, tensorflow
    
    # AI Behavior
    AI_AUTO_RESPOND: bool = True
    AI_CONTEXT_MESSAGES: int = Field(default=10, ge=1, le=100)
    AI_MAX_RESPONSE_LENGTH: int = Field(default=1000, ge=50, le=5000)
    AI_TEMPERATURE: float = Field(default=0.7, ge=0.0, le=2.0)
    AI_TOP_P: float = Field(default=0.9, ge=0.0, le=1.0)
    AI_FREQUENCY_PENALTY: float = Field(default=0.0, ge=0.0, le=2.0)
    AI_PRESENCE_PENALTY: float = Field(default=0.0, ge=0.0, le=2.0)
    
    # RAG Configuration
    RAG_ENABLED: bool = False
    EMBEDDING_MODEL: str = "all-MiniLM-L6-v2"
    VECTOR_DB_PATH: str = "./data/vector_db"
    VECTOR_DB_TYPE: str = "chroma"  # chroma, faiss, qdrant
    SIMILARITY_THRESHOLD: float = Field(default=0.7, ge=0.0, le=1.0)
    
    # Security & Rate Limiting
    RATE_LIMIT_ENABLED: bool = True
    RATE_LIMIT_REQUESTS: int = Field(default=100, ge=1, le=10000)
    RATE_LIMIT_WINDOW: int = Field(default=3600, ge=1, le=86400)
    RATE_LIMIT_STRATEGY: str = "fixed-window"  # fixed-window, sliding-window, token-bucket
    
    # JWT Authentication
    JWT_SECRET_KEY: str = Field(default_factory=lambda: secrets.token_urlsafe(64))
    JWT_ALGORITHM: str = "HS256"
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    JWT_REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    
    # Feature Flags
    FEATURE_SENTIMENT_ANALYSIS: bool = True
    FEATURE_AI_SUGGESTIONS: bool = True
    FEATURE_MESSAGE_MODERATION: bool = False
    FEATURE_FILE_UPLOAD: bool = True
    FEATURE_PROJECT_MANAGEMENT: bool = True
    FEATURE_TICKET_SYSTEM: bool = True
    FEATURE_REAL_TIME_CHAT: bool = True
    FEATURE_USER_AUTHENTICATION: bool = False
    
    # File Upload Configuration
    UPLOAD_FOLDER: str = "./uploads"
    MAX_FILE_SIZE: int = Field(default=16 * 1024 * 1024, ge=1024, le=100 * 1024 * 1024)  # 16MB default
    ALLOWED_EXTENSIONS: List[str] = Field(default=[
        'txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif', 'doc', 'docx', 
        'xls', 'xlsx', 'csv', 'json', 'xml'
    ])
    
    # Logging
    LOG_LEVEL: str = "INFO"
    LOG_FILE: str = "chat_system.log"
    LOG_FORMAT: str = "console"  # console, json, detailed
    LOG_MAX_BYTES: int = 10 * 1024 * 1024  # 10MB
    LOG_BACKUP_COUNT: int = 5
    
    # Monitoring & Metrics
    METRICS_ENABLED: bool = True
    HEALTH_CHECK_ENABLED: bool = True
    PERFORMANCE_MONITORING: bool = True
    
    # Cache Configuration
    CACHE_ENABLED: bool = True
    CACHE_BACKEND: str = "memory"  # memory, redis, memcached
    CACHE_TTL: int = 300  # 5 minutes
    REDIS_URL: Optional[str] = None
    
    # Email Configuration
    EMAIL_ENABLED: bool = False
    EMAIL_HOST: Optional[str] = None
    EMAIL_PORT: int = 587
    EMAIL_USERNAME: Optional[str] = None
    EMAIL_PASSWORD: Optional[str] = None
    EMAIL_USE_TLS: bool = True
    
    # WebSocket Configuration
    WEBSOCKET_ENABLED: bool = True
    WEBSOCKET_PING_INTERVAL: int = 20
    WEBSOCKET_PING_TIMEOUT: int = 30
    WEBSOCKET_MAX_SIZE: int = 16 * 1024 * 1024  # 16MB
    
    # Background Tasks
    BACKGROUND_TASKS_ENABLED: bool = True
    TASK_WORKERS: int = 2
    TASK_RETRY_ATTEMPTS: int = 3
    
    # Model Config
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        validate_assignment=True,
        extra="ignore"
    )

    # Field Validators
    @field_validator("APP_ENVIRONMENT")
    @classmethod
    def validate_environment(cls, v):
        allowed = ["development", "production", "staging", "testing"]
        if v not in allowed:
            raise ValueError(f"APP_ENVIRONMENT must be one of {allowed}")
        return v

    @field_validator("PORT")
    @classmethod
    def validate_port(cls, v):
        if not 1024 <= v <= 65535:
            raise ValueError("PORT must be between 1024 and 65535")
        return v

    @field_validator("HOST")
    @classmethod
    def validate_host(cls, v):
        try:
            ip_address(v)
        except ValueError:
            if v not in ["localhost", "0.0.0.0", "127.0.0.1"]:
                raise ValueError("HOST must be a valid IP address or localhost")
        return v

    @field_validator("APP_SECRET_KEY")
    @classmethod
    def validate_secret_key(cls, v):
        if len(v) < 32:
            raise ValueError("APP_SECRET_KEY must be at least 32 characters long")
        return v

    @field_validator("DATABASE_URL")
    @classmethod
    def validate_database_url(cls, v):
        if v.startswith('sqlite:///'):
            db_path = v[10:]
            db_dir = os.path.dirname(db_path)
            if db_dir and not os.path.exists(db_dir):
                os.makedirs(db_dir, exist_ok=True)
        elif v.startswith('postgresql://'):
            # Validate PostgreSQL URL format
            try:
                parsed = urllib.parse.urlparse(v)
                if not all([parsed.scheme, parsed.hostname]):
                    raise ValueError("Invalid PostgreSQL URL format")
            except Exception as e:
                raise ValueError(f"Invalid database URL: {e}")
        return v

    @field_validator("CORS_ORIGINS", mode="before")
    @classmethod
    def validate_cors_origins(cls, v):
        if isinstance(v, str):
            if v.startswith('[') and v.endswith(']'):
                import ast
                try:
                    return ast.literal_eval(v)
                except (ValueError, SyntaxError):
                    # Invalid literal syntax, fall back to comma-separated
                    pass
            return [origin.strip() for origin in v.split(',')]
        return v

    @field_validator("OLLAMA_BASE_URL")
    @classmethod
    def validate_ollama_url(cls, v):
        if not v.startswith(('http://', 'https://')):
            raise ValueError("OLLAMA_BASE_URL must start with http:// or https://")
        return v.rstrip('/')

    @field_validator("LOG_LEVEL")
    @classmethod
    def validate_log_level(cls, v):
        allowed = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        if v.upper() not in allowed:
            raise ValueError(f"LOG_LEVEL must be one of {allowed}")
        return v.upper()

    @field_validator("UPLOAD_FOLDER")
    @classmethod
    def validate_upload_folder(cls, v):
        path = Path(v)
        if not path.exists():
            path.mkdir(parents=True, exist_ok=True)
        return str(path.absolute())

    @field_validator("ALLOWED_EXTENSIONS")
    @classmethod
    def validate_allowed_extensions(cls, v):
        if not v:
            raise ValueError("ALLOWED_EXTENSIONS cannot be empty")
        return [ext.lower().lstrip('.') for ext in v]

    @field_validator("RATE_LIMIT_STRATEGY")
    @classmethod
    def validate_rate_limit_strategy(cls, v):
        allowed = ["fixed-window", "sliding-window", "token-bucket"]
        if v not in allowed:
            raise ValueError(f"RATE_LIMIT_STRATEGY must be one of {allowed}")
        return v

    @field_validator("VECTOR_DB_TYPE")
    @classmethod
    def validate_vector_db_type(cls, v):
        allowed = ["chroma", "faiss", "qdrant", "pinecone"]
        if v not in allowed:
            raise ValueError(f"VECTOR_DB_TYPE must be one of {allowed}")
        return v

    # Model Validators
    @model_validator(mode="after")
    def validate_custom_model_path(self):
        if self.CUSTOM_MODEL_ENABLED and not os.path.exists(self.CUSTOM_MODEL_PATH):
            raise ValueError(f"Custom model path does not exist: {self.CUSTOM_MODEL_PATH}")
        return self

    @model_validator(mode="after")
    def validate_vector_db_path(self):
        if self.RAG_ENABLED:
            os.makedirs(self.VECTOR_DB_PATH, exist_ok=True)
        return self

    @model_validator(mode="after")
    def validate_workers(self):
        if self.RELOAD and self.WORKERS > 1:
            raise ValueError("WORKERS must be 1 when RELOAD is enabled")
        return self

    @model_validator(mode="after")
    def validate_email_config(self):
        if self.EMAIL_ENABLED:
            if not all([self.EMAIL_HOST, self.EMAIL_USERNAME, self.EMAIL_PASSWORD]):
                raise ValueError("Email configuration incomplete when EMAIL_ENABLED is True")
        return self

    @model_validator(mode="after")
    def validate_cache_config(self):
        if self.CACHE_ENABLED and self.CACHE_BACKEND == "redis" and not self.REDIS_URL:
            raise ValueError("REDIS_URL is required when using redis cache backend")
        return self

    # Computed properties
    @property
    def is_development(self) -> bool:
        return self.APP_ENVIRONMENT == "development"
    
    @property
    def is_production(self) -> bool:
        return self.APP_ENVIRONMENT == "production"
    
    @property
    def is_testing(self) -> bool:
        return self.APP_ENVIRONMENT == "testing"
    
    @property
    def is_staging(self) -> bool:
        return self.APP_ENVIRONMENT == "staging"
    
    @property
    def project_features_enabled(self) -> bool:
        return self.FEATURE_PROJECT_MANAGEMENT
    
    @property
    def ticket_system_enabled(self) -> bool:
        return self.FEATURE_TICKET_SYSTEM
    
    @property
    def file_upload_enabled(self) -> bool:
        return self.FEATURE_FILE_UPLOAD

    # Configuration groups
    @property
    def ai_config(self) -> Dict[str, Any]:
        """Get AI configuration as dictionary"""
        return {
            "enabled": self.AI_ENABLED,
            "ollama": {
                "base_url": self.OLLAMA_BASE_URL,
                "default_model": self.OLLAMA_DEFAULT_MODEL,
                "timeout": self.OLLAMA_TIMEOUT,
                "max_retries": self.OLLAMA_MAX_RETRIES
            },
            "custom_model": {
                "enabled": self.CUSTOM_MODEL_ENABLED,
                "path": self.CUSTOM_MODEL_PATH,
                "type": self.CUSTOM_MODEL_TYPE
            },
            "behavior": {
                "auto_respond": self.AI_AUTO_RESPOND,
                "context_messages": self.AI_CONTEXT_MESSAGES,
                "max_response_length": self.AI_MAX_RESPONSE_LENGTH,
                "temperature": self.AI_TEMPERATURE,
                "top_p": self.AI_TOP_P,
                "frequency_penalty": self.AI_FREQUENCY_PENALTY,
                "presence_penalty": self.AI_PRESENCE_PENALTY
            },
            "rag": {
                "enabled": self.RAG_ENABLED,
                "embedding_model": self.EMBEDDING_MODEL,
                "vector_db_path": self.VECTOR_DB_PATH,
                "vector_db_type": self.VECTOR_DB_TYPE,
                "similarity_threshold": self.SIMILARITY_THRESHOLD
            },
            "features": {
                "sentiment_analysis": self.FEATURE_SENTIMENT_ANALYSIS,
                "ai_suggestions": self.FEATURE_AI_SUGGESTIONS,
                "moderation": self.FEATURE_MESSAGE_MODERATION
            }
        }
    
    @property
    def security_config(self) -> Dict[str, Any]:
        """Get security configuration"""
        return {
            "rate_limiting": {
                "enabled": self.RATE_LIMIT_ENABLED,
                "requests": self.RATE_LIMIT_REQUESTS,
                "window": self.RATE_LIMIT_WINDOW,
                "strategy": self.RATE_LIMIT_STRATEGY
            },
            "jwt": {
                "secret_key": "***" if self.JWT_SECRET_KEY else None,
                "algorithm": self.JWT_ALGORITHM,
                "access_token_expire_minutes": self.JWT_ACCESS_TOKEN_EXPIRE_MINUTES,
                "refresh_token_expire_days": self.JWT_REFRESH_TOKEN_EXPIRE_DAYS
            },
            "cors": {
                "origins": self.CORS_ORIGINS,
                "allow_credentials": self.CORS_ALLOW_CREDENTIALS,
                "allow_methods": self.CORS_ALLOW_METHODS,
                "allow_headers": self.CORS_ALLOW_HEADERS,
                "expose_headers": self.CORS_EXPOSE_HEADERS
            }
        }
    
    @property
    def file_config(self) -> Dict[str, Any]:
        """Get file upload configuration"""
        return {
            "enabled": self.FEATURE_FILE_UPLOAD,
            "upload_folder": self.UPLOAD_FOLDER,
            "max_file_size": self.MAX_FILE_SIZE,
            "allowed_extensions": self.ALLOWED_EXTENSIONS
        }
    
    @property
    def feature_config(self) -> Dict[str, Any]:
        """Get feature flags configuration"""
        return {
            "project_management": self.FEATURE_PROJECT_MANAGEMENT,
            "ticket_system": self.FEATURE_TICKET_SYSTEM,
            "file_upload": self.FEATURE_FILE_UPLOAD,
            "real_time_chat": self.FEATURE_REAL_TIME_CHAT,
            "user_authentication": self.FEATURE_USER_AUTHENTICATION,
            "sentiment_analysis": self.FEATURE_SENTIMENT_ANALYSIS,
            "ai_suggestions": self.FEATURE_AI_SUGGESTIONS,
            "message_moderation": self.FEATURE_MESSAGE_MODERATION
        }
    
    @property
    def system_config(self) -> Dict[str, Any]:
        """Get system configuration"""
        return {
            "monitoring": {
                "metrics_enabled": self.METRICS_ENABLED,
                "health_check_enabled": self.HEALTH_CHECK_ENABLED,
                "performance_monitoring": self.PERFORMANCE_MONITORING
            },
            "cache": {
                "enabled": self.CACHE_ENABLED,
                "backend": self.CACHE_BACKEND,
                "ttl": self.CACHE_TTL,
                "redis_url": self.REDIS_URL if self.CACHE_BACKEND == "redis" else None
            },
            "websocket": {
                "enabled": self.WEBSOCKET_ENABLED,
                "ping_interval": self.WEBSOCKET_PING_INTERVAL,
                "ping_timeout": self.WEBSOCKET_PING_TIMEOUT,
                "max_size": self.WEBSOCKET_MAX_SIZE
            },
            "background_tasks": {
                "enabled": self.BACKGROUND_TASKS_ENABLED,
                "workers": self.TASK_WORKERS,
                "retry_attempts": self.TASK_RETRY_ATTEMPTS
            }
        }

    def get_safe_settings(self) -> Dict[str, Any]:
        """Get settings without sensitive data for logging"""
        return {
            "app": {
                "name": self.APP_NAME,
                "version": self.APP_VERSION,
                "environment": self.APP_ENVIRONMENT,
                "debug": self.APP_DEBUG,
                "url": self.APP_URL,
                "timezone": self.APP_TIMEZONE
            },
            "server": {
                "host": self.HOST,
                "port": self.PORT,
                "reload": self.RELOAD,
                "workers": self.WORKERS
            },
            "database": {
                "url": self.DATABASE_URL.split('://')[0] + '://***',
                "timeout": self.DATABASE_TIMEOUT,
                "pool_size": self.DATABASE_POOL_SIZE
            },
            "ai": {
                "enabled": self.AI_ENABLED,
                "ollama_base_url": self.OLLAMA_BASE_URL,
                "default_model": self.OLLAMA_DEFAULT_MODEL,
                "rag_enabled": self.RAG_ENABLED
            },
            "features": self.feature_config,
            "security": {
                "rate_limiting_enabled": self.RATE_LIMIT_ENABLED,
                "jwt_enabled": bool(self.JWT_SECRET_KEY)
            },
            "logging": {
                "level": self.LOG_LEVEL,
                "format": self.LOG_FORMAT
            }
        }

    def validate_feature_dependencies(self) -> List[str]:
        """Validate feature dependencies and return warnings"""
        warnings = []
        
        if self.FEATURE_USER_AUTHENTICATION and not self.JWT_SECRET_KEY:
            warnings.append("User authentication enabled but JWT_SECRET_KEY not set")
        
        if self.FEATURE_REAL_TIME_CHAT and not self.WEBSOCKET_ENABLED:
            warnings.append("Real-time chat enabled but WebSocket disabled")
        
        if self.RAG_ENABLED and not self.AI_ENABLED:
            warnings.append("RAG enabled but AI is disabled")
        
        if self.FEATURE_MESSAGE_MODERATION and not self.AI_ENABLED:
            warnings.append("Message moderation enabled but AI is disabled")
        
        if self.CACHE_ENABLED and self.CACHE_BACKEND == "redis" and not self.REDIS_URL:
            warnings.append("Redis cache enabled but REDIS_URL not configured")
        
        return warnings

# Create settings instance with error handling
try:
    settings = EnvironmentSettings()
    
    # Validate feature dependencies
    feature_warnings = settings.validate_feature_dependencies()
    if feature_warnings:
        print("⚠️ Feature dependency warnings:")
        for warning in feature_warnings:
            print(f"   • {warning}")
            
except Exception as e:
    print(f"❌ Error loading settings: {e}")
    print("💡 Please check your .env file or environment variables")
    print("📋 Required environment variables:")
    print("   - APP_SECRET_KEY (min 32 chars)")
    print("   - DATABASE_URL (sqlite:///path or postgresql://user:pass@host/db)")
    print("   - OLLAMA_BASE_URL (http://localhost:11434)")
    raise