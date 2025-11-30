# config/settings.py
import os
import sys
import logging
from typing import List, Dict, Any, Optional
from pathlib import Path
from pydantic import Field
try:
    from pydantic_settings import BaseSettings
except ImportError:
    # Fallback für ältere Pydantic Versionen
    from pydantic import BaseSettings
from logging.config import dictConfig
from datetime import datetime

class EnvironmentSettings(BaseSettings):
    """Environment-specific settings - Kombination aus alter und neuer Struktur"""
    
    # Application (alte Variablen)
    APP_NAME: str = "Chat System"
    APP_VERSION: str = "2.0.0"
    APP_ENVIRONMENT: str = Field(default="development")
    APP_DEBUG: bool = Field(default=True)
    APP_SECRET_KEY: str = Field(default="your-secret-key-here-change-in-production")
    
    # Server
    HOST: str = Field(default="0.0.0.0")
    PORT: int = Field(default=8000)
    
    # CORS - Default development origins, can be overridden via environment
    CORS_ORIGINS: List[str] = Field(default=["http://localhost:3000", "http://127.0.0.1:3000", "http://localhost:8000"])
    
    def get_effective_debug(self) -> bool:
        """Get effective debug mode - auto-disabled in production"""
        if self.APP_ENVIRONMENT.lower() == "production":
            return False
        return self.APP_DEBUG
    
    def get_effective_cors_origins(self) -> List[str]:
        """Get effective CORS origins - wildcards filtered in production"""
        if self.APP_ENVIRONMENT.lower() == "production":
            # Filter out any wildcard entries in production
            safe_origins = [origin for origin in self.CORS_ORIGINS if origin != "*"]
            return safe_origins
        return self.CORS_ORIGINS
    
    # Security
    SECRET_KEY: str = Field(default="your-secret-key-here")
    RATE_LIMIT_ENABLED: bool = Field(default=True)
    RATE_LIMIT_REQUESTS: int = Field(default=100)
    RATE_LIMIT_WINDOW: int = Field(default=60)
    
    # AI Configuration
    AI_ENABLED: bool = Field(default=True)
    OLLAMA_BASE_URL: str = Field(default="http://localhost:11434")
    OLLAMA_DEFAULT_MODEL: str = Field(default="llama2")
    AI_MAX_RESPONSE_LENGTH: int = Field(default=1000)
    AI_CONTEXT_MESSAGES: int = Field(default=10)
    
    # RAG Configuration
    RAG_ENABLED: bool = Field(default=False)
    VECTOR_STORE_ENABLED: bool = Field(default=False)
    
    # Features
    FEATURE_PROJECT_MANAGEMENT: bool = Field(default=True)
    FEATURE_TICKET_SYSTEM: bool = Field(default=True)
    FEATURE_FILE_UPLOAD: bool = Field(default=True)
    FEATURE_USER_AUTHENTICATION: bool = Field(default=False)
    
    # File Upload (alte Variablen)
    UPLOAD_FOLDER: str = Field(default="uploads")
    MAX_FILE_SIZE: int = Field(default=10 * 1024 * 1024)
    ALLOWED_EXTENSIONS: List[str] = Field(default=["jpg", "jpeg", "png", "gif", "pdf", "txt", "doc", "docx"])
    
    # Database
    DATABASE_URL: str = Field(default="chat_system.db")
    DATABASE_TIMEOUT: int = Field(default=30)
    DATABASE_POOL_SIZE: int = Field(default=10)
    DATABASE_MAX_OVERFLOW: int = Field(default=20)
    
    # Logging (alte Variablen)
    LOG_LEVEL: str = Field(default="INFO")
    LOG_FORMAT: str = Field(default="console")
    LOG_FILE: str = Field(default="chat_system.log")
    
    # Legacy Features für Kompatibilität
    PROJECT_FEATURES: bool = Field(default=True)
    TICKET_SYSTEM_ENABLED: bool = Field(default=True)
    WEBSOCKET_ENABLED: bool = Field(default=True)
    
    # Properties für Kompatibilität
    @property
    def ENVIRONMENT(self) -> str:
        return self.APP_ENVIRONMENT
    
    @property
    def DEBUG(self) -> bool:
        return self.APP_DEBUG
    
    @property
    def UPLOAD_DIR(self) -> str:
        return self.UPLOAD_FOLDER
    
    @property
    def ALLOWED_FILE_TYPES(self) -> List[str]:
        return self.ALLOWED_EXTENSIONS
    
    @property
    def is_development(self) -> bool:
        return self.APP_ENVIRONMENT.lower() == "development"
    
    @property
    def is_production(self) -> bool:
        return self.APP_ENVIRONMENT.lower() == "production"
    
    @property
    def is_testing(self) -> bool:
        return self.APP_ENVIRONMENT.lower() == "testing"

    # Pydantic v2 Config
    class Config:
        env_file = ".env"
        case_sensitive = False
        extra = "ignore"

