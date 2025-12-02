"""
🎤 Transcription Service

Handles speech-to-text conversion using Whisper or other STT engines.
"""

from typing import Dict, Any, Optional
from pathlib import Path
import os
from config.settings import logger


class TranscriptionService:
    """
    Speech-to-text transcription service.
    
    Supports:
    - Whisper API integration
    - Local Whisper model
    - Multiple language support
    - Timestamp extraction
    """
    
    def __init__(self):
        self.whisper_enabled = os.getenv("WHISPER_ENABLED", "false").lower() == "true"
        self.whisper_model = os.getenv("WHISPER_MODEL", "base")
        self.whisper_api_key = os.getenv("OPENAI_API_KEY", "")
        self.use_local_model = os.getenv("WHISPER_LOCAL", "true").lower() == "true"
        
        logger.info(f"🎤 Transcription Service initialized (Whisper: {self.whisper_enabled})")
    
    async def transcribe_audio(
        self,
        audio_file_path: str,
        language: Optional[str] = None,
        include_timestamps: bool = False
    ) -> Dict[str, Any]:
        """
        Transcribe audio file to text.
        
        Args:
            audio_file_path: Path to audio file
            language: Optional language code (e.g., 'de', 'en')
            include_timestamps: Include word-level timestamps
            
        Returns:
            Transcription result with text and metadata
        """
        if not os.path.exists(audio_file_path):
            return {
                "error": "Audio file not found",
                "file_path": audio_file_path
            }
        
        if not self.whisper_enabled:
            return {
                "error": "Transcription service is disabled",
                "text": "",
                "note": "Enable WHISPER_ENABLED=true in .env to use transcription"
            }
        
        try:
            # TODO: Integrate actual Whisper implementation
            # This is a placeholder
            result = {
                "text": "Placeholder transcription text. Whisper integration pending.",
                "language": language or "auto",
                "duration": 0.0,
                "confidence": 0.0,
                "file_path": audio_file_path,
                "model": self.whisper_model,
                "timestamps": [] if include_timestamps else None,
                "status": "placeholder"
            }
            
            logger.info(f"🎤 Audio transcribed: {Path(audio_file_path).name}")
            return result
            
        except Exception as e:
            logger.error(f"❌ Transcription failed: {e}")
            return {
                "error": str(e),
                "file_path": audio_file_path
            }
    
    async def transcribe_stream(
        self,
        audio_chunks: bytes,
        session_id: str
    ) -> Dict[str, Any]:
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
            "note": "Streaming transcription not yet implemented"
        }
    
    def get_supported_languages(self) -> list:
        """Get list of supported languages"""
        return [
            {"code": "de", "name": "German"},
            {"code": "en", "name": "English"},
            {"code": "es", "name": "Spanish"},
            {"code": "fr", "name": "French"},
            {"code": "it", "name": "Italian"},
            {"code": "auto", "name": "Auto-detect"}
        ]
    
    def get_service_info(self) -> Dict[str, Any]:
        """Get transcription service information"""
        return {
            "service": "transcription",
            "enabled": self.whisper_enabled,
            "model": self.whisper_model,
            "local_model": self.use_local_model,
            "supported_languages": len(self.get_supported_languages()),
            "streaming_supported": False  # TODO: Update when implemented
        }


# Singleton instance
_transcription_service: Optional[TranscriptionService] = None


def get_transcription_service() -> TranscriptionService:
    """Get or create transcription service singleton"""
    global _transcription_service
    if _transcription_service is None:
        _transcription_service = TranscriptionService()
    return _transcription_service
