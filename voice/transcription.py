"""
🎤 Transcription Service

Handles speech-to-text conversion using Whisper or other STT engines with fallback.
"""

import os
from pathlib import Path
from typing import Any, Dict, Optional

from config.settings import logger, voice_config


class TranscriptionService:
    """
    Speech-to-text transcription service with graceful degradation.

    Supports:
    - OpenAI Whisper API (cloud)
    - Local Whisper model (openai-whisper)
    - Multiple language support
    - Timestamp extraction
    - Automatic fallback when dependencies unavailable
    """

    def __init__(self):
        # Use centralized configuration
        self.whisper_enabled = voice_config.whisper_enabled
        self.whisper_model = voice_config.whisper_model
        self.whisper_api_key = voice_config.whisper_api_key
        self.use_local_model = voice_config.whisper_local
        self.default_language = voice_config.whisper_language

        # Check engine availability
        self.engine_available = self._check_engine_availability()

        logger.info(
            f"🎤 Transcription Service initialized "
            f"(Enabled: {self.whisper_enabled}, Local: {self.use_local_model}, "
            f"Available: {self.engine_available})"
        )
        
        if self.whisper_enabled and not self.engine_available:
            logger.warning(
                "⚠️ Whisper is enabled but dependencies are not available. "
                "Falling back to placeholder mode."
            )

    def _check_engine_availability(self) -> bool:
        """Check if Whisper engine is available"""
        if not self.whisper_enabled:
            return False
            
        try:
            if self.use_local_model:
                # Check for local whisper installation
                import whisper  # noqa: F401
                return True
            else:
                # Check for OpenAI API
                import openai  # noqa: F401
                return bool(self.whisper_api_key)
        except ImportError as e:
            logger.debug(f"Whisper not available: {e}")
            return False

    async def transcribe_audio(
        self, audio_file_path: str, language: Optional[str] = None, include_timestamps: bool = False
    ) -> Dict[str, Any]:
        """
        Transcribe audio file to text with automatic fallback.

        Args:
            audio_file_path: Path to audio file
            language: Optional language code (e.g., 'de', 'en', or 'auto')
            include_timestamps: Include word-level timestamps

        Returns:
            Transcription result with text and metadata
        """
        # Validate input
        if not os.path.exists(audio_file_path):
            return {
                "success": False,
                "error": "Audio file not found",
                "file_path": audio_file_path,
                "fallback": True,
            }

        # Use default language if not provided
        language = language or self.default_language

        # Check if service is enabled
        if not self.whisper_enabled:
            return self._fallback_response(
                audio_file_path, language, include_timestamps,
                "Transcription service is disabled. "
                "Set WHISPER_ENABLED=true in .env to enable."
            )

        # Check if engine is available
        if not self.engine_available:
            return self._fallback_response(
                audio_file_path, language, include_timestamps,
                "Whisper dependencies not available. "
                "Install 'openai-whisper' for local or 'openai' for API."
            )

        try:
            # Attempt actual transcription
            if self.use_local_model:
                return await self._transcribe_local(audio_file_path, language, include_timestamps)
            else:
                return await self._transcribe_api(audio_file_path, language, include_timestamps)

        except Exception as e:
            logger.error(f"❌ Transcription failed: {e}")
            return self._fallback_response(
                audio_file_path, language, include_timestamps,
                f"Transcription failed: {str(e)}"
            )

    def _fallback_response(
        self,
        audio_file_path: str,
        language: str,
        include_timestamps: bool,
        reason: str
    ) -> Dict[str, Any]:
        """Generate fallback response when transcription is unavailable"""
        return {
            "success": False,
            "fallback": True,
            "text": "[Transcription unavailable - placeholder text]",
            "language": language,
            "duration": 0.0,
            "confidence": 0.0,
            "file_path": audio_file_path,
            "model": self.whisper_model,
            "timestamps": [] if include_timestamps else None,
            "status": "fallback",
            "message": "Transcription service returned placeholder response",
            "reason": reason,
            "suggestion": "Install Whisper or configure WHISPER_API_KEY in .env",
        }

    async def _transcribe_local(
        self, audio_file_path: str, language: str, include_timestamps: bool
    ) -> Dict[str, Any]:
        """Transcribe using local Whisper model"""
        try:
            import whisper
            
            # Load model (cached after first load)
            model = whisper.load_model(self.whisper_model)
            
            # Transcribe
            result = model.transcribe(
                audio_file_path,
                language=None if language == "auto" else language,
                word_timestamps=include_timestamps
            )
            
            logger.info(f"🎤 Audio transcribed locally: {Path(audio_file_path).name}")
            
            return {
                "success": True,
                "fallback": False,
                "text": result["text"].strip(),
                "language": result.get("language", language),
                "duration": 0.0,  # TODO: Extract from audio file
                "confidence": 0.0,  # Whisper doesn't provide word confidence
                "file_path": audio_file_path,
                "model": self.whisper_model,
                "timestamps": result.get("segments", []) if include_timestamps else None,
                "status": "success",
                "engine": "whisper-local",
            }
            
        except Exception as e:
            logger.error(f"Local Whisper transcription failed: {e}")
            return self._fallback_response(audio_file_path, language, include_timestamps, str(e))

    async def _transcribe_api(
        self, audio_file_path: str, language: str, include_timestamps: bool
    ) -> Dict[str, Any]:
        """Transcribe using OpenAI Whisper API"""
        try:
            from openai import AsyncOpenAI
            
            client = AsyncOpenAI(api_key=self.whisper_api_key)
            
            # Open audio file
            with open(audio_file_path, "rb") as audio_file:
                # Transcribe
                if include_timestamps:
                    result = await client.audio.transcriptions.create(
                        model="whisper-1",
                        file=audio_file,
                        language=None if language == "auto" else language,
                        response_format="verbose_json",
                        timestamp_granularities=["word"]
                    )
                else:
                    result = await client.audio.transcriptions.create(
                        model="whisper-1",
                        file=audio_file,
                        language=None if language == "auto" else language,
                    )
            
            logger.info(f"🎤 Audio transcribed via API: {Path(audio_file_path).name}")
            
            return {
                "success": True,
                "fallback": False,
                "text": result.text.strip(),
                "language": getattr(result, "language", language),
                "duration": getattr(result, "duration", 0.0),
                "confidence": 0.0,
                "file_path": audio_file_path,
                "model": "whisper-1",
                "timestamps": getattr(result, "words", None) if include_timestamps else None,
                "status": "success",
                "engine": "whisper-api",
            }
            
        except Exception as e:
            logger.error(f"OpenAI Whisper API transcription failed: {e}")
            return self._fallback_response(audio_file_path, language, include_timestamps, str(e))

    async def transcribe_stream(self, audio_chunks: bytes, session_id: str) -> Dict[str, Any]:
        """
        Transcribe streaming audio in real-time.

        Args:
            audio_chunks: Audio data chunks
            session_id: Session identifier

        Returns:
            Partial transcription result
        """
        # TODO: Implement streaming transcription
        return {
            "text": "",
            "is_final": False,
            "session_id": session_id,
            "status": "streaming",
            "note": "Streaming transcription not yet implemented",
        }

    def get_supported_languages(self) -> list:
        """Get list of supported languages"""
        return [
            {"code": "de", "name": "German"},
            {"code": "en", "name": "English"},
            {"code": "es", "name": "Spanish"},
            {"code": "fr", "name": "French"},
            {"code": "it", "name": "Italian"},
            {"code": "auto", "name": "Auto-detect"},
        ]

    def get_service_info(self) -> Dict[str, Any]:
        """Get transcription service information"""
        return {
            "service": "transcription",
            "enabled": self.whisper_enabled,
            "engine_available": self.engine_available,
            "model": self.whisper_model,
            "local_model": self.use_local_model,
            "supported_languages": len(self.get_supported_languages()),
            "streaming_supported": False,
            "fallback_mode": not self.engine_available,
            "configuration": {
                "WHISPER_ENABLED": self.whisper_enabled,
                "WHISPER_MODEL": self.whisper_model,
                "WHISPER_LOCAL": self.use_local_model,
                "WHISPER_LANGUAGE": self.default_language,
            }
        }


# Singleton instance
_transcription_service: Optional[TranscriptionService] = None


def get_transcription_service() -> TranscriptionService:
    """Get or create transcription service singleton"""
    global _transcription_service
    if _transcription_service is None:
        _transcription_service = TranscriptionService()
    return _transcription_service
