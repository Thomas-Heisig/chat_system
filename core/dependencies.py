"""
Dependency Injection Container for FastAPI Application

This module provides a centralized dependency injection system using FastAPI's
native dependency injection patterns. It ensures:
- Single instance (singleton) patterns for stateful services
- Clean separation of concerns
- Easy testing through dependency override
- Type-safe dependency resolution

Architecture Decision:
- Uses FastAPI's Depends() system (native, no external libraries)
- Lazy initialization for expensive resources
- Thread-safe singleton pattern for shared state
- Easy to mock for testing

See: ADR-010-dependency-injection-pattern.md
"""

from functools import lru_cache
from typing import Generator

from sqlalchemy.orm import Session

from config.settings import enhanced_logger
from database.connection import get_db_session
from database.repositories import (
    FileRepository,
    MessageRepository,
    ProjectRepository,
    StatisticsRepository,
    TicketRepository,
    UserRepository,
)
from services.ai_service import AIService
from services.auth_service import AuthService
from services.file_service import FileService
from services.message_service import MessageService
from services.plugin_service import PluginService
from services.project_service import ProjectService
from services.settings_service import SettingsService


# ============================================================================
# Database Dependencies
# ============================================================================


def get_db() -> Generator[Session, None, None]:
    """
    Database session dependency.

    Provides a SQLAlchemy session with automatic cleanup.
    Each request gets its own session.

    Yields:
        SQLAlchemy Session object

    Example:
        @router.get("/users")
        async def get_users(db: Session = Depends(get_db)):
            return db.query(User).all()
    """
    db = get_db_session()
    try:
        yield db
    finally:
        db.close()


# ============================================================================
# Repository Dependencies (Scoped per request)
# ============================================================================


def get_user_repository(db: Session = None) -> UserRepository:
    """Get UserRepository instance"""
    return UserRepository(db)


def get_message_repository(db: Session = None) -> MessageRepository:
    """Get MessageRepository instance"""
    return MessageRepository(db)


def get_project_repository(db: Session = None) -> ProjectRepository:
    """Get ProjectRepository instance"""
    return ProjectRepository(db)


def get_ticket_repository(db: Session = None) -> TicketRepository:
    """Get TicketRepository instance"""
    return TicketRepository(db)


def get_file_repository(db: Session = None) -> FileRepository:
    """Get FileRepository instance"""
    return FileRepository(db)


def get_statistics_repository(db: Session = None) -> StatisticsRepository:
    """Get StatisticsRepository instance"""
    return StatisticsRepository(db)


# ============================================================================
# Service Dependencies (Singleton pattern with @lru_cache)
# ============================================================================


@lru_cache()
def get_auth_service() -> AuthService:
    """
    Get singleton AuthService instance.

    The AuthService maintains JWT keys and authentication state,
    so we use a singleton pattern to avoid regenerating keys.

    Returns:
        Singleton AuthService instance
    """
    enhanced_logger.info("Initializing singleton AuthService")
    return AuthService()


@lru_cache()
def get_settings_service() -> SettingsService:
    """
    Get singleton SettingsService instance.

    Settings are loaded once and cached for the application lifetime.

    Returns:
        Singleton SettingsService instance
    """
    enhanced_logger.info("Initializing singleton SettingsService")
    return SettingsService()


@lru_cache()
def get_plugin_service() -> PluginService:
    """
    Get singleton PluginService instance.

    Plugin registry is maintained globally across all requests.

    Returns:
        Singleton PluginService instance
    """
    enhanced_logger.info("Initializing singleton PluginService")
    return PluginService()


@lru_cache()
def get_ai_service() -> AIService:
    """
    Get singleton AIService instance.

    AI connections (Ollama, OpenAI) are expensive to establish,
    so we reuse a single instance.

    Returns:
        Singleton AIService instance
    """
    enhanced_logger.info("Initializing singleton AIService")
    return AIService()


# ============================================================================
# Composite Service Dependencies (Created per request with dependencies)
# ============================================================================


