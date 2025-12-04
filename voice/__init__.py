"""
🎤 Voice & Audio Integration Package

Provides voice processing capabilities including:
- Audio upload and storage
- Speech-to-text (Whisper integration)
- Text-to-speech generation
- Real-time audio streaming via WebSocket
"""

from .audio_processor import AudioProcessor
from .text_to_speech import TextToSpeechService
from .transcription import TranscriptionService

__all__ = ["TranscriptionService", "TextToSpeechService", "AudioProcessor"]
