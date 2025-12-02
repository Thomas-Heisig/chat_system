"""
🎤 Voice & Audio Integration Package

Provides voice processing capabilities including:
- Audio upload and storage
- Speech-to-text (Whisper integration)
- Text-to-speech generation
- Real-time audio streaming via WebSocket
"""

from .transcription import TranscriptionService
from .text_to_speech import TextToSpeechService
from .audio_processor import AudioProcessor

__all__ = ['TranscriptionService', 'TextToSpeechService', 'AudioProcessor']
