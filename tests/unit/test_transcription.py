"""Unit tests for TranscriptionService."""

import os
import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest

from voice.transcription import TranscriptionService, get_transcription_service


class TestTranscriptionService:
    @pytest.fixture
    def service(self):
        with patch.dict(os.environ, {"WHISPER_ENABLED": "true", "WHISPER_MODEL": "base"}):
            return TranscriptionService()

    @pytest.fixture
    def disabled_service(self):
        with patch.dict(os.environ, {"WHISPER_ENABLED": "false"}):
            return TranscriptionService()

    @pytest.fixture
    def temp_audio_file(self):
        """Create a temporary audio file for testing."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".wav", delete=False) as f:
            f.write("dummy audio content")
            temp_path = f.name
        yield temp_path
        # Cleanup
        if os.path.exists(temp_path):
            os.unlink(temp_path)

    def test_initialization(self, service):
        assert service.whisper_enabled is True
        assert service.whisper_model == "base"
        assert service.use_local_model is True

    def test_initialization_disabled(self, disabled_service):
        assert disabled_service.whisper_enabled is False

    @pytest.mark.asyncio
    async def test_transcribe_audio_file_not_found(self, service):
        result = await service.transcribe_audio("nonexistent.wav")
        assert "error" in result
        assert "not found" in result["error"].lower()

    @pytest.mark.asyncio
    async def test_transcribe_audio_disabled(self, disabled_service, temp_audio_file):
        result = await disabled_service.transcribe_audio(temp_audio_file)
        assert "error" in result
        assert "disabled" in result["error"].lower()

    @pytest.mark.asyncio
    async def test_transcribe_audio_placeholder(self, service, temp_audio_file):
        result = await service.transcribe_audio(temp_audio_file)
        assert "text" in result
        assert result["status"] == "placeholder"
        assert result["model"] == "base"
        assert result["file_path"] == temp_audio_file

    @pytest.mark.asyncio
    async def test_transcribe_audio_with_language(self, service, temp_audio_file):
        result = await service.transcribe_audio(temp_audio_file, language="de")
        assert result["language"] == "de"

    @pytest.mark.asyncio
    async def test_transcribe_audio_with_timestamps(self, service, temp_audio_file):
        result = await service.transcribe_audio(temp_audio_file, include_timestamps=True)
        assert result["timestamps"] is not None
        assert isinstance(result["timestamps"], list)

    @pytest.mark.asyncio
    async def test_transcribe_stream(self, service):
        result = await service.transcribe_stream(b"audio data", "session_123")
        assert result["session_id"] == "session_123"
        assert result["is_final"] is False
        assert result["status"] == "streaming"

    def test_get_supported_languages(self, service):
        languages = service.get_supported_languages()
        assert isinstance(languages, list)
        assert len(languages) > 0
        assert all("code" in lang and "name" in lang for lang in languages)

    def test_get_service_info(self, service):
        info = service.get_service_info()
        assert info["service"] == "transcription"
        assert info["enabled"] is True
        assert info["model"] == "base"
        assert "supported_languages" in info

    def test_singleton(self):
        service1 = get_transcription_service()
        service2 = get_transcription_service()
        assert service1 is service2
