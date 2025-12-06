"""
Tests for Message Service
"""

from unittest.mock import Mock

import pytest

from database.models import Message, MessageType
from services.exceptions import ExternalAIUnavailableError
from services.message_service import MessageService


@pytest.fixture
def mock_repository():
    """Create mock repository"""
    repo = Mock()
    repo.save_message = Mock(return_value="msg_123")
    repo.get_recent_messages = Mock(return_value=[])
    repo.get_all_messages = Mock(return_value=[])
    return repo


@pytest.fixture
def message_service(mock_repository):
    """Get message service with mock repository"""
    return MessageService(mock_repository)


def test_message_service_initialization(message_service):
    """Test message service initializes correctly"""
    assert message_service is not None
    assert message_service.repository is not None
    assert hasattr(message_service, "ollama_base_url")
    assert hasattr(message_service, "ollama_available")


def test_save_message(message_service, mock_repository):
    """Test saving a message"""
    message = Message(username="test_user", message="Test message", message_type=MessageType.USER)

    result = message_service.save_message(message)

    assert result is not None
    assert result.id == "msg_123"
    mock_repository.save_message.assert_called_once()


def test_save_message_validation_empty_username(message_service):
    """Test save message with empty username - Pydantic validates at model level"""
    from pydantic_core import ValidationError

    with pytest.raises(ValidationError):
        Message(username="", message="Test message")


def test_save_message_validation_empty_message(message_service):
    """Test save message with empty content - Pydantic validates at model level"""
    from pydantic_core import ValidationError

    with pytest.raises(ValidationError):
        Message(username="user", message="")


def test_get_recent_messages(message_service, mock_repository):
    """Test getting recent messages"""
    messages = message_service.get_recent_messages(limit=10)

    assert messages is not None
    mock_repository.get_recent_messages.assert_called_once_with(10)


def test_get_recent_messages_limit_validation(message_service, mock_repository):
    """Test limit validation for recent messages"""
    # Test negative limit
    messages = message_service.get_recent_messages(limit=-5)
    assert messages is not None

    # Test very high limit
    messages = message_service.get_recent_messages(limit=2000)
    assert messages is not None


# Note: WebSocket management tests moved to test_websocket_manager.py
# as these are now handled by the ConnectionManager, not MessageService


def test_health_check(message_service):
    """Test health check"""
    health = message_service.health_check()

    assert health is not None
    assert "status" in health
    assert "service" in health
    assert health["service"] == "message_service"


def test_get_ai_status(message_service):
    """Test getting AI status"""
    status = message_service.get_ai_status()

    assert status is not None
    assert "ai_enabled" in status
    assert "ollama_available" in status
    assert "custom_model_available" in status
    assert "available_models" in status


def test_external_ai_unavailable_error():
    """Test ExternalAIUnavailableError exception"""
    error = ExternalAIUnavailableError("AI service down")

    assert isinstance(error, Exception)
    assert "AI service down" in str(error)  # Error message includes the reason
