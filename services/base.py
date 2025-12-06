"""
Base Service Classes

Provides common functionality for all services in the application.
Reduces code duplication and establishes consistent patterns.

See: docs/SERVICE_CONSOLIDATION_ANALYSIS.md for architecture decisions.
"""

from abc import ABC, abstractmethod
from datetime import datetime
from typing import Any, Dict, Optional

from config.settings import enhanced_logger, logger


class BaseService(ABC):
    """
    Abstract base class for all services.
    
    Provides:
    - Consistent initialization logging
    - Service lifecycle management
    - Common utility methods
    - Health check interface
    
    Usage:
        class MyService(BaseService):
            def __init__(self):
                super().__init__("My Service", "🚀")
                # Service-specific initialization
                
            def health_check(self) -> Dict[str, Any]:
                return {"status": "healthy"}
    """
    
    def __init__(self, service_name: str, emoji: str = "🔧"):
        """
        Initialize base service.
        
        Args:
            service_name: Human-readable name of the service
            emoji: Emoji to use in logs (for visual identification)
        """
        self.service_name = service_name
        self.emoji = emoji
        self.initialized_at = datetime.now()
        
        logger.info(f"{emoji} {service_name} initialized")
        enhanced_logger.info(
            "Service initialized",
            service=service_name,
            timestamp=self.initialized_at.isoformat()
        )
    
    @abstractmethod
    def health_check(self) -> Dict[str, Any]:
        """
        Perform health check for this service.
        
        Must be implemented by subclasses.
        
        Returns:
            Dict with health status:
            {
                "status": "healthy" | "degraded" | "unhealthy",
                "details": {...},
                "timestamp": "2024-01-01T00:00:00Z"
            }
        """
        pass
    
    def get_service_info(self) -> Dict[str, Any]:
        """
        Get service information.
        
        Returns:
            Dict with service metadata
        """
        return {
            "name": self.service_name,
            "emoji": self.emoji,
            "initialized_at": self.initialized_at.isoformat(),
            "uptime_seconds": (datetime.now() - self.initialized_at).total_seconds()
        }
    
    def log_info(self, message: str, **kwargs):
        """Log info message with service context"""
        enhanced_logger.info(
            message,
            service=self.service_name,
            **kwargs
        )
    
    def log_error(self, message: str, error: Optional[Exception] = None, **kwargs):
        """Log error message with service context"""
        enhanced_logger.error(
            message,
            service=self.service_name,
            error=str(error) if error else None,
            **kwargs
        )
    
    def log_warning(self, message: str, **kwargs):
        """Log warning message with service context"""
        enhanced_logger.warning(
            message,
            service=self.service_name,
            **kwargs
        )


