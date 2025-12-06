"""
🌉 Messaging Bridge

API Gateway for external platform integration with pluggable adapters.
"""

from datetime import datetime
from typing import Any, Dict, List, Optional

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
        self, platform: str, adapter: Any, rate_limit: Optional[Dict[str, int]] = None
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
                "window_start": datetime.now(),
            }

        logger.info(f"🔌 Adapter registered: {platform}")

    async def send_message(
        self, platform: str, message: Dict[str, Any], target: Optional[str] = None
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
                "supported_platforms": list(self.adapters.keys()),
            }

        # Check rate limit
        if not self._check_rate_limit(platform):
            return {"error": "Rate limit exceeded", "platform": platform}

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
            return {"error": str(e), "platform": platform}

    async def receive_message(self, platform: str, raw_message: Dict[str, Any]) -> Dict[str, Any]:
        """
        Receive and normalize message from platform.

        Args:
            platform: Source platform
            raw_message: Platform-specific message

        Returns:
            Normalized message
        """
        if platform not in self.adapters:
            return {"error": f"Platform not supported: {platform}"}

        try:
            adapter = self.adapters[platform]

            # Transform to unified format
            normalized = await adapter.normalize(raw_message)

            logger.info(f"📥 Message received from {platform}")
            return normalized

        except Exception as e:
            logger.error(f"❌ Failed to receive message from {platform}: {e}")
            return {"error": str(e), "platform": platform}

    def _transform_message(self, message: Dict[str, Any], platform: str) -> Dict[str, Any]:
        """
        Transform unified message to platform-specific format.

        Args:
            message: Unified message format with fields like 'text', 'user', 'attachments'
            platform: Target platform (slack, discord, teams, etc.)

        Returns:
            Platform-specific message format
        """
        if platform == "slack":
            return self._transform_to_slack(message)
        elif platform == "discord":
            return self._transform_to_discord(message)
        elif platform == "teams":
            return self._transform_to_teams(message)
        elif platform == "telegram":
            return self._transform_to_telegram(message)
        else:
            # Return message as-is for unknown platforms with warning
            logger.warning(
                f"No transformation defined for platform: {platform}. "
                f"Returning message in unified format. "
                f"Configure platform-specific transformation for proper delivery."
            )
            return message

    def _transform_to_slack(self, message: Dict[str, Any]) -> Dict[str, Any]:
        """Transform message to Slack format"""
        slack_message = {"text": message.get("text", "")}

        # Add channel if specified
        if "channel" in message:
            slack_message["channel"] = message["channel"]

        # Add thread_ts for threading
        if "thread_id" in message:
            slack_message["thread_ts"] = message["thread_id"]

        # Transform attachments to Slack blocks format
        if "attachments" in message:
            slack_message["attachments"] = [
                {
                    "text": att.get("text", ""),
                    "title": att.get("title", ""),
                    "image_url": att.get("image_url", ""),
                }
                for att in message["attachments"]
            ]

        # Add mentions
        if "mentions" in message:
            for user_id in message["mentions"]:
                slack_message["text"] = slack_message["text"].replace(
                    f"@{user_id}", f"<@{user_id}>"
                )

        return slack_message

    def _transform_to_discord(self, message: Dict[str, Any]) -> Dict[str, Any]:
        """Transform message to Discord format"""
        discord_message = {"content": message.get("text", "")}

        # Add embed for rich content
        if "attachments" in message and message["attachments"]:
            discord_message["embeds"] = [
                {
                    "title": att.get("title", ""),
                    "description": att.get("text", ""),
                    "image": {"url": att.get("image_url", "")},
                }
                for att in message["attachments"]
            ]

        # Add mentions (Discord uses <@user_id> format)
        if "mentions" in message:
            for user_id in message["mentions"]:
                discord_message["content"] = discord_message["content"].replace(
                    f"@{user_id}", f"<@{user_id}>"
                )

        return discord_message

    def _transform_to_teams(self, message: Dict[str, Any]) -> Dict[str, Any]:
        """Transform message to Microsoft Teams format"""
        teams_message = {"body": {"contentType": "html", "content": message.get("text", "")}}

        # Add attachments
        if "attachments" in message:
            teams_message["attachments"] = [
                {
                    "contentType": "application/vnd.microsoft.card.adaptive",
                    "content": {
                        "type": "AdaptiveCard",
                        "body": [{"type": "TextBlock", "text": att.get("text", "")}],
                    },
                }
                for att in message["attachments"]
            ]

        # Add mentions (Teams uses <at>name</at> format)
        if "mentions" in message:
            teams_message["mentions"] = [
                {"id": idx, "mentionText": f"@{user_id}", "mentioned": {"user": {"id": user_id}}}
                for idx, user_id in enumerate(message["mentions"])
            ]

        return teams_message

    def _transform_to_telegram(self, message: Dict[str, Any]) -> Dict[str, Any]:
        """Transform message to Telegram format"""
        telegram_message = {"text": message.get("text", "")}

        # Add chat_id if specified
        if "channel" in message:
            telegram_message["chat_id"] = message["channel"]

        # Telegram uses parse_mode for formatting
        if "format" in message:
            telegram_message["parse_mode"] = message["format"]  # HTML or Markdown

        # Add reply_to for threading
        if "thread_id" in message:
            telegram_message["reply_to_message_id"] = message["thread_id"]

        return telegram_message

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
            return {"platform": platform, "status": "not_registered"}

        # Future enhancement: Add adapter health checks
        # adapter = self.adapters[platform]
        # adapter_status = adapter.get_status() if hasattr(adapter, 'get_status') else 'active'

        rate_limit = self.rate_limits.get(platform, {})

        return {
            "platform": platform,
            "status": "active",
            "rate_limit": (
                {
                    "current": rate_limit.get("current_count", 0),
                    "max": rate_limit.get("max_messages", 0),
                    "window_seconds": rate_limit.get("window_seconds", 0),
                }
                if rate_limit
                else None
            ),
        }


# Singleton instance
_messaging_bridge: Optional[MessagingBridge] = None


def get_messaging_bridge() -> MessagingBridge:
    """Get or create messaging bridge singleton"""
    global _messaging_bridge
    if _messaging_bridge is None:
        _messaging_bridge = MessagingBridge()
    return _messaging_bridge
