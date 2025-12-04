"""Unit tests for ElyzaService."""

import os
from unittest.mock import patch

import pytest

from services.elyza_service import ElyzaService


class TestElyzaService:
    @pytest.fixture
    def service(self):
        with patch.dict(os.environ, {"ENABLE_ELYZA_FALLBACK": "true"}):
            return ElyzaService()

    def test_initialization(self, service):
        assert service.enabled is True
        assert len(service.patterns) > 0

    def test_greeting_response(self, service):
        response = service.generate_response("Hallo")
        assert isinstance(response, str)
        assert len(response) > 0

    def test_default_response(self, service):
        response = service.generate_response("Random text xyz123")
        assert isinstance(response, str)
        assert len(response) > 0

    def test_context_management(self, service):
        assert len(service.get_context()) == 0
        service.generate_response("First message")
        assert len(service.get_context()) == 1
        service.clear_context()
        assert len(service.get_context()) == 0
