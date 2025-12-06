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
    assert hasattr(message_service, "active_connections")
    assert hasattr(message_service, "elyza_service")


def test_save_message(message_service, mock_repository):
    """Test saving a message"""
    message = Message(username="test_user", message="Test message", message_type=MessageType.USER)

    result = message_service.save_message(message)

    assert result is not None
    assert result.id == "msg_123"
    mock_repository.save_message.assert_called_once()


def test_save_message_validation_empty_username(message_service):
    """Test save message with empty username"""
    message = Message(username="", message="Test message")

    with pytest.raises(ValueError, match="Username cannot be empty"):
        message_service.save_message(message)


def test_save_message_validation_empty_message(message_service):
    """Test save message with empty content"""
    message = Message(username="user", message="")

    with pytest.raises(ValueError, match="Message cannot be empty"):
        message_service.save_message(message)


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


def test_websocket_registration(message_service):
    """Test WebSocket connection registration"""
    room_id = "room_123"
    mock_ws = Mock()

    message_service.register_websocket(room_id, mock_ws)

    assert room_id in message_service.active_connections
    assert mock_ws in message_service.active_connections[room_id]


def test_websocket_unregistration(message_service):
    """Test WebSocket connection unregistration"""
    room_id = "room_123"
    mock_ws = Mock()

    message_service.register_websocket(room_id, mock_ws)
    message_service.unregister_websocket(room_id, mock_ws)

    assert room_id not in message_service.active_connections


def test_get_room_connections(message_service):
    """Test getting room connections"""
    room_id = "room_123"
    mock_ws1 = Mock()
    mock_ws2 = Mock()

    message_service.register_websocket(room_id, mock_ws1)
    message_service.register_websocket(room_id, mock_ws2)

    connections = message_service.get_room_connections(room_id)

    assert len(connections) == 2
    assert mock_ws1 in connections
    assert mock_ws2 in connections


@pytest.mark.asyncio
async def test_broadcast_to_room(message_service):
    """Test broadcasting message to room"""
    room_id = "room_123"
    mock_ws = Mock()
    mock_ws.send_json = Mock(return_value=None)

    # Make send_json async
    async def async_send_json(data):
        return None

    mock_ws.send_json = async_send_json

    message_service.register_websocket(room_id, mock_ws)

    message_data = {"type": "message", "content": "Test"}
    await message_service.broadcast_to_room(room_id, message_data)

    # Verify connection is still registered (not disconnected)
    assert room_id in message_service.active_connections


def test_get_connection_stats(message_service):
    """Test getting connection statistics"""
    room1 = "room_1"
    room2 = "room_2"

    message_service.register_websocket(room1, Mock())
    message_service.register_websocket(room1, Mock())
    message_service.register_websocket(room2, Mock())

    stats = message_service.get_connection_stats()

    assert stats["total_rooms"] == 2
    assert stats["total_connections"] == 3
    assert room1 in stats["rooms"]
    assert stats["rooms"][room1] == 2


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
    assert str(error) == "AI service down"
