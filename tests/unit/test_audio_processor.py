"""Unit tests for AudioProcessor."""

import os
import tempfile

import pytest

from voice.audio_processor import AudioProcessor, get_audio_processor


class TestAudioProcessor:
    @pytest.fixture
    def processor(self):
        return AudioProcessor()

    @pytest.fixture
    def temp_audio_file(self):
        """Create a temporary audio file for testing."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".mp3", delete=False) as f:
            f.write("dummy audio content")
            temp_path = f.name
        yield temp_path
        # Cleanup
        if os.path.exists(temp_path):
            os.unlink(temp_path)

    def test_initialization(self, processor):
        assert processor.upload_dir.exists()
        assert len(processor.supported_formats) > 0
        assert processor.max_file_size > 0

    @pytest.mark.asyncio
    async def test_process_upload_file_not_found(self, processor):
        result = await processor.process_upload("nonexistent.mp3")
        assert "error" in result
        assert "not found" in result["error"].lower()

    @pytest.mark.asyncio
    async def test_process_upload_placeholder(self, processor, temp_audio_file):
        result = await processor.process_upload(temp_audio_file)
        assert result["original_file"] == temp_audio_file
        assert result["status"] == "placeholder"
        assert "file_size" in result
        assert "duration" in result

    @pytest.mark.asyncio
    async def test_process_upload_with_target_format(self, processor, temp_audio_file):
        result = await processor.process_upload(temp_audio_file, target_format="wav")
        assert result["status"] == "placeholder"

    @pytest.mark.asyncio
    async def test_convert_format_unsupported(self, processor, temp_audio_file):
        result = await processor.convert_format(temp_audio_file, "xyz")
        assert "error" in result
        assert "Unsupported format" in result["error"]

    @pytest.mark.asyncio
    async def test_convert_format_placeholder(self, processor, temp_audio_file):
        result = await processor.convert_format(temp_audio_file, "wav")
        assert result["output_format"] == "wav"
        assert result["status"] == "placeholder"

    @pytest.mark.asyncio
    async def test_analyze_audio(self, processor, temp_audio_file):
        result = await processor.analyze_audio(temp_audio_file)
        assert result["file_path"] == temp_audio_file
        assert "duration" in result
        assert "sample_rate" in result

    def test_is_supported_format(self, processor):
        assert processor.is_supported_format("test.mp3")
        assert processor.is_supported_format("test.wav")
        assert not processor.is_supported_format("test.xyz")

    def test_get_service_info(self, processor):
        info = processor.get_service_info()
        assert info["service"] == "audio_processor"
        assert "supported_formats" in info
        assert "max_file_size_mb" in info

    def test_singleton(self):
        processor1 = get_audio_processor()
        processor2 = get_audio_processor()
        assert processor1 is processor2
