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
