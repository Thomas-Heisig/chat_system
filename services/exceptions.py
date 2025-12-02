"""
Exception classes for the chat system services.
"""


class ServiceException(Exception):
    """Base exception for all service-related errors."""
    pass


class ExternalAIUnavailableError(ServiceException):
    """
    Raised when external AI service (Ollama, OpenAI, etc.) is unavailable.
    
    This exception is used to trigger fallback mechanisms like Elyza service
    when the primary AI service cannot be reached.
    
    Example:
        try:
            response = await ai_service.generate_response(prompt)
        except ExternalAIUnavailableError:
            # Fallback to Elyza or other simple response
            if ENABLE_ELYZA_FALLBACK:
                response = elyza_service.generate_response(prompt)
    """
    
    def __init__(self, message: str = "External AI service is unavailable", service_name: str = None):
        self.service_name = service_name
        super().__init__(message)


class DatabaseConnectionError(ServiceException):
    """Raised when database connection fails."""
    pass


class ValidationError(ServiceException):
    """Raised when input validation fails."""
    pass


class AuthenticationError(ServiceException):
    """Raised when authentication fails."""
    pass


class AuthorizationError(ServiceException):
    """Raised when user is not authorized for an action."""
    pass


class ResourceNotFoundError(ServiceException):
    """Raised when a requested resource is not found."""
    
    def __init__(self, resource_type: str, resource_id: str):
        self.resource_type = resource_type
        self.resource_id = resource_id
        message = f"{resource_type} with ID '{resource_id}' not found"
        super().__init__(message)