def get_message_service(
    repository: MessageRepository = None,
) -> MessageService:
    """
    Get MessageService instance with injected repository.

    Args:
        repository: MessageRepository instance (injected)

    Returns:
        MessageService instance with dependencies

    Example:
        @router.post("/messages")
        async def create_message(
            service: MessageService = Depends(get_message_service)
        ):
            return service.create_message(...)
    """
    if repository is None:
        repository = get_message_repository()
    return MessageService(repository)


def get_file_service(
    repository: FileRepository = None,
) -> FileService:
    """
    Get FileService instance with injected repository.

    Args:
        repository: FileRepository instance (injected)

    Returns:
        FileService instance with dependencies
    """
    if repository is None:
        repository = get_file_repository()
    return FileService(repository)


def get_project_service(
    repository: ProjectRepository = None,
) -> ProjectService:
    """
    Get ProjectService instance with injected repository.

    Args:
        repository: ProjectRepository instance (injected)

    Returns:
        ProjectService instance with dependencies
    """
    if repository is None:
        repository = get_project_repository()
    return ProjectService(repository)


# ============================================================================
# Dependency Override Support (for testing)
# ============================================================================


_dependency_overrides = {}


def override_dependency(dependency_func, override_func):
    """
    Override a dependency for testing purposes.

    Args:
        dependency_func: Original dependency function
        override_func: Replacement function

    Example:
        # In tests
        override_dependency(get_auth_service, lambda: MockAuthService())
        # Now all endpoints will use MockAuthService

        # Cleanup
        clear_dependency_overrides()
    """
    _dependency_overrides[dependency_func] = override_func
    enhanced_logger.debug(
        f"Dependency overridden: {dependency_func.__name__} -> {override_func.__name__}"
    )


def clear_dependency_overrides():
    """Clear all dependency overrides (typically in test teardown)"""
    _dependency_overrides.clear()
    enhanced_logger.debug("All dependency overrides cleared")


def get_dependency(dependency_func):
    """
    Get dependency with override support.

    Returns the overridden dependency if available, otherwise the original.
    """
    return _dependency_overrides.get(dependency_func, dependency_func)


# ============================================================================
# Cache Management
# ============================================================================


def clear_singleton_cache():
    """
    Clear all singleton caches.

    This should be called:
    - During application shutdown
    - When services need to be reinitialized
    - In test teardown to ensure clean state

    Warning:
        This will force recreation of all singleton services on next access.
        Use with caution in production.
    """
    enhanced_logger.info("Clearing singleton service cache")
    get_auth_service.cache_clear()
    get_settings_service.cache_clear()
    get_plugin_service.cache_clear()
    get_ai_service.cache_clear()
    enhanced_logger.info("Singleton service cache cleared")


# ============================================================================
# Health Check Dependencies
# ============================================================================


def check_dependencies_health() -> Dict[str, Any]:
    """
    Check health status of all dependencies.

    Returns:
        Dictionary with health status of each dependency

    Example response:
        {
            "database": "healthy",
            "auth_service": "healthy",
            "ai_service": "degraded",
            "plugin_service": "healthy"
        }
    """
    health_status = {}

    # Check database
    try:
        db = get_db_session()
        db.execute("SELECT 1")
        health_status["database"] = "healthy"
        db.close()
    except Exception as e:
        health_status["database"] = f"unhealthy: {str(e)}"

    # Check services
    try:
        _auth_service = get_auth_service()  # noqa: F841
        health_status["auth_service"] = "healthy"
    except Exception as e:
        health_status["auth_service"] = f"unhealthy: {str(e)}"

    try:
        _ai_service = get_ai_service()  # noqa: F841
        health_status["ai_service"] = "healthy"
    except Exception as e:
        health_status["ai_service"] = f"unhealthy: {str(e)}"

    try:
        _plugin_service = get_plugin_service()  # noqa: F841
        health_status["plugin_service"] = "healthy"
    except Exception as e:
        health_status["plugin_service"] = f"unhealthy: {str(e)}"

    return health_status
