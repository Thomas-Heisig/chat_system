# 🔊 Voice Processing Documentation

**Version:** 1.0.0  
**Last Updated:** 2025-12-05  
**Status:** Feature Implementation Pending

## Overview

The Voice Processing module provides comprehensive audio handling capabilities for the chat system, including text-to-speech (TTS), speech-to-text (STT) transcription, and audio file processing.

## Table of Contents

- [Architecture](#architecture)
- [Components](#components)
- [Configuration](#configuration)
- [API Reference](#api-reference)
- [Integration Guide](#integration-guide)
- [Troubleshooting](#troubleshooting)
- [Roadmap](#roadmap)

---

## Architecture

### Component Overview

```
voice/
├── text_to_speech.py      # TTS service for generating speech from text
├── transcription.py        # STT service using Whisper
├── audio_processor.py      # Audio file processing and conversion
└── __init__.py            # Module initialization
```

### Data Flow

```
┌─────────────┐
│   Client    │
└──────┬──────┘
       │
       ├── Text Input ────────────┐
       │                          ▼
       │                  ┌───────────────┐
       │                  │ TTS Service   │
       │                  │ (text_to_speech)│
       │                  └───────┬───────┘
       │                          │
       │                   Audio Output
       │
       ├── Audio Upload ─────────┐
       │                          ▼
       │                  ┌───────────────┐
       │                  │ Audio         │
       │                  │ Processor     │
       │                  └───────┬───────┘
       │                          │
       │                   Processed Audio
       │                          │
       │                          ▼
       │                  ┌───────────────┐
       │                  │ Transcription │
       │                  │ Service       │
       │                  └───────┬───────┘
       │                          │
       └──────────── Text Output ─┘
```

---

## Components

### 1. Text-to-Speech Service

**File:** `voice/text_to_speech.py`

#### Features

- **Multiple TTS Engines**: Support for OpenAI TTS, Google Cloud TTS, Azure TTS, and Coqui TTS
- **Voice Selection**: Choose from various voice profiles
- **Speed Control**: Adjust speech rate (0.5x to 2.0x)
- **Format Support**: MP3, WAV, OGG output formats
- **Streaming Support**: Real-time speech generation (planned)

#### Configuration

```bash
# .env configuration
TTS_ENABLED=true
TTS_ENGINE=openai           # Options: openai, google, azure, coqui
TTS_VOICE=alloy             # Engine-specific voice ID
TTS_FORMAT=mp3              # Output format: mp3, wav, ogg
```

#### Usage Example

```python
from voice.text_to_speech import get_tts_service

# Initialize service
tts = get_tts_service()

# Generate speech
result = await tts.generate_speech(
    text="Hello, how can I help you today?",
    voice="alloy",
    speed=1.0,
    output_path="output/greeting.mp3"
)

# Check available voices
voices = tts.get_available_voices()

# Get service information
info = tts.get_service_info()
```

#### Available Voices

**OpenAI TTS:**
- `alloy` - Neutral, balanced voice
- `echo` - Clear, professional voice
- `fable` - Expressive, storytelling voice
- `onyx` - Deep, authoritative voice
- `nova` - Energetic, friendly voice
- `shimmer` - Soft, gentle voice

**Google Cloud TTS:**
- `de-DE-Wavenet-A` - German Female
- `de-DE-Wavenet-B` - German Male
- `en-US-Wavenet-A` - English Female
- `en-US-Wavenet-B` - English Male

#### Implementation Status

- ✅ Service structure and API
- ✅ Configuration management
- ✅ Voice profile definitions
- ⏸️ Actual TTS engine integration (OpenAI API)
- ⏸️ Streaming support
- ⏸️ Audio caching

#### Next Steps

1. **Integrate OpenAI TTS API**
   ```python
   # Required library
   pip install openai
   
   # Implementation
   from openai import AsyncOpenAI
   
   client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))
   response = await client.audio.speech.create(
       model="tts-1",
       voice=voice,
       input=text
   )
   ```

2. **Add Google Cloud TTS**
   ```python
   pip install google-cloud-texttospeech
   ```

3. **Implement Coqui TTS for local/offline mode**
   ```python
   pip install TTS
   ```

---

### 2. Transcription Service (Whisper)

**File:** `voice/transcription.py`

#### Features

- **Whisper Integration**: OpenAI Whisper model support
- **Language Support**: Auto-detect or specify language
- **Timestamp Extraction**: Word-level timestamps
- **Multiple Models**: tiny, base, small, medium, large
- **Local & Cloud**: Support for both local models and OpenAI API
- **Streaming Transcription**: Real-time audio transcription (planned)

#### Configuration

```bash
# .env configuration
WHISPER_ENABLED=true
WHISPER_MODEL=base          # Options: tiny, base, small, medium, large
WHISPER_LOCAL=true          # Use local model vs. API
OPENAI_API_KEY=sk-xxx       # For API mode
```

#### Usage Example

```python
from voice.transcription import get_transcription_service

# Initialize service
transcription = get_transcription_service()

# Transcribe audio file
result = await transcription.transcribe_audio(
    audio_file_path="uploads/audio/recording.wav",
    language="de",              # Optional: de, en, es, fr, it
    include_timestamps=True
)

# Result structure
{
    "text": "Transcribed text content",
    "language": "de",
    "duration": 45.3,
    "confidence": 0.95,
    "timestamps": [
        {"word": "Hello", "start": 0.0, "end": 0.5},
        ...
    ]
}

# Stream transcription
async for partial in transcription.transcribe_stream(audio_chunks, session_id):
    print(partial["text"])
```

#### Supported Languages

- German (de)
- English (en)
- Spanish (es)
- French (fr)
- Italian (it)
- Auto-detect (auto)

#### Model Comparison

| Model  | Size   | Parameters | Speed     | Accuracy | Use Case            |
|--------|--------|------------|-----------|----------|---------------------|
| tiny   | 39 MB  | 39M        | Very Fast | Good     | Real-time, mobile   |
| base   | 74 MB  | 74M        | Fast      | Better   | General purpose     |
| small  | 244 MB | 244M       | Medium    | Great    | Balanced quality    |
| medium | 769 MB | 769M       | Slow      | Excellent| High accuracy needs |
| large  | 1.5 GB | 1550M      | Very Slow | Best     | Maximum accuracy    |

#### Implementation Status

- ✅ Service structure and API
- ✅ Configuration management
- ✅ Language support
- ⏸️ Whisper model integration
- ⏸️ Timestamp extraction
- ⏸️ Streaming transcription

#### Next Steps

1. **Integrate Local Whisper**
   ```python
   # Required library
   pip install openai-whisper
   
   # Implementation
   import whisper
   
   model = whisper.load_model(self.whisper_model)
   result = model.transcribe(audio_file_path, language=language)
   ```

2. **Add OpenAI Whisper API**
   ```python
   from openai import AsyncOpenAI
   
   client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))
   with open(audio_file_path, "rb") as audio_file:
       transcript = await client.audio.transcriptions.create(
           model="whisper-1",
           file=audio_file
       )
   ```

---

### 3. Audio Processor

**File:** `voice/audio_processor.py`

#### Features

- **Format Conversion**: Convert between MP3, WAV, OGG, FLAC, M4A, WebM
- **Audio Normalization**: Standardize volume levels
- **Noise Reduction**: Remove background noise (planned)
- **Quality Analysis**: Analyze audio properties
- **File Validation**: Check format and size limits
- **Batch Processing**: Process multiple files

#### Configuration

```bash
# .env configuration
MAX_AUDIO_SIZE=26214400     # 25MB in bytes
```

#### Usage Example

```python
from voice.audio_processor import get_audio_processor

# Initialize processor
processor = get_audio_processor()

# Process uploaded file
result = await processor.process_upload(
    file_path="uploads/audio/recording.m4a",
    target_format="wav"
)

# Convert format
conversion = await processor.convert_format(
    input_path="audio.mp3",
    output_format="wav"
)

# Analyze audio
analysis = await processor.analyze_audio("audio.wav")

# Check if format is supported
is_valid = processor.is_supported_format("recording.mp3")
```

#### Supported Formats

- **MP3** - MPEG Audio Layer III (lossy)
- **WAV** - Waveform Audio File Format (lossless)
- **OGG** - Ogg Vorbis (lossy)
- **FLAC** - Free Lossless Audio Codec (lossless)
- **M4A** - MPEG-4 Audio (lossy/lossless)
- **WebM** - WebM Audio (lossy)

#### Implementation Status

- ✅ Service structure and API
- ✅ Format validation
- ✅ File size checks
- ⏸️ Actual audio processing (librosa/pydub)
- ⏸️ Format conversion
- ⏸️ Noise reduction
- ⏸️ Audio normalization

#### Next Steps

1. **Integrate pydub for audio processing**
   ```python
   # Required libraries
   pip install pydub ffmpeg-python
   
   # Implementation
   from pydub import AudioSegment
   
   audio = AudioSegment.from_file(input_path)
   audio = audio.set_frame_rate(16000)
   audio = audio.set_channels(1)
   audio.export(output_path, format=target_format)
   ```

2. **Add librosa for audio analysis**
   ```python
   pip install librosa
   
   import librosa
   
   y, sr = librosa.load(audio_file_path)
   duration = librosa.get_duration(y=y, sr=sr)
   ```

---

## Configuration

### Environment Variables

Complete `.env` configuration for voice processing:

```bash
# === Text-to-Speech Configuration ===
TTS_ENABLED=true
TTS_ENGINE=openai              # openai, google, azure, coqui
TTS_VOICE=alloy                # Engine-specific voice
TTS_FORMAT=mp3                 # mp3, wav, ogg

# === Speech-to-Text Configuration ===
WHISPER_ENABLED=true
WHISPER_MODEL=base             # tiny, base, small, medium, large
WHISPER_LOCAL=true             # true for local, false for API
OPENAI_API_KEY=sk-xxx          # Required for API mode

# === Audio Processing Configuration ===
MAX_AUDIO_SIZE=26214400        # 25MB default

# === Optional API Keys ===
GOOGLE_CLOUD_API_KEY=xxx       # For Google TTS
AZURE_SPEECH_KEY=xxx           # For Azure TTS
AZURE_SPEECH_REGION=xxx        # For Azure TTS
```

### Dependencies

Add to `requirements.txt`:

```txt
# Voice Processing (when implementing)
openai>=1.0.0                  # OpenAI TTS and Whisper API
openai-whisper>=20231117       # Local Whisper model
pydub>=0.25.1                  # Audio processing
ffmpeg-python>=0.2.0           # Audio codec support
librosa>=0.10.0                # Audio analysis
soundfile>=0.12.1              # Audio I/O
numpy>=1.24.0                  # Audio processing arrays

# Optional engines
google-cloud-texttospeech      # Google Cloud TTS
azure-cognitiveservices-speech # Azure TTS
TTS>=0.20.0                    # Coqui TTS (local)
```

### System Dependencies

```bash
# Install FFmpeg (required for audio processing)
# Ubuntu/Debian
sudo apt-get update
sudo apt-get install ffmpeg

# macOS
brew install ffmpeg

# Windows
# Download from https://ffmpeg.org/download.html
```

---

## API Reference

### REST Endpoints

#### POST /api/voice/tts

Generate speech from text.

**Request:**
```json
{
  "text": "Hello, how can I help you?",
  "voice": "alloy",
  "speed": 1.0,
  "format": "mp3"
}
```

**Response:**
```json
{
  "file_path": "/uploads/audio/speech_xyz.mp3",
  "duration": 3.2,
  "format": "mp3",
  "voice": "alloy"
}
```

#### POST /api/voice/transcribe

Transcribe audio to text.

**Request:** Multipart form data
- `file`: Audio file
- `language`: Optional language code
- `include_timestamps`: Boolean

**Response:**
```json
{
  "text": "Transcribed text content",
  "language": "en",
  "duration": 45.3,
  "confidence": 0.95
}
```

#### POST /api/voice/process

Process audio file.

**Request:** Multipart form data
- `file`: Audio file
- `target_format`: Target format (optional)

**Response:**
```json
{
  "processed_file": "/uploads/audio/processed_xyz.wav",
  "format": "wav",
  "duration": 45.3,
  "sample_rate": 16000
}
```

---

## Integration Guide

### WebSocket Integration

Stream audio for real-time transcription:

```javascript
const ws = new WebSocket('ws://localhost:8000/ws/voice');

// Send audio chunks
const mediaRecorder = new MediaRecorder(stream);
mediaRecorder.ondataavailable = (event) => {
  ws.send(JSON.stringify({
    type: 'audio_chunk',
    data: event.data,
    session_id: 'unique_session_id'
  }));
};

// Receive transcriptions
ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  if (data.type === 'transcription') {
    console.log('Transcribed:', data.text);
  }
};
```

### Chat Integration

Integrate voice with the chat system:

```python
from voice.text_to_speech import get_tts_service
from voice.transcription import get_transcription_service

# Text-to-Speech for AI responses
async def send_ai_response_with_voice(message: str):
    # Generate text response
    ai_response = await ai_service.generate(message)
    
    # Convert to speech
    tts = get_tts_service()
    audio = await tts.generate_speech(ai_response)
    
    # Send both text and audio
    return {
        "text": ai_response,
        "audio_url": audio["file_path"]
    }

# Speech-to-Text for user input
async def process_voice_message(audio_file: str):
    transcription = get_transcription_service()
    result = await transcription.transcribe_audio(audio_file)
    
    # Process as regular message
    await process_message(result["text"])
```

---

## Troubleshooting

### Common Issues

#### TTS Not Working

**Problem:** TTS service returns error
**Solutions:**
1. Check `TTS_ENABLED=true` in `.env`
2. Verify API key: `OPENAI_API_KEY=sk-xxx`
3. Check TTS engine is supported: `TTS_ENGINE=openai`
4. Verify output directory exists and is writable

#### Whisper Model Not Loading

**Problem:** Transcription fails with model error
**Solutions:**
1. Install whisper: `pip install openai-whisper`
2. Download model manually: `whisper --model base --download`
3. Check disk space for model files (up to 1.5GB)
4. Verify model name: `WHISPER_MODEL=base`

#### Audio Format Not Supported

**Problem:** Audio upload rejected
**Solutions:**
1. Check file extension: `.mp3`, `.wav`, `.ogg`, `.flac`, `.m4a`, `.webm`
2. Install FFmpeg: `sudo apt-get install ffmpeg`
3. Verify file size under limit (25MB default)
4. Convert format: `ffmpeg -i input.xxx -acodec libmp3lame output.mp3`

#### Poor Transcription Quality

**Problem:** Transcription inaccurate
**Solutions:**
1. Use larger model: `WHISPER_MODEL=medium` or `large`
2. Specify language: `language="de"` instead of auto-detect
3. Improve audio quality: reduce noise, use better microphone
4. Ensure audio is clear and not too quiet

### Debug Mode

Enable detailed logging:

```bash
# .env
LOG_LEVEL=DEBUG
```

Check logs:
```bash
tail -f logs/chat_system.log | grep voice
```

---

## Roadmap

### Phase 1: Core Implementation (Current)
- [x] Service structure and APIs
- [x] Configuration management
- [ ] OpenAI TTS integration
- [ ] Whisper transcription integration
- [ ] Basic audio processing

### Phase 2: Enhanced Features
- [ ] Streaming TTS
- [ ] Real-time transcription
- [ ] Noise reduction
- [ ] Audio normalization
- [ ] Multiple language support

### Phase 3: Advanced Features
- [ ] Voice cloning
- [ ] Custom voice training
- [ ] Speaker diarization (identify speakers)
- [ ] Emotion detection
- [ ] Audio quality enhancement

### Phase 4: Performance & Scale
- [ ] Audio caching
- [ ] Batch processing optimization
- [ ] GPU acceleration for Whisper
- [ ] CDN integration for audio files
- [ ] Load balancing for TTS requests

---

## Performance Considerations

### TTS Performance

- **API Mode**: ~1-2 seconds per request
- **Local Mode**: ~0.5-1 seconds per request (with GPU)
- **Streaming**: Real-time or near real-time

### Whisper Performance

| Model  | CPU Time (30s audio) | GPU Time (30s audio) |
|--------|---------------------|---------------------|
| tiny   | ~10s                | ~2s                 |
| base   | ~15s                | ~3s                 |
| small  | ~30s                | ~5s                 |
| medium | ~60s                | ~10s                |
| large  | ~120s               | ~20s                |

### Resource Requirements

- **Memory**: 512MB - 4GB depending on model
- **Disk**: 100MB - 2GB for models
- **CPU**: Multicore recommended
- **GPU**: Optional but significantly faster (CUDA support)

---

## Testing

### Unit Tests

```python
# tests/unit/test_voice_processing.py
import pytest
from voice.text_to_speech import get_tts_service
from voice.transcription import get_transcription_service
from voice.audio_processor import get_audio_processor

@pytest.mark.asyncio
async def test_tts_generation():
    tts = get_tts_service()
    result = await tts.generate_speech("Test message")
    assert "file_path" in result

@pytest.mark.asyncio
async def test_transcription():
    transcription = get_transcription_service()
    result = await transcription.transcribe_audio("test_audio.wav")
    assert "text" in result

@pytest.mark.asyncio
async def test_audio_processing():
    processor = get_audio_processor()
    result = await processor.process_upload("test.mp3")
    assert result["format"] == "mp3"
```

### Integration Tests

See [TESTING_GUIDE.md](TESTING_GUIDE.md) for complete testing instructions.

---

## Security Considerations

### File Upload Security

1. **File Size Limits**: Enforce `MAX_AUDIO_SIZE`
2. **Format Validation**: Only allow supported formats
3. **Virus Scanning**: Scan uploaded files (recommended)
4. **Storage Isolation**: Store in separate directory
5. **Access Control**: Verify user permissions

### API Key Security

1. **Environment Variables**: Never commit API keys
2. **Key Rotation**: Regularly rotate API keys
3. **Rate Limiting**: Implement per-user limits
4. **Usage Monitoring**: Track API usage

### Privacy

1. **Audio Deletion**: Auto-delete after processing
2. **Encryption**: Encrypt audio files at rest
3. **Transcription Privacy**: Clear transcription cache
4. **Compliance**: Follow GDPR/privacy regulations

---

## Support

For issues or questions:

1. Check [Troubleshooting](#troubleshooting) section
2. Review logs: `logs/chat_system.log`
3. See [CONTRIBUTING.md](../CONTRIBUTING.md)
4. Open issue on GitHub

---

**Last Updated:** 2025-12-05  
**Version:** 1.0.0  
**Status:** Documentation Complete - Implementation Pending
