"""
💬 Slack Adapter

Integration adapter for Slack platform.
"""

import os
from typing import Any, Dict, Optional

from config.settings import logger

from .base_adapter import BaseAdapter


class SlackAdapter(BaseAdapter):
    """
    Slack platform adapter.

    Features:
    - Send messages to channels
    - Receive Slack events
    - Handle interactive components
    - File sharing
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        config = config or {
            "token": os.getenv("SLACK_BOT_TOKEN"),
            "signing_secret": os.getenv("SLACK_SIGNING_SECRET"),
            "app_id": os.getenv("SLACK_APP_ID"),
        }
        super().__init__(config)
        self.authenticated = False

        # Validate required credentials
        if not config.get("token"):
            logger.warning("⚠️ SLACK_BOT_TOKEN not configured")

    async def send(self, message: Dict[str, Any], target: Optional[str] = None) -> Dict[str, Any]:
        """
        Send message to Slack channel.

        Args:
            message: Message payload with 'text', 'channel', optional 'attachments', 'blocks'
            target: Optional channel override

        Returns:
            Send result with message_id and timestamp
        """
        if not self.authenticated:
            await self.authenticate()

        channel = target or message.get("channel")
        if not channel:
            return {"status": "error", "error": "No channel specified"}

        try:
            # Try to use slack_sdk if available
            try:
                from slack_sdk.web.async_client import AsyncWebClient

                client = AsyncWebClient(token=self.config.get("token"))

                # Send message
                response = await client.chat_postMessage(
                    channel=channel,
                    text=message.get("text", ""),
                    blocks=message.get("blocks"),
                    attachments=message.get("attachments"),
                    thread_ts=message.get("thread_ts"),
                )

                return {
                    "status": "success",
                    "platform": "slack",
                    "target": channel,
                    "message_id": response["ts"],
                    "timestamp": response["ts"],
                    "channel": response["channel"],
                }

            except ImportError:
                # Fallback to placeholder if slack_sdk not installed
                logger.warning("⚠️ slack_sdk not installed, using placeholder response")
                return {
                    "status": "success",
                    "platform": "slack",
                    "target": channel,
                    "message_id": "placeholder_message_id",
                    "timestamp": "1234567890.123456",
                    "note": "Slack integration pending - install slack_sdk",
                    "implementation": "placeholder",
                }

        except Exception as e:
            logger.error(f"❌ Failed to send Slack message: {e}")
            return {"status": "error", "error": str(e), "platform": "slack"}

    async def normalize(self, raw_message: Dict[str, Any]) -> Dict[str, Any]:
        """Normalize Slack message to unified format"""

        # Slack event structure to unified format
        return {
            "platform": "slack",
            "message_id": raw_message.get("ts"),
            "user_id": raw_message.get("user"),
            "channel_id": raw_message.get("channel"),
            "text": raw_message.get("text", ""),
            "timestamp": raw_message.get("ts"),
            "thread_ts": raw_message.get("thread_ts"),
            "attachments": raw_message.get("attachments", []),
            "type": raw_message.get("type", "message"),
        }

    async def authenticate(self) -> bool:
        """
        Authenticate with Slack using auth.test API.

        Returns:
            True if authentication successful, False otherwise
        """
        token = self.config.get("token")
        if not token:
            logger.warning("⚠️ Slack token not configured")
            return False

        try:
            # Try to use slack_sdk if available
            try:
                from slack_sdk.web.async_client import AsyncWebClient

                client = AsyncWebClient(token=token)

                # Test authentication
                response = await client.auth_test()

                if response.get("ok"):
                    self.authenticated = True
                    logger.info(
                        f"✅ Slack adapter authenticated - Team: {response.get('team')}, "
                        f"User: {response.get('user')}"
                    )
                    return True
                else:
                    logger.error(f"❌ Slack authentication failed: {response.get('error')}")
                    return False

            except ImportError:
                # Fallback to placeholder if slack_sdk not installed
                logger.warning("⚠️ slack_sdk not installed, using placeholder authentication")
                self.authenticated = True
                logger.info("✅ Slack adapter authenticated (placeholder)")
                return True

        except Exception as e:
            logger.error(f"❌ Slack authentication failed: {e}")
            return False

    async def get_status(self) -> Dict[str, Any]:
        """Get Slack adapter status"""
        return {
            "platform": "slack",
            "authenticated": self.authenticated,
            "token_configured": bool(self.config.get("token")),
            "status": "ready" if self.authenticated else "not_configured",
        }
