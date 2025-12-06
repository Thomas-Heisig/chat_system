"""Unit tests for SlackAdapter."""

import pytest

from integration.adapters.slack_adapter import SlackAdapter


class TestSlackAdapter:
    @pytest.fixture
    def adapter_with_token(self):
        config = {
            "token": "xoxb-test-token",
            "signing_secret": "test-secret",
            "app_id": "test-app-id",
        }
        return SlackAdapter(config)

    @pytest.fixture
    def adapter_without_token(self):
        return SlackAdapter({"token": None})

    def test_initialization_with_token(self, adapter_with_token):
        assert adapter_with_token.config["token"] == "xoxb-test-token"
        assert adapter_with_token.authenticated is False

    def test_initialization_without_token(self, adapter_without_token):
        assert adapter_without_token.config.get("token") is None

    @pytest.mark.asyncio
    async def test_send_message_placeholder(self, adapter_with_token):
        message = {"text": "Test message", "channel": "C123456"}
        result = await adapter_with_token.send(message)

        # When slack_sdk is not installed, status should be "placeholder"
        assert result["status"] in ["success", "placeholder"]
        assert result["platform"] == "slack"
        assert "message_id" in result

    @pytest.mark.asyncio
    async def test_send_message_with_target(self, adapter_with_token):
        message = {"text": "Test message"}
        result = await adapter_with_token.send(message, target="C123456")

        # When slack_sdk is not installed, status should be "placeholder"
        assert result["status"] in ["success", "placeholder"]
        assert result["target"] == "C123456"

    @pytest.mark.asyncio
    async def test_normalize_message(self, adapter_with_token):
        raw_message = {
            "ts": "1234567890.123456",
            "user": "U123456",
            "channel": "C123456",
            "text": "Hello world",
            "type": "message",
            "thread_ts": "1234567890.123450",
            "attachments": [{"text": "attachment"}],
        }

        normalized = await adapter_with_token.normalize(raw_message)

        assert normalized["platform"] == "slack"
        assert normalized["message_id"] == "1234567890.123456"
        assert normalized["user_id"] == "U123456"
        assert normalized["channel_id"] == "C123456"
        assert normalized["text"] == "Hello world"
        assert normalized["thread_ts"] == "1234567890.123450"
        assert len(normalized["attachments"]) == 1

    @pytest.mark.asyncio
    async def test_authenticate_with_token(self, adapter_with_token):
        result = await adapter_with_token.authenticate()
        assert result is True
        assert adapter_with_token.authenticated is True

    @pytest.mark.asyncio
    async def test_authenticate_without_token(self, adapter_without_token):
        result = await adapter_without_token.authenticate()
        assert result is False

    @pytest.mark.asyncio
    async def test_get_status_authenticated(self, adapter_with_token):
        await adapter_with_token.authenticate()
        status = await adapter_with_token.get_status()

        assert status["platform"] == "slack"
        assert status["authenticated"] is True
        assert status["token_configured"] is True
        assert status["status"] == "ready"

    @pytest.mark.asyncio
    async def test_get_status_not_authenticated(self, adapter_with_token):
        status = await adapter_with_token.get_status()

        assert status["authenticated"] is False
        assert status["status"] == "not_configured"
