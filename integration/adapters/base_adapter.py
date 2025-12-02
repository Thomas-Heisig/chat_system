"""
🔌 Base Adapter Interface

Abstract base class for platform adapters.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional


class BaseAdapter(ABC):
    """
    Abstract base adapter for external platform integration.
    """
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.platform_name = self.__class__.__name__.replace("Adapter", "").lower()
    
    @abstractmethod
    async def send(
        self,
        message: Dict[str, Any],
        target: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Send message to platform.
        
        Args:
            message: Message in platform format
            target: Target channel/user
            
        Returns:
            Send result
        """
        pass
    
    @abstractmethod
    async def normalize(
        self,
        raw_message: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Normalize platform message to unified format.
        
        Args:
            raw_message: Platform-specific message
            
        Returns:
            Unified message format
        """
        pass
    
    @abstractmethod
    async def authenticate(self) -> bool:
        """
        Authenticate with platform.
        
        Returns:
            True if authentication successful
        """
        pass
    
    @abstractmethod
    async def get_status(self) -> Dict[str, Any]:
        """
        Get adapter status.
        
        Returns:
            Status information
        """
        pass
    
    def get_info(self) -> Dict[str, Any]:
        """Get adapter information"""
        return {
            "platform": self.platform_name,
            "adapter_class": self.__class__.__name__,
            "config": {
                k: "***" if "key" in k.lower() or "secret" in k.lower() or "token" in k.lower() else v
                for k, v in self.config.items()
            }
        }
