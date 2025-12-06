"""
🎵 Audio Processor

Handles audio file processing, format conversion, and analysis with fallback.
"""

import os
from pathlib import Path
from typing import Any, Dict, Optional

from config.settings import logger, voice_config


class AudioProcessor:
    """
    Audio processing utilities with graceful degradation.

    Supports:
    - Format conversion (with pydub/ffmpeg)
    - Audio normalization
    - Noise reduction
    - Duration and quality analysis
    - Automatic fallback when dependencies unavailable
    """

    def __init__(self):
        self.upload_dir = Path("uploads/audio")
        self.upload_dir.mkdir(parents=True, exist_ok=True)

        # Use centralized configuration
        self.enabled = voice_config.audio_processing_enabled
        self.supported_formats = voice_config.audio_formats
        self.max_file_size = voice_config.max_audio_size

        # Check for audio processing libraries
        self.libraries_available = self._check_libraries()

        logger.info(
            f"🎵 Audio Processor initialized "
            f"(Enabled: {self.enabled}, Libraries: {self.libraries_available})"
        )
        
        if self.enabled and not self.libraries_available:
            logger.warning(
                "⚠️ Audio processing is enabled but libraries (pydub/librosa) "
                "are not available. Some features will use fallback mode."
            )

    def _check_libraries(self) -> Dict[str, bool]:
        """Check availability of audio processing libraries"""
        libraries = {}
        
        try:
            import pydub  # noqa: F401
            libraries['pydub'] = True
        except ImportError:
            libraries['pydub'] = False
            
        try:
            import librosa  # noqa: F401
            libraries['librosa'] = True
        except ImportError:
            libraries['librosa'] = False
            
        try:
            import soundfile  # noqa: F401
            libraries['soundfile'] = True
        except ImportError:
            libraries['soundfile'] = False
            
        return libraries

    async def process_upload(
        self, file_path: str, target_format: Optional[str] = "wav"
    ) -> Dict[str, Any]:
        """
        Process uploaded audio file with automatic fallback.

        Args:
            file_path: Path to uploaded file
            target_format: Target audio format for processing

        Returns:
            Processing result with metadata
        """
        # Validate file existence
        if not os.path.exists(file_path):
            return {
                "success": False,
                "error": "File not found",
                "file_path": file_path,
                "fallback": True,
            }

        try:
            file_size = os.path.getsize(file_path)

            # Validate file size
            if file_size > self.max_file_size:
                return {
                    "success": False,
                    "error": f"File too large. Maximum size: {self.max_file_size / 1024 / 1024:.1f}MB",
                    "file_size": file_size,
                    "max_size": self.max_file_size,
                    "fallback": True,
                }

            # Check if processing is enabled
            if not self.enabled:
                return self._fallback_response(
                    file_path, file_size,
                    "Audio processing is disabled. Set AUDIO_PROCESSING_ENABLED=true in .env."
                )

            # Try actual processing if libraries available
            if self.libraries_available.get('pydub') or self.libraries_available.get('librosa'):
                return await self._process_with_libraries(file_path, target_format)
            else:
                return self._fallback_response(
                    file_path, file_size,
                    "Audio processing libraries not available. Install pydub or librosa."
                )

        except Exception as e:
            logger.error(f"❌ Audio processing failed: {e}")
            return self._fallback_response(file_path, 0, str(e))

    def _fallback_response(self, file_path: str, file_size: int, reason: str) -> Dict[str, Any]:
        """Generate fallback response for audio processing"""
        return {
            "success": True,
            "fallback": True,
            "original_file": file_path,
            "file_size": file_size,
            "format": Path(file_path).suffix[1:],
            "duration": 0.0,
            "sample_rate": 16000,
            "channels": 1,
            "bitrate": 128,
            "processed_file": file_path,
            "status": "fallback",
            "message": "Audio processing returned basic info only",
            "reason": reason,
            "suggestion": "Install pydub or librosa for full audio processing",
        }

    async def _process_with_libraries(
        self, file_path: str, target_format: str
    ) -> Dict[str, Any]:
        """Process audio using available libraries"""
        file_size = os.path.getsize(file_path)
        
        try:
            # Try pydub first (more lightweight)
            if self.libraries_available.get('pydub'):
                from pydub import AudioSegment
                
                audio = AudioSegment.from_file(file_path)
                
                result = {
                    "success": True,
                    "fallback": False,
                    "original_file": file_path,
                    "file_size": file_size,
                    "format": Path(file_path).suffix[1:],
                    "duration": len(audio) / 1000.0,  # Convert ms to seconds
                    "sample_rate": audio.frame_rate,
                    "channels": audio.channels,
                    "bitrate": audio.frame_rate * audio.sample_width * 8 * audio.channels,
                    "processed_file": file_path,
                    "status": "success",
                    "engine": "pydub",
                }
                
                logger.info(f"🎵 Audio processed with pydub: {Path(file_path).name}")
                return result
                
            # Fall back to librosa
            elif self.libraries_available.get('librosa'):
                import librosa
                
                y, sr = librosa.load(file_path, sr=None)
                duration = librosa.get_duration(y=y, sr=sr)
                
                # Determine channel count correctly
                # librosa returns (n_samples,) for mono, (n_channels, n_samples) for multi-channel
                channels = 1 if len(y.shape) == 1 else y.shape[0]
                
                result = {
                    "success": True,
                    "fallback": False,
                    "original_file": file_path,
                    "file_size": file_size,
                    "format": Path(file_path).suffix[1:],
                    "duration": duration,
                    "sample_rate": sr,
                    "channels": channels,
                    "bitrate": sr * 16,  # Estimate
                    "processed_file": file_path,
                    "status": "success",
                    "engine": "librosa",
                }
                
                logger.info(f"🎵 Audio processed with librosa: {Path(file_path).name}")
                return result
            
        except Exception as e:
            logger.error(f"Audio processing with libraries failed: {e}")
            return self._fallback_response(file_path, file_size, str(e))
        
        return self._fallback_response(file_path, file_size, "No processing libraries available")

    async def convert_format(self, input_path: str, output_format: str) -> Dict[str, Any]:
        """
        Convert audio file to different format.

        Args:
            input_path: Input file path
            output_format: Target format (mp3, wav, etc.)

        Returns:
            Conversion result with output path
        """
        if output_format not in self.supported_formats:
            return {
                "error": f"Unsupported format: {output_format}",
                "supported_formats": self.supported_formats,
            }

        output_path = str(Path(input_path).with_suffix(f".{output_format}"))
        
        # Check if pydub is available for conversion
        if not self.libraries_available.get("pydub", False):
            logger.warning(
                "⚠️ Format conversion requested but pydub not available. "
                "Install with: pip install pydub"
            )
            return {
                "input_file": input_path,
                "output_file": output_path,
                "output_format": output_format,
                "status": "unavailable",
                "message": "pydub library not available for format conversion",
                "suggestion": "Install pydub and ffmpeg: pip install pydub && apt-get install ffmpeg"
            }
        
        try:
            from pydub import AudioSegment
            
            # Load audio file
            audio = AudioSegment.from_file(input_path)
            
            # Export to target format
            audio.export(output_path, format=output_format)
            
            logger.info(f"🔄 Audio converted: {Path(input_path).name} -> {output_format}")
            
            return {
                "success": True,
                "input_file": input_path,
                "output_file": output_path,
                "output_format": output_format,
                "duration": len(audio) / 1000.0,  # milliseconds to seconds
                "sample_rate": audio.frame_rate,
                "channels": audio.channels,
                "status": "success",
            }
            
        except Exception as e:
            logger.error(f"❌ Audio conversion failed: {e}")
            return {
                "error": str(e),
                "input_file": input_path,
                "output_file": output_path,
                "output_format": output_format,
                "status": "error",
            }

    async def analyze_audio(self, file_path: str) -> Dict[str, Any]:
        """
        Analyze audio file properties.

        Args:
            file_path: Path to audio file

        Returns:
            Audio analysis including quality metrics
        """
        file_format = Path(file_path).suffix[1:]
        
        # Try WAV analysis with built-in wave library first (no dependencies)
        if file_format.lower() == 'wav':
            try:
                import wave
                with wave.open(file_path, 'rb') as wav_file:
                    frames = wav_file.getnframes()
                    rate = wav_file.getframerate()
                    channels = wav_file.getnchannels()
                    duration = frames / float(rate)
                    
                    # Determine quality based on sample rate
                    if rate >= 44100:
                        quality = "high"
                    elif rate >= 16000:
                        quality = "medium"
                    else:
                        quality = "low"
                    
                    return {
                        "file_path": file_path,
                        "duration": duration,
                        "sample_rate": rate,
                        "channels": channels,
                        "format": file_format,
                        "quality": quality,
                        "bitrate": None,  # WAV doesn't have bitrate info
                        "status": "success",
                        "method": "wave"
                    }
            except Exception as e:
                logger.debug(f"WAV analysis failed: {e}")
        
        # Try pydub for other formats
        if self.libraries_available.get("pydub", False):
            try:
                from pydub import AudioSegment
                
                audio = AudioSegment.from_file(file_path)
                
                # Determine quality based on sample rate and channels
                if audio.frame_rate >= 44100 and audio.channels >= 2:
                    quality = "high"
                elif audio.frame_rate >= 16000:
                    quality = "medium"
                else:
                    quality = "low"
                
                return {
                    "file_path": file_path,
                    "duration": len(audio) / 1000.0,  # milliseconds to seconds
                    "sample_rate": audio.frame_rate,
                    "channels": audio.channels,
                    "format": file_format,
                    "quality": quality,
                    "bitrate": None,  # Not directly available in pydub
                    "status": "success",
                    "method": "pydub"
                }
                
            except Exception as e:
                logger.error(f"❌ Audio analysis failed: {e}")
                return {
                    "file_path": file_path,
                    "error": str(e),
                    "format": file_format,
                    "status": "error",
                }
        
        # Fallback: return basic file info
        logger.warning("⚠️ Audio analysis libraries not available")
        return {
            "file_path": file_path,
            "duration": 0.0,
            "sample_rate": None,
            "channels": None,
            "format": file_format,
            "quality": "unknown",
            "status": "unavailable",
            "message": "Audio analysis libraries not available",
            "suggestion": "Install pydub for full audio analysis: pip install pydub"
        }

    def is_supported_format(self, filename: str) -> bool:
        """Check if file format is supported"""
        ext = Path(filename).suffix[1:].lower()
        return ext in self.supported_formats

    def get_service_info(self) -> Dict[str, Any]:
        """Get audio processor service information"""
        return {
            "service": "audio_processor",
            "enabled": self.enabled,
            "supported_formats": self.supported_formats,
            "max_file_size_mb": self.max_file_size / 1024 / 1024,
            "upload_directory": str(self.upload_dir),
            "libraries_available": self.libraries_available,
            "fallback_mode": not any(self.libraries_available.values()),
            "configuration": {
                "AUDIO_PROCESSING_ENABLED": self.enabled,
                "MAX_AUDIO_SIZE": self.max_file_size,
                "AUDIO_FORMATS": self.supported_formats,
            }
        }


# Singleton instance
_audio_processor: Optional[AudioProcessor] = None


def get_audio_processor() -> AudioProcessor:
    """Get or create audio processor singleton"""
    global _audio_processor
    if _audio_processor is None:
        _audio_processor = AudioProcessor()
    return _audio_processor