# Initialize settings
settings = EnvironmentSettings()

# Erweiterte Logging-Funktionen aus alter Datei
def setup_logging(level: str = None, log_file: str = None, format_type: str = None):
    """Setup comprehensive logging configuration with enhanced features - Kompatibel mit alter Funktion"""
    
    # Verwende Settings als Default, falls keine Parameter übergeben
    level = level or settings.LOG_LEVEL
    log_file = log_file or settings.LOG_FILE
    format_type = format_type or settings.LOG_FORMAT
    
    level_mapping = {
        "DEBUG": logging.DEBUG,
        "INFO": logging.INFO,
        "WARNING": logging.WARNING,
        "ERROR": logging.ERROR,
        "CRITICAL": logging.CRITICAL
    }
    
    log_level = level_mapping.get(level.upper(), logging.INFO)
    
    # Create logs directory with proper structure
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)
    log_path = log_dir / log_file
    
    # Configure root logger
    logger = logging.getLogger()
    logger.setLevel(log_level)

    # Clear existing handlers to avoid duplicates
    for handler in logger.handlers[:]:
        logger.removeHandler(handler)

    # Enhanced formatters
    if format_type == "json":
        import json
        class JsonFormatter(logging.Formatter):
            def format(self, record):
                log_entry = {
                    "timestamp": self.formatTime(record, "%Y-%m-%d %H:%M:%S.%f"),
                    "level": record.levelname,
                    "logger": record.name,
                    "message": record.getMessage(),
                    "module": record.module,
                    "function": record.funcName,
                    "line": record.lineno,
                    "process": record.process,
                    "thread": record.threadName
                }
                if record.exc_info:
                    log_entry["exception"] = self.formatException(record.exc_info)
                if hasattr(record, 'custom_fields'):
                    log_entry.update(record.custom_fields)
                return json.dumps(log_entry)
        
        formatter = JsonFormatter()
        
    elif format_type == "detailed":
        formatter = logging.Formatter(
            '%(asctime)s | %(levelname)-8s | %(name)-20s | %(module)-15s | %(funcName)-20s | %(lineno)-4d | %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
    else:
        # Enhanced console formatter with colors and better formatting
        class ColorFormatter(logging.Formatter):
            # ANSI color codes
            grey = "\x1b[38;20m"
            green = "\x1b[32;20m"
            yellow = "\x1b[33;20m"
            red = "\x1b[31;20m"
            bold_red = "\x1b[31;1m"
            blue = "\x1b[34;20m"
            magenta = "\x1b[35;20m"
            cyan = "\x1b[36;20m"
            reset = "\x1b[0m"
            
            # Enhanced format with better structure
            base_format = "%(asctime)s | %(levelname)-8s | %(name)-15s | %(message)s (%(filename)s:%(lineno)d)"

            FORMATS = {
                logging.DEBUG: cyan + base_format + reset,
                logging.INFO: green + base_format + reset,
                logging.WARNING: yellow + base_format + reset,
                logging.ERROR: red + base_format + reset,
                logging.CRITICAL: bold_red + base_format + reset
            }

            def format(self, record):
                log_fmt = self.FORMATS.get(record.levelno, self.FORMATS[logging.INFO])
                formatter = logging.Formatter(log_fmt, datefmt='%H:%M:%S')
                return formatter.format(record)
        
        # Use simple formatter for non-TTY outputs
        formatter = ColorFormatter() if sys.stdout.isatty() else logging.Formatter(
            '%(asctime)s | %(levelname)-8s | %(name)-15s | %(message)s',
            datefmt='%H:%M:%S'
        )

    # File handler with rotation
    try:
        from logging.handlers import RotatingFileHandler
        file_handler = RotatingFileHandler(
            log_path, 
            maxBytes=10*1024*1024,  # 10MB
            backupCount=5,
            encoding='utf-8'
        )
        file_handler.setFormatter(logging.Formatter(
            '%(asctime)s | %(levelname)-8s | %(name)-20s | %(module)-15s | %(funcName)-20s | %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        ))
    except ImportError:
        # Fallback to basic FileHandler
        file_handler = logging.FileHandler(log_path, encoding='utf-8')
        file_handler.setFormatter(logging.Formatter(
            '%(asctime)s | %(levelname)-8s | %(name)s | %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        ))

    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)

    # Add handlers
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)

    # Configure specific loggers
    third_party_loggers = ['urllib3', 'requests', 'werkzeug', 'asyncio']
    for lib_logger in third_party_loggers:
        logging.getLogger(lib_logger).setLevel(logging.WARNING)

    # Get module logger for initialization message
    module_logger = logging.getLogger(__name__)
    module_logger.info(f"🚀 Logging initialized - Level: {level}, Format: {format_type}")
    module_logger.info(f"📁 Log file: {log_path}")
    
    return module_logger

# Custom logger with additional methods - Vollständig aus alter Datei übernommen
class EnhancedLogger:
    def __init__(self, name: str):
        self.logger = logging.getLogger(name)
    
    def debug(self, msg: str, **kwargs):
        self.logger.debug(msg, extra={'custom_fields': kwargs})
    
    def info(self, msg: str, **kwargs):
        self.logger.info(msg, extra={'custom_fields': kwargs})
    
    def warning(self, msg: str, **kwargs):
        self.logger.warning(msg, extra={'custom_fields': kwargs})
    
    def error(self, msg: str, **kwargs):
        self.logger.error(msg, extra={'custom_fields': kwargs})
    
    def critical(self, msg: str, **kwargs):
        self.logger.critical(msg, extra={'custom_fields': kwargs})
    
    def performance(self, operation: str, duration: float, **kwargs):
        """Log performance metrics"""
        if duration > 1.0:  # Log as warning if operation takes more than 1 second
            self.warning(f"Performance issue: {operation} took {duration:.2f}s", 
                        operation=operation, duration=duration, **kwargs)
        else:
            self.debug(f"Performance: {operation} took {duration:.2f}s", 
                      operation=operation, duration=duration, **kwargs)
    
    def security(self, event: str, user: str = None, ip: str = None, **kwargs):
        """Log security-related events"""
        self.warning(f"Security event: {event}", 
                    security_event=event, user=user, ip=ip, **kwargs)
    
    def database(self, operation: str, table: str = None, duration: float = None, **kwargs):
        """Log database operations"""
        self.debug(f"Database {operation} on {table}", 
                  db_operation=operation, table=table, duration=duration, **kwargs)

# Initialize logging with settings
logger = setup_logging(settings.LOG_LEVEL, settings.LOG_FILE, settings.LOG_FORMAT)

# Create enhanced logger instance
enhanced_logger = EnhancedLogger(__name__)

# Configuration groups for easy access (aus neuer Datei)
class AIConfig:
    """AI-related configuration"""
    def __init__(self, settings: EnvironmentSettings):
        self.enabled = settings.AI_ENABLED
        self.ollama_base_url = settings.OLLAMA_BASE_URL
        self.default_model = settings.OLLAMA_DEFAULT_MODEL
        self.max_response_length = settings.AI_MAX_RESPONSE_LENGTH
        self.context_messages = settings.AI_CONTEXT_MESSAGES
        self.rag_enabled = settings.RAG_ENABLED
        self.vector_store_enabled = settings.VECTOR_STORE_ENABLED

class SecurityConfig:
    """Security-related configuration"""
    def __init__(self, settings: EnvironmentSettings):
        self.secret_key = settings.SECRET_KEY
        self.rate_limiting_enabled = settings.RATE_LIMIT_ENABLED
        self.rate_limit_requests = settings.RATE_LIMIT_REQUESTS
        self.rate_limit_window = settings.RATE_LIMIT_WINDOW

class FileConfig:
    """File upload configuration"""
    def __init__(self, settings: EnvironmentSettings):
        self.max_file_size = settings.MAX_FILE_SIZE
        self.allowed_file_types = settings.ALLOWED_EXTENSIONS
        self.upload_dir = Path(settings.UPLOAD_FOLDER)
        self.upload_dir.mkdir(exist_ok=True)

class FeatureConfig:
    """Feature flags configuration"""
    def __init__(self, settings: EnvironmentSettings):
        self.projects = settings.FEATURE_PROJECT_MANAGEMENT
        self.tickets = settings.FEATURE_TICKET_SYSTEM
        self.file_upload = settings.FEATURE_FILE_UPLOAD
        self.user_auth = settings.FEATURE_USER_AUTHENTICATION

class SystemConfig:
    """System configuration"""
    def __init__(self, settings: EnvironmentSettings):
        self.app_name = settings.APP_NAME
        self.app_version = settings.APP_VERSION
        self.environment = settings.APP_ENVIRONMENT
        self.debug = settings.APP_DEBUG
        self.host = settings.HOST
        self.port = settings.PORT
        self.cors_origins = settings.CORS_ORIGINS
        self.database_url = settings.DATABASE_URL

# Create configuration groups
ai_config = AIConfig(settings)
security_config = SecurityConfig(settings)
file_config = FileConfig(settings)
feature_config = FeatureConfig(settings)
system_config = SystemConfig(settings)

# Configuration validation and logging - Kombination aus alter und neuer Datei
def log_configuration_summary():
    """Log comprehensive configuration summary"""
    
    # Basic application info
    logger.info(f"⚙️ Application: {settings.APP_NAME} v{settings.APP_VERSION}")
    logger.info(f"🌍 Environment: {settings.APP_ENVIRONMENT}")
    logger.info(f"🔧 Debug Mode: {settings.APP_DEBUG}")
    logger.info(f"🚀 Server: {settings.HOST}:{settings.PORT}")
    
    # Security configuration
    logger.info(f"🔐 CORS Origins: {len(settings.CORS_ORIGINS)} configured")
    logger.info(f"🛡️ Rate Limiting: {settings.RATE_LIMIT_ENABLED}")
    
    # AI features
    logger.info(f"🤖 AI Enabled: {settings.AI_ENABLED}")
    if settings.AI_ENABLED:
        logger.info(f"   📍 Ollama URL: {settings.OLLAMA_BASE_URL}")
        logger.info(f"   🧠 Default Model: {settings.OLLAMA_DEFAULT_MODEL}")
        logger.info(f"   📚 RAG Enabled: {settings.RAG_ENABLED}")
        logger.info(f"   🗃️ Vector Store: {settings.VECTOR_STORE_ENABLED}")
    
    # Database configuration
    logger.info(f"💾 Database: {settings.DATABASE_URL.split('://')[0] if settings.DATABASE_URL else 'SQLite'}")
    
    # File upload configuration
    logger.info(f"📁 Upload Folder: {settings.UPLOAD_FOLDER}")
    logger.info(f"📄 Allowed Extensions: {len(settings.ALLOWED_EXTENSIONS)} file types")
    
    # Logging configuration
    logger.info(f"📝 Log Level: {settings.LOG_LEVEL}")
    logger.info(f"📊 Log Format: {settings.LOG_FORMAT}")

def validate_environment():
    """Validate environment configuration and log warnings with auto-correction for production"""
    
    warnings = []
    corrections_applied = []
    
    # Production environment checks with auto-correction
    if settings.is_production:
        # Debug mode is auto-disabled in production via get_effective_debug()
        if settings.APP_DEBUG and not settings.get_effective_debug():
            corrections_applied.append("Debug mode auto-disabled in production (get_effective_debug() returns False)")
        
        # CORS wildcard auto-filtered in production via get_effective_cors_origins()
        if "*" in settings.CORS_ORIGINS and "*" not in settings.get_effective_cors_origins():
            corrections_applied.append("Wildcard CORS origins auto-filtered in production")
        
        if not settings.APP_SECRET_KEY or len(settings.APP_SECRET_KEY) < 32:
            warnings.append("Weak or missing APP_SECRET_KEY in production - please set a secure key (min 32 chars)")
        
        if settings.DATABASE_URL and "sqlite" in settings.DATABASE_URL.lower():
            warnings.append("SQLite database in production - consider PostgreSQL for better performance")
        
        if not settings.CORS_ORIGINS or all(o == "*" for o in settings.CORS_ORIGINS):
            warnings.append("No valid CORS origins configured for production - API calls from browsers may fail")
    
    # Development environment informational warnings (less critical)
    if settings.is_development:
        if "*" in settings.CORS_ORIGINS:
            warnings.append("CORS is set to '*' - this is acceptable for development but restrict in production")
        if len(settings.APP_SECRET_KEY) < 32:
            warnings.append("Consider using a longer APP_SECRET_KEY (min 32 chars) for better security")
    
    # Feature-specific warnings (all environments)
    if settings.AI_ENABLED and not settings.OLLAMA_BASE_URL:
        warnings.append("AI enabled but OLLAMA_BASE_URL not configured")
    
    if settings.RAG_ENABLED and not settings.VECTOR_STORE_ENABLED:
        warnings.append("RAG enabled but vector store not configured")
    
    # Log corrections that were auto-applied
    for correction in corrections_applied:
        logger.info(f"✅ Auto-correction: {correction}")
    
    # Log warnings
    for warning in warnings:
        logger.warning(f"⚠️ {warning}")
    
    return len(warnings) == 0

def get_system_info() -> Dict[str, Any]:
    """Get system information for logging - Aus alter Datei"""
    import platform
    try:
        import psutil
        psutil_available = True
    except ImportError:
        psutil_available = False
    
    try:
        if psutil_available:
            return {
                "platform": platform.system(),
                "platform_version": platform.version(),
                "python_version": platform.python_version(),
                "cpu_cores": psutil.cpu_count(),
                "memory_total": f"{psutil.virtual_memory().total / 1024 / 1024 / 1024:.1f} GB",
                "disk_usage": f"{psutil.disk_usage('.').percent:.1f}%",
                "process_id": os.getpid()
            }
        else:
            return {
                "platform": platform.system(),
                "python_version": platform.python_version(),
                "process_id": os.getpid(),
                "note": "psutil not available for detailed system info"
            }
    except Exception as e:
        return {
            "platform": platform.system(),
            "python_version": platform.python_version(),
            "process_id": os.getpid(),
            "error": f"Failed to get system info: {str(e)}"
        }

# Initialize configuration logging
log_configuration_summary()

# Validate environment
environment_valid = validate_environment()

# Log system information
system_info = get_system_info()
logger.info(f"💻 System Info: {system_info}")

# Log initialization status
if environment_valid:
    logger.info("✅ Environment configuration validated successfully")
else:
    logger.warning("⚠️ Environment configuration has warnings - check logs above")

# Log feature availability
logger.info("🔧 Available features:")
logger.info(f"   • File Upload: {hasattr(settings, 'UPLOAD_FOLDER')}")
logger.info(f"   • Project Management: {hasattr(settings, 'PROJECT_FEATURES') and settings.PROJECT_FEATURES}")
logger.info(f"   • Ticket System: {hasattr(settings, 'TICKET_SYSTEM_ENABLED') and settings.TICKET_SYSTEM_ENABLED}")
logger.info(f"   • Real-time Chat: {hasattr(settings, 'WEBSOCKET_ENABLED') and settings.WEBSOCKET_ENABLED}")

# Final initialization message
logger.info("🎉 Application configuration completed successfully!")

# Export public interface - Kombination aus beiden Dateien
__all__ = [
    'settings', 
    'logger', 
    'enhanced_logger', 
    'setup_logging', 
    'EnvironmentSettings',
    'EnhancedLogger',
    'validate_environment',
    'ai_config',
    'security_config', 
    'file_config',
    'feature_config',
    'system_config'
]