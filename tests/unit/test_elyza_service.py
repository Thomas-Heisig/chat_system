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

    @pytest.mark.asyncio
    async def test_greeting_response(self, service):
        result = await service.generate_response("Hallo")
        assert isinstance(result, dict)
        assert "response" in result
        assert len(result["response"]) > 0

    @pytest.mark.asyncio
    async def test_default_response(self, service):
        result = await service.generate_response("Random text xyz123")
        assert isinstance(result, dict)
        assert "response" in result
        assert len(result["response"]) > 0

    @pytest.mark.asyncio
    async def test_context_management(self, service):
        user_id = "test_user"
        assert len(service.get_context(user_id)) == 0
        await service.generate_response("First message", user_id=user_id)
        assert len(service.get_context(user_id)) == 1
        service.clear_context(user_id)
        assert len(service.get_context(user_id)) == 0