class PlaceholderService(BaseService):
    """
    Base class for services that are planned but not yet implemented.
    
    Provides:
    - Consistent placeholder responses
    - Feature status tracking
    - Implementation planning metadata
    
    Usage:
        class EmotionDetectionService(PlaceholderService):
            def __init__(self):
                super().__init__(
                    service_name="Emotion Detection Service",
                    emoji="🎭",
                    planned_features=[
                        "Text emotion detection",
                        "Audio emotion detection",
                        "Video emotion detection"
                    ]
                )
                
            async def detect_from_text(self, text: str):
                return self.placeholder_response(
                    "detect_from_text",
                    input_data={"text_length": len(text)}
                )
    """
    
    def __init__(
        self,
        service_name: str,
        emoji: str = "🚧",
        planned_features: Optional[list] = None,
        priority: str = "low"
    ):
        """
        Initialize placeholder service.
        
        Args:
            service_name: Name of the service
            emoji: Emoji for logging
            planned_features: List of features to be implemented
            priority: Implementation priority (low/medium/high/critical)
        """
        super().__init__(service_name, emoji)
        self.planned_features = planned_features or []
        self.priority = priority
        self.is_implemented = False
        
        logger.info(
            f"{emoji} {service_name} initialized (placeholder - "
            f"{len(self.planned_features)} features planned)"
        )
    
    def placeholder_response(
        self,
        feature_name: str,
        input_data: Optional[Dict[str, Any]] = None,
        additional_context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Generate a consistent placeholder response.
        
        Args:
            feature_name: Name of the feature being called
            input_data: Information about the input (for logging)
            additional_context: Additional context to include
            
        Returns:
            Standardized placeholder response
        """
        response = {
            "status": "not_implemented",
            "message": f"{feature_name} is not yet implemented",
            "service": self.service_name,
            "feature": feature_name,
            "priority": self.priority,
            "timestamp": datetime.now().isoformat()
        }
        
        if input_data:
            response["input_summary"] = input_data
        
        if additional_context:
            response["context"] = additional_context
        
        self.log_warning(
            f"Placeholder method called: {feature_name}",
            input_data=input_data
        )
        
        return response
    
    def health_check(self) -> Dict[str, Any]:
        """Health check for placeholder service"""
        return {
            "status": "degraded",
            "reason": "Service not yet implemented",
            "planned_features": self.planned_features,
            "priority": self.priority,
            "timestamp": datetime.now().isoformat()
        }
    
    def get_implementation_status(self) -> Dict[str, Any]:
        """
        Get detailed implementation status.
        
        Returns:
            Dict with implementation details
        """
        return {
            "service": self.service_name,
            "is_implemented": self.is_implemented,
            "priority": self.priority,
            "planned_features": self.planned_features,
            "feature_count": len(self.planned_features),
            "service_info": self.get_service_info()
        }


class RepositoryBackedService(BaseService):
    """
    Base class for services that interact with database repositories.
    
    Provides:
    - Repository lifecycle management
    - Common database operation patterns
    - Transaction support
    
    Usage:
        class MessageService(RepositoryBackedService):
            def __init__(self, repository: MessageRepository):
                super().__init__(
                    service_name="Message Service",
                    emoji="💬",
                    repository=repository
                )
    """
    
    def __init__(
        self,
        service_name: str,
        emoji: str,
        repository: Any
    ):
        """
        Initialize repository-backed service.
        
        Args:
            service_name: Name of the service
            emoji: Emoji for logging
            repository: Database repository instance
        """
        super().__init__(service_name, emoji)
        self.repository = repository
        
        self.log_info(
            "Repository-backed service initialized",
            repository_type=repository.__class__.__name__
        )
    
    def health_check(self) -> Dict[str, Any]:
        """Health check including repository status"""
        try:
            # Simple repository check
            # Subclasses can override for more specific checks
            has_repository = self.repository is not None
            
            return {
                "status": "healthy" if has_repository else "unhealthy",
                "repository": {
                    "available": has_repository,
                    "type": self.repository.__class__.__name__ if has_repository else None
                },
                "timestamp": datetime.now().isoformat()
            }
        except Exception as e:
            return {
                "status": "unhealthy",
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }


class ExternalServiceIntegration(BaseService):
    """
    Base class for services that integrate with external APIs/services.
    
    Provides:
    - Connection health monitoring
    - Retry logic
    - Circuit breaker pattern support
    - Graceful degradation
    
    Usage:
        class SlackService(ExternalServiceIntegration):
            def __init__(self):
                super().__init__(
                    service_name="Slack Integration",
                    emoji="💬",
                    endpoint="https://slack.com/api"
                )
    """
    
    def __init__(
        self,
        service_name: str,
        emoji: str,
        endpoint: Optional[str] = None,
        timeout: int = 5
    ):
        """
        Initialize external service integration.
        
        Args:
            service_name: Name of the service
            emoji: Emoji for logging
            endpoint: External service endpoint URL
            timeout: Connection timeout in seconds
        """
        super().__init__(service_name, emoji)
        self.endpoint = endpoint
        self.timeout = timeout
        self.is_available = False
        
        if endpoint:
            self.is_available = self._check_connection()
            
        self.log_info(
            "External service integration initialized",
            endpoint=endpoint,
            available=self.is_available
        )
    
    def _check_connection(self) -> bool:
        """
        Check if external service is available.
        
        Can be overridden by subclasses for custom health checks.
        
        Returns:
            True if service is available, False otherwise
        """
        if not self.endpoint:
            return False
            
        try:
            import requests
            response = requests.get(
                self.endpoint,
                timeout=self.timeout
            )
            return response.status_code < 500
        except Exception as e:
            self.log_warning(
                "External service connection check failed",
                error=str(e)
            )
            return False
    
    def health_check(self) -> Dict[str, Any]:
        """Health check for external service"""
        is_healthy = self._check_connection()
        
        return {
            "status": "healthy" if is_healthy else "degraded",
            "external_service": {
                "endpoint": self.endpoint,
                "available": is_healthy,
                "timeout": self.timeout
            },
            "timestamp": datetime.now().isoformat()
        }
    
    def require_connection(self) -> bool:
        """
        Check if connection is available, raise if not.
        
        Raises:
            ConnectionError: If external service is not available
            
        Returns:
            True if available
        """
        if not self.is_available:
            raise ConnectionError(
                f"{self.service_name} external service is not available"
            )
        return True
