"""Unit tests for MessageService with AI fallback."""

from unittest.mock import Mock, patch

import pytest

from services.exceptions import ExternalAIUnavailableError
from services.message_service import MessageService


class TestMessageService:
    @pytest.fixture
    def mock_repo(self):
        return Mock()

    @pytest.fixture
    def service(self, mock_repo):
        return MessageService(mock_repo)

    def test_initialization(self, service):
        assert service is not None
        assert service.repository is not None

    @patch("services.message_service.requests.post")
    def test_ai_unavailable_raises_exception(self, mock_post, service):
        mock_post.side_effect = Exception("Connection refused")

        with pytest.raises(ExternalAIUnavailableError):
            service._generate_with_ollama("Test message", "", "llama2")

    @patch("services.message_service.requests.post")
    @patch("services.message_service.get_elyza_service")
    def test_fallback_to_elyza(self, mock_elyza, mock_post, service):
        # Simulate Ollama failure
        mock_post.side_effect = Exception("Connection failed")

        # Mock Elyza service
        mock_elyza_instance = Mock()
        mock_elyza_instance.is_enabled.return_value = True
        mock_elyza_instance.generate_response.return_value = "Fallback response"
        mock_elyza.return_value = mock_elyza_instance

        # This should use fallback
        response = service.generate_ai_response("Test message")

        assert response is not None
        assert isinstance(response, str)
