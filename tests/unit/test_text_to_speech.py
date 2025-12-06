"""Unit tests for TextToSpeechService."""

import os
from unittest.mock import patch

import pytest

from voice.text_to_speech import TextToSpeechService, get_tts_service


class TestTextToSpeechService:
    @pytest.fixture
    def service(self):
        with patch.dict(os.environ, {"TTS_ENABLED": "true", "TTS_ENGINE": "openai"}):
            return TextToSpeechService()

    @pytest.fixture
    def disabled_service(self):
        with patch.dict(os.environ, {"TTS_ENABLED": "false"}):
            return TextToSpeechService()

    def test_initialization(self, service):
        assert service.tts_enabled is True
        assert service.tts_engine == "openai"
        assert service.default_voice == "alloy"
        assert service.output_format == "mp3"

    def test_initialization_disabled(self, disabled_service):
        assert disabled_service.tts_enabled is False

    @pytest.mark.asyncio
    async def test_generate_speech_disabled(self, disabled_service):
        result = await disabled_service.generate_speech("Test text")
        assert "error" in result
        assert "disabled" in result["error"].lower()

    @pytest.mark.asyncio
    async def test_generate_speech_empty_text(self, service):
        result = await service.generate_speech("")
        assert "error" in result
        assert "empty" in result["error"].lower()

    @pytest.mark.asyncio
    async def test_generate_speech_placeholder(self, service):
        result = await service.generate_speech("Hello world")
        assert result["text"] == "Hello world"
        assert result["status"] == "placeholder"
        assert result["voice"] == "alloy"
        assert result["format"] == "mp3"
        assert "duration" in result

    @pytest.mark.asyncio
    async def test_generate_speech_custom_voice(self, service):
        result = await service.generate_speech("Test", voice="nova")
        assert result["voice"] == "nova"

    @pytest.mark.asyncio
    async def test_generate_speech_custom_speed(self, service):
        result = await service.generate_speech("Test", speed=1.5)
        assert result["speed"] == 1.5

    @pytest.mark.asyncio
    async def test_stream_speech(self, service):
        chunks = []
        async for chunk in service.stream_speech("Test"):
            chunks.append(chunk)
        assert len(chunks) == 1
        assert chunks[0] == b""

    def test_get_available_voices(self, service):
        voices = service.get_available_voices()
        assert isinstance(voices, list)
        assert len(voices) > 0
        assert all("id" in v and "name" in v for v in voices)

    def test_get_service_info(self, service):
        info = service.get_service_info()
        assert info["service"] == "text_to_speech"
        assert info["enabled"] is True
        assert info["engine"] == "openai"
        assert "available_voices" in info

    def test_singleton(self):
        service1 = get_tts_service()
        service2 = get_tts_service()
        assert service1 is service2
