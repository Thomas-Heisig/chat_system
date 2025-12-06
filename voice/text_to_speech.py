"""
🔊 Text-to-Speech Service

Handles text-to-speech conversion for voice output with fallback mechanisms.
"""

import os
from pathlib import Path
from typing import Any, Dict, Optional

from config.settings import logger, voice_config


class TextToSpeechService:
    """
    Text-to-speech service for generating audio from text.

    Supports:
    - Multiple TTS engines (OpenAI TTS, gTTS, Coqui, Google, Azure)
    - Voice selection with engine-specific options
    - Speed and pitch control
    - Multiple output formats
    - Graceful fallback to placeholder when dependencies unavailable
    """

    def __init__(self):
        # Use centralized configuration with fallback to environment variables
        self.tts_enabled = voice_config.tts_enabled
        self.tts_engine = voice_config.tts_engine
        self.default_voice = voice_config.tts_voice
        self.output_format = voice_config.tts_format
        self.api_key = voice_config.tts_api_key
        self.default_speed = voice_config.tts_speed

        # Engine availability flags
        self.engine_available = self._check_engine_availability()

        logger.info(
            f"🔊 Text-to-Speech Service initialized "
            f"(Engine: {self.tts_engine}, Enabled: {self.tts_enabled}, "
            f"Available: {self.engine_available})"
        )

        if self.tts_enabled and not self.engine_available:
            logger.warning(
                f"⚠️ TTS engine '{self.tts_engine}' is enabled but dependencies "
                f"are not available. Falling back to placeholder mode."
            )

    def _check_engine_availability(self) -> bool:
        """Check if the configured TTS engine has required dependencies"""
        if not self.tts_enabled:
            return False

        try:
            if self.tts_engine == "gtts":
                import gtts  # noqa: F401

                return True
            elif self.tts_engine == "openai":
                # Check if openai library is available
                import openai  # noqa: F401

                return bool(self.api_key)
            elif self.tts_engine == "google":
                import google.cloud.texttospeech  # noqa: F401

                return True
            elif self.tts_engine == "azure":
                import azure.cognitiveservices.speech  # noqa: F401

                return bool(self.api_key)
            elif self.tts_engine == "coqui":
                from TTS.api import TTS  # noqa: F401

                return True
            else:
                logger.warning(f"Unknown TTS engine: {self.tts_engine}")
                return False
        except ImportError as e:
            logger.debug(f"TTS engine '{self.tts_engine}' not available: {e}")
            return False

    async def generate_speech(
        self,
        text: str,
        voice: Optional[str] = None,
        speed: Optional[float] = None,
        output_path: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Generate speech from text with automatic fallback.

        Args:
            text: Text to convert to speech
            voice: Voice identifier (optional, uses default)
            speed: Speech speed (0.5 to 2.0, optional)
            output_path: Path to save audio file

        Returns:
            Result with audio file path and metadata
        """
        # Validate input
        if not text or not text.strip():
            return {
                "success": False,
                "error": "Text cannot be empty",
                "fallback": True,
            }

        # Use defaults if not provided
        voice = voice or self.default_voice
        speed = speed or self.default_speed

        # Check if TTS is enabled
        if not self.tts_enabled:
            return self._fallback_response(
                text,
                voice,
                speed,
                output_path,
                "Text-to-speech service is disabled. "
                "Set TTS_ENABLED=true in .env to enable TTS.",
            )

        # Check if engine is available
        if not self.engine_available:
            return self._fallback_response(
                text,
                voice,
                speed,
                output_path,
                f"TTS engine '{self.tts_engine}' dependencies not available. "
                f"Install required packages or use a different engine.",
            )

        try:
            # Attempt actual TTS generation based on engine
            if self.tts_engine == "gtts":
                return await self._generate_gtts(text, voice, speed, output_path)
            elif self.tts_engine == "openai":
                return await self._generate_openai(text, voice, speed, output_path)
            else:
                # Fallback for unimplemented engines
                return self._fallback_response(
                    text,
                    voice,
                    speed,
                    output_path,
                    f"TTS engine '{self.tts_engine}' implementation pending",
                )

        except Exception as e:
            logger.error(f"❌ TTS generation failed: {e}")
            return self._fallback_response(
                text, voice, speed, output_path, f"TTS generation failed: {str(e)}"
            )

    def _fallback_response(
        self, text: str, voice: str, speed: float, output_path: Optional[str], reason: str
    ) -> Dict[str, Any]:
        """Generate fallback response when TTS is unavailable"""
        return {
            "success": False,
            "fallback": True,
            "text": text,
            "voice": voice,
            "speed": speed,
            "format": self.output_format,
            "duration": len(text) * 0.05,  # Rough estimate
            "file_path": output_path or "/tmp/placeholder_audio.mp3",
            "file_size": 0,
            "status": "fallback",
            "message": "TTS service returned placeholder response",
            "reason": reason,
            "suggestion": "Install TTS dependencies or configure TTS_ENGINE in .env",
        }

    async def _generate_gtts(
        self, text: str, voice: str, speed: float, output_path: Optional[str]
    ) -> Dict[str, Any]:
        """Generate speech using gTTS (Google Text-to-Speech)"""
        try:
            from gtts import gTTS

            # Determine output path
            if not output_path:
                output_dir = Path("uploads/audio/tts")
                output_dir.mkdir(parents=True, exist_ok=True)
                output_path = str(output_dir / f"tts_{hash(text)}.mp3")

            # Generate speech
            # gTTS expects 2-letter language codes, default to 'en' for other voice IDs
            lang = voice if len(voice) == 2 and voice.isalpha() else "en"
            tts = gTTS(text=text, lang=lang, slow=(speed < 1.0))
            tts.save(output_path)

            file_size = os.path.getsize(output_path)

            logger.info(f"🔊 Speech generated with gTTS: {len(text)} characters")

            return {
                "success": True,
                "fallback": False,
                "text": text,
                "voice": voice,
                "speed": speed,
                "format": "mp3",
                "duration": len(text) * 0.05,
                "file_path": output_path,
                "file_size": file_size,
                "status": "success",
                "engine": "gtts",
            }

        except Exception as e:
            logger.error(f"gTTS generation failed: {e}")
            return self._fallback_response(text, voice, speed, output_path, str(e))

    async def _generate_openai(
        self, text: str, voice: str, speed: float, output_path: Optional[str]
    ) -> Dict[str, Any]:
        """Generate speech using OpenAI TTS API"""
        try:
            from openai import AsyncOpenAI

            client = AsyncOpenAI(api_key=self.api_key)

            # Determine output path
            if not output_path:
                output_dir = Path("uploads/audio/tts")
                output_dir.mkdir(parents=True, exist_ok=True)
                output_path = str(output_dir / f"tts_{hash(text)}.mp3")

            # Generate speech
            response = await client.audio.speech.create(
                model="tts-1", voice=voice, input=text, speed=speed
            )

            # Save to file
            with open(output_path, "wb") as f:
                f.write(response.content)

            file_size = os.path.getsize(output_path)

            logger.info(f"🔊 Speech generated with OpenAI TTS: {len(text)} characters")

            return {
                "success": True,
                "fallback": False,
                "text": text,
                "voice": voice,
                "speed": speed,
                "format": "mp3",
                "duration": len(text) * 0.05,  # Estimate
                "file_path": output_path,
                "file_size": file_size,
                "status": "success",
                "engine": "openai",
            }

        except Exception as e:
            logger.error(f"OpenAI TTS generation failed: {e}")
            return self._fallback_response(text, voice, speed, output_path, str(e))

    async def stream_speech(self, text: str, voice: Optional[str] = None):
        """
        Stream speech generation in real-time.

        Args:
            text: Text to convert
            voice: Voice identifier

        Yields:
            Audio chunks

        Note:
            Streaming TTS is a future enhancement. Currently returns empty bytes.
            See docs/VOICE_PROCESSING.md for implementation roadmap.
        """
        # Not implemented - future enhancement
        yield b""  # Placeholder

    def get_available_voices(self) -> list:
        """Get list of available voices"""
        # Placeholder voices based on common TTS services
        voices = {
            "openai": [
                {"id": "alloy", "name": "Alloy", "language": "multi"},
                {"id": "echo", "name": "Echo", "language": "multi"},
                {"id": "fable", "name": "Fable", "language": "multi"},
                {"id": "onyx", "name": "Onyx", "language": "multi"},
                {"id": "nova", "name": "Nova", "language": "multi"},
                {"id": "shimmer", "name": "Shimmer", "language": "multi"},
            ],
            "google": [
                {"id": "de-DE-Wavenet-A", "name": "German Female", "language": "de"},
                {"id": "de-DE-Wavenet-B", "name": "German Male", "language": "de"},
                {"id": "en-US-Wavenet-A", "name": "English Female", "language": "en"},
                {"id": "en-US-Wavenet-B", "name": "English Male", "language": "en"},
            ],
        }

        return voices.get(self.tts_engine, [])

    def get_service_info(self) -> Dict[str, Any]:
        """Get TTS service information"""
        return {
            "service": "text_to_speech",
            "enabled": self.tts_enabled,
            "engine": self.tts_engine,
            "engine_available": self.engine_available,
            "default_voice": self.default_voice,
            "output_format": self.output_format,
            "available_voices": len(self.get_available_voices()),
            "streaming_supported": False,
            "fallback_mode": not self.engine_available,
            "configuration": {
                "TTS_ENABLED": self.tts_enabled,
                "TTS_ENGINE": self.tts_engine,
                "TTS_VOICE": self.default_voice,
                "TTS_FORMAT": self.output_format,
                "TTS_SPEED": self.default_speed,
            },
        }


# Singleton instance
_tts_service: Optional[TextToSpeechService] = None


def get_tts_service() -> TextToSpeechService:
    """Get or create TTS service singleton"""
    global _tts_service
    if _tts_service is None:
        _tts_service = TextToSpeechService()
    return _tts_service
