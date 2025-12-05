"""Unit tests for MessagingBridge."""

from unittest.mock import AsyncMock, Mock

import pytest

from integration.messaging_bridge import MessagingBridge, get_messaging_bridge


class TestMessagingBridge:
    @pytest.fixture
    def bridge(self):
        return MessagingBridge()

    @pytest.fixture
    def mock_adapter(self):
        adapter = Mock()
        adapter.send = AsyncMock(
            return_value={"status": "success", "message_id": "mock_id"}
        )
        adapter.normalize = AsyncMock(
            return_value={
                "platform": "test_platform",
                "text": "Test message",
                "user_id": "U123",
            }
        )
        return adapter

    def test_initialization(self, bridge):
        assert len(bridge.adapters) == 0
        assert len(bridge.message_queue) == 0
        assert len(bridge.rate_limits) == 0

    def test_register_adapter(self, bridge, mock_adapter):
        bridge.register_adapter("test_platform", mock_adapter)

        assert "test_platform" in bridge.adapters
        assert bridge.adapters["test_platform"] == mock_adapter

    def test_register_adapter_with_rate_limit(self, bridge, mock_adapter):
        rate_limit = {"max_messages": 50, "window_seconds": 60}
        bridge.register_adapter("test_platform", mock_adapter, rate_limit)

        assert "test_platform" in bridge.rate_limits
        assert bridge.rate_limits["test_platform"]["max_messages"] == 50

    @pytest.mark.asyncio
    async def test_send_message_success(self, bridge, mock_adapter):
        bridge.register_adapter("test_platform", mock_adapter)

        message = {"text": "Hello world"}
        result = await bridge.send_message("test_platform", message)

        assert result["status"] == "success"
        mock_adapter.send.assert_called_once()

    @pytest.mark.asyncio
    async def test_send_message_platform_not_supported(self, bridge):
        result = await bridge.send_message("unknown_platform", {"text": "Test"})

        assert "error" in result
        assert "not supported" in result["error"].lower()

    @pytest.mark.asyncio
    async def test_send_message_with_target(self, bridge, mock_adapter):
        bridge.register_adapter("test_platform", mock_adapter)

        message = {"text": "Hello"}
        result = await bridge.send_message("test_platform", message, target="channel_123")

        mock_adapter.send.assert_called_once()

    @pytest.mark.asyncio
    async def test_receive_message(self, bridge, mock_adapter):
        bridge.register_adapter("test_platform", mock_adapter)

        raw_message = {"type": "message", "text": "Test message"}
        result = await bridge.receive_message("test_platform", raw_message)

        assert result["platform"] == "test_platform"
        assert result["text"] == "Test message"
        mock_adapter.normalize.assert_called_once()

    @pytest.mark.asyncio
    async def test_receive_message_platform_not_supported(self, bridge):
        result = await bridge.receive_message("unknown_platform", {})

        assert "error" in result
        assert "not supported" in result["error"].lower()

    def test_get_supported_platforms(self, bridge, mock_adapter):
        bridge.register_adapter("slack", mock_adapter)
        bridge.register_adapter("teams", mock_adapter)

        platforms = bridge.get_supported_platforms()
        assert len(platforms) == 2
        assert "slack" in platforms
        assert "teams" in platforms

    def test_get_platform_status_not_registered(self, bridge):
        status = bridge.get_platform_status("unknown")
        assert status["status"] == "not_registered"

    def test_get_platform_status_active(self, bridge, mock_adapter):
        bridge.register_adapter("test_platform", mock_adapter)

        status = bridge.get_platform_status("test_platform")
        assert status["platform"] == "test_platform"
        assert status["status"] == "active"

    def test_get_platform_status_with_rate_limit(self, bridge, mock_adapter):
        rate_limit = {"max_messages": 100, "window_seconds": 60}
        bridge.register_adapter("test_platform", mock_adapter, rate_limit)

        status = bridge.get_platform_status("test_platform")
        assert status["rate_limit"] is not None
        assert status["rate_limit"]["max"] == 100

    @pytest.mark.asyncio
    async def test_rate_limiting(self, bridge, mock_adapter):
        rate_limit = {"max_messages": 2, "window_seconds": 60}
        bridge.register_adapter("test_platform", mock_adapter, rate_limit)

        # First two messages should succeed
        await bridge.send_message("test_platform", {"text": "Message 1"})
        await bridge.send_message("test_platform", {"text": "Message 2"})

        # Third message should be rate limited
        result = await bridge.send_message("test_platform", {"text": "Message 3"})
        assert "error" in result
        assert "Rate limit" in result["error"]

    def test_singleton(self):
        bridge1 = get_messaging_bridge()
        bridge2 = get_messaging_bridge()
        assert bridge1 is bridge2

    def test_transform_to_slack(self, bridge):
        """Test Slack message transformation"""
        unified_message = {
            "text": "Hello @user1",
            "channel": "C123456",
            "thread_id": "1234567890.123456",
            "mentions": ["user1"],
            "attachments": [
                {"title": "Test", "text": "Attachment text", "image_url": "http://example.com/image.png"}
            ],
        }

        result = bridge._transform_to_slack(unified_message)

        assert result["text"] == "Hello <@user1>"
        assert result["channel"] == "C123456"
        assert result["thread_ts"] == "1234567890.123456"
        assert len(result["attachments"]) == 1
        assert result["attachments"][0]["title"] == "Test"

    def test_transform_to_discord(self, bridge):
        """Test Discord message transformation"""
        unified_message = {
            "text": "Hello @user1",
            "mentions": ["user1"],
            "attachments": [{"title": "Test", "text": "Description", "image_url": "http://example.com/image.png"}],
        }

        result = bridge._transform_to_discord(unified_message)

        assert result["content"] == "Hello <@user1>"
        assert "embeds" in result
        assert len(result["embeds"]) == 1
        assert result["embeds"][0]["title"] == "Test"

    def test_transform_to_teams(self, bridge):
        """Test Microsoft Teams message transformation"""
        unified_message = {
            "text": "Hello world",
            "mentions": ["user1", "user2"],
            "attachments": [{"text": "Card content"}],
        }

        result = bridge._transform_to_teams(unified_message)

        assert result["body"]["content"] == "Hello world"
        assert result["body"]["contentType"] == "html"
        assert "attachments" in result
        assert "mentions" in result
        assert len(result["mentions"]) == 2

    def test_transform_to_telegram(self, bridge):
        """Test Telegram message transformation"""
        unified_message = {
            "text": "Hello world",
            "channel": "123456789",
            "format": "Markdown",
            "thread_id": "999",
        }

        result = bridge._transform_to_telegram(unified_message)

        assert result["text"] == "Hello world"
        assert result["chat_id"] == "123456789"
        assert result["parse_mode"] == "Markdown"
        assert result["reply_to_message_id"] == "999"

    def test_transform_unknown_platform(self, bridge):
        """Test transformation for unknown platform"""
        unified_message = {"text": "Hello world"}

        result = bridge._transform_message(unified_message, "unknown_platform")

        # Should return message as-is
        assert result == unified_message
