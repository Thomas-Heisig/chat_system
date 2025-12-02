"""
🌉 Messaging Bridge

API Gateway for external platform integration with pluggable adapters.
"""

from typing import Dict, Any, List, Optional
from datetime import datetime
from config.settings import logger


class MessagingBridge:
    """
    Central messaging bridge for external platform integration.
    
    Features:
    - Unified message format
    - Pluggable platform adapters
    - Protocol translation
    - Rate limiting per platform
    - Message queuing and retry
    """
    
    def __init__(self):
        self.adapters: Dict[str, Any] = {}
        self.message_queue: List[Dict] = []
        self.rate_limits: Dict[str, Dict] = {}
        
        logger.info("🌉 Messaging Bridge initialized")
    
    def register_adapter(
        self,
        platform: str,
        adapter: Any,
        rate_limit: Optional[Dict[str, int]] = None
    ):
        """
        Register a platform adapter.
        
        Args:
            platform: Platform name (e.g., 'slack', 'teams')
            adapter: Adapter instance
            rate_limit: Rate limit configuration
        """
        self.adapters[platform] = adapter
        
        if rate_limit:
            self.rate_limits[platform] = {
                "max_messages": rate_limit.get("max_messages", 100),
                "window_seconds": rate_limit.get("window_seconds", 60),
                "current_count": 0,
                "window_start": datetime.now()
            }
        
        logger.info(f"🔌 Adapter registered: {platform}")
    
    async def send_message(
        self,
        platform: str,
        message: Dict[str, Any],
        target: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Send message to external platform.
        
        Args:
            platform: Target platform
            message: Unified message format
            target: Optional target channel/user
            
        Returns:
            Send result
        """
        if platform not in self.adapters:
            return {
                "error": f"Platform not supported: {platform}",
                "supported_platforms": list(self.adapters.keys())
            }
        
        # Check rate limit
        if not self._check_rate_limit(platform):
            return {
                "error": "Rate limit exceeded",
                "platform": platform
            }
        
        try:
            adapter = self.adapters[platform]
            
            # Transform message to platform format
            platform_message = self._transform_message(message, platform)
            
            # Send via adapter
            result = await adapter.send(platform_message, target)
            
            # Update rate limit
            self._update_rate_limit(platform)
            
            logger.info(f"📤 Message sent to {platform}")
            return result
            
        except Exception as e:
            logger.error(f"❌ Failed to send message to {platform}: {e}")
            return {
                "error": str(e),
                "platform": platform
            }
    
    async def receive_message(
        self,
        platform: str,
        raw_message: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Receive and normalize message from platform.
        
        Args:
            platform: Source platform
            raw_message: Platform-specific message
            
        Returns:
            Normalized message
        """
        if platform not in self.adapters:
            return {
                "error": f"Platform not supported: {platform}"
            }
        
        try:
            adapter = self.adapters[platform]
            
            # Transform to unified format
            normalized = await adapter.normalize(raw_message)
            
            logger.info(f"📥 Message received from {platform}")
            return normalized
            
        except Exception as e:
            logger.error(f"❌ Failed to receive message from {platform}: {e}")
            return {
                "error": str(e),
                "platform": platform
            }
    
    def _transform_message(
        self,
        message: Dict[str, Any],
        platform: str
    ) -> Dict[str, Any]:
        """Transform unified message to platform format"""
        # TODO: Implement platform-specific transformations
        return message
    
    def _check_rate_limit(self, platform: str) -> bool:
        """Check if platform rate limit allows sending"""
        if platform not in self.rate_limits:
            return True
        
        limit = self.rate_limits[platform]
        now = datetime.now()
        
        # Reset window if expired
        window_elapsed = (now - limit["window_start"]).total_seconds()
        if window_elapsed > limit["window_seconds"]:
            limit["current_count"] = 0
            limit["window_start"] = now
        
        return limit["current_count"] < limit["max_messages"]
    
    def _update_rate_limit(self, platform: str):
        """Update rate limit counter"""
        if platform in self.rate_limits:
            self.rate_limits[platform]["current_count"] += 1
    
    def get_supported_platforms(self) -> List[str]:
        """Get list of supported platforms"""
        return list(self.adapters.keys())
    
    def get_platform_status(self, platform: str) -> Dict[str, Any]:
        """Get status of a platform adapter"""
        if platform not in self.adapters:
            return {
                "platform": platform,
                "status": "not_registered"
            }
        
        adapter = self.adapters[platform]
        rate_limit = self.rate_limits.get(platform, {})
        
        return {
            "platform": platform,
            "status": "active",
            "rate_limit": {
                "current": rate_limit.get("current_count", 0),
                "max": rate_limit.get("max_messages", 0),
                "window_seconds": rate_limit.get("window_seconds", 0)
            } if rate_limit else None
        }


# Singleton instance
_messaging_bridge: Optional[MessagingBridge] = None


def get_messaging_bridge() -> MessagingBridge:
    """Get or create messaging bridge singleton"""
    global _messaging_bridge
    if _messaging_bridge is None:
        _messaging_bridge = MessagingBridge()
    return _messaging_bridge
