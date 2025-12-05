# Implementation Notes for TODO Items

This document provides detailed implementation guidance for TODO items that require external library integration.

## Voice Processing Features

### Text-to-Speech Implementation (Task 2)

**Status:** Placeholder implementation ready  
**Files:** `voice/text_to_speech.py`

#### Integration Options

##### Option 1: OpenAI TTS API (Recommended for production)
```bash
# Already have openai in requirements.txt
pip install openai>=1.0.0
```

**Implementation:**
```python
from openai import AsyncOpenAI

client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))

async def generate_speech(self, text: str, voice: str = "alloy", ...):
    response = await client.audio.speech.create(
        model="tts-1",
        voice=voice,
        input=text,
        response_format=self.output_format
    )
    
    # Save to file
    with open(output_path, "wb") as f:
        f.write(response.content)
    
    return {"file_path": output_path, ...}
```

##### Option 2: Google Text-to-Speech (gTTS)
```bash
pip install gTTS
```

**Implementation:**
```python
from gtts import gTTS

def generate_speech(self, text: str, ...):
    tts = gTTS(text=text, lang='de')  # or 'en', etc.
    tts.save(output_path)
    return {"file_path": output_path, ...}
```

##### Option 3: pyttsx3 (Offline)
```bash
pip install pyttsx3
```

**Implementation:**
```python
import pyttsx3

engine = pyttsx3.init()
engine.save_to_file(text, output_path)
engine.runAndWait()
```

#### Configuration

Add to `.env`:
```env
TTS_ENABLED=true
TTS_ENGINE=openai  # or: google, pyttsx3
TTS_VOICE=alloy    # voice identifier
TTS_FORMAT=mp3     # output format
OPENAI_API_KEY=sk-...  # if using OpenAI
```

---

### Whisper Transcription Implementation (Task 3)

**Status:** Placeholder implementation ready  
**Files:** `voice/transcription.py`

#### Integration Options

##### Option 1: OpenAI Whisper API (Recommended)
```bash
# Already have openai in requirements.txt
pip install openai>=1.0.0
```

**Implementation:**
```python
from openai import AsyncOpenAI

client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))

async def transcribe_audio(self, audio_file_path: str, ...):
    with open(audio_file_path, "rb") as audio_file:
        transcript = await client.audio.transcriptions.create(
            model="whisper-1",
            file=audio_file,
            language=language,
            response_format="json" if include_timestamps else "text"
        )
    
    return {
        "text": transcript.text,
        "language": language,
        ...
    }
```

##### Option 2: Local Whisper Model
```bash
pip install openai-whisper
pip install ffmpeg-python  # required dependency
# System dependency: install ffmpeg
```

**Implementation:**
```python
import whisper

# Load model (do once during initialization)
model = whisper.load_model(self.whisper_model)  # tiny, base, small, medium, large

def transcribe_audio(self, audio_file_path: str, ...):
    result = model.transcribe(
        audio_file_path,
        language=language,
        task="transcribe"
    )
    
    return {
        "text": result["text"],
        "segments": result["segments"] if include_timestamps else None,
        ...
    }
```

#### Configuration

Add to `.env`:
```env
WHISPER_ENABLED=true
WHISPER_MODEL=base  # tiny, base, small, medium, large
WHISPER_LOCAL=true  # or false for API
OPENAI_API_KEY=sk-...  # if using API
```

---

### Audio Processing Implementation (Task 4)

**Status:** Placeholder implementation ready  
**Files:** `voice/audio_processor.py`

#### Required Libraries
```bash
pip install librosa>=0.10.0
pip install pydub>=0.25.0
pip install soundfile>=0.12.0
# System dependency: install ffmpeg
```

#### Implementation

##### Format Conversion
```python
from pydub import AudioSegment

async def convert_format(self, input_path: str, output_format: str):
    audio = AudioSegment.from_file(input_path)
    output_path = str(Path(input_path).with_suffix(f".{output_format}"))
    audio.export(output_path, format=output_format)
    
    return {
        "input_file": input_path,
        "output_file": output_path,
        "output_format": output_format
    }
```

##### Audio Analysis
```python
import librosa
import soundfile as sf

async def analyze_audio(self, file_path: str):
    # Load audio
    y, sr = librosa.load(file_path, sr=None)
    
    # Get audio properties
    duration = librosa.get_duration(y=y, sr=sr)
    tempo, _ = librosa.beat.beat_track(y=y, sr=sr)
    
    # Get audio info
    info = sf.info(file_path)
    
    return {
        "duration": duration,
        "sample_rate": sr,
        "channels": info.channels,
        "tempo": tempo,
        "format": Path(file_path).suffix[1:],
        ...
    }
```

##### Audio Normalization
```python
from pydub import AudioSegment
from pydub.effects import normalize

async def process_upload(self, file_path: str, ...):
    audio = AudioSegment.from_file(file_path)
    
    # Normalize audio
    normalized = normalize(audio)
    
    # Convert to target format
    if target_format != Path(file_path).suffix[1:]:
        output_path = str(Path(file_path).with_suffix(f".{target_format}"))
        normalized.export(output_path, format=target_format)
    else:
        output_path = file_path
    
    return {
        "original_file": file_path,
        "processed_file": output_path,
        ...
    }
```

---

## ELYZA Model Integration

### ELYZA Model Loading (Task 5)

**Status:** Placeholder implementation ready  
**Files:** `elyza/elyza_model.py`

#### Model Options

ELYZA is a Japanese LLM. Implementation depends on the specific ELYZA model variant:

##### Option 1: Using Hugging Face Transformers
```bash
pip install transformers>=4.30.0
pip install torch>=2.0.0
pip install accelerate>=0.20.0
```

**Implementation:**
```python
from transformers import AutoModelForCausalLM, AutoTokenizer

def _initialize_model(self):
    if not os.path.exists(self.model_path):
        # Download from Hugging Face
        model_name = "elyza/ELYZA-japanese-Llama-2-7b"  # example
        self.tokenizer = AutoTokenizer.from_pretrained(model_name)
        self.model = AutoModelForCausalLM.from_pretrained(
            model_name,
            device_map="auto",
            torch_dtype="auto"
        )
        self.model_loaded = True
    else:
        # Load local model
        self.tokenizer = AutoTokenizer.from_pretrained(self.model_path)
        self.model = AutoModelForCausalLM.from_pretrained(self.model_path)
        self.model_loaded = True
```

##### Option 2: Using llama.cpp for CPU inference
```bash
pip install llama-cpp-python
```

**Implementation:**
```python
from llama_cpp import Llama

def _initialize_model(self):
    self.model = Llama(
        model_path=f"{self.model_path}/model.gguf",
        n_ctx=2048,
        n_threads=4
    )
    self.model_loaded = True
```

#### Configuration

Add to `.env`:
```env
ENABLE_ELYZA_FALLBACK=true
ELYZA_MODEL_PATH=./models/elyza
ELYZA_MODEL_NAME=elyza/ELYZA-japanese-Llama-2-7b
```

---

### ELYZA Inference Implementation (Task 6)

**Status:** Depends on Task 5  
**Files:** `elyza/elyza_model.py`

#### Implementation

##### Using Transformers
```python
async def generate(self, prompt: str, max_length: int = 512, temperature: float = 0.7):
    if not self.model_loaded:
        return {"error": "Model not loaded"}
    
    # Tokenize input
    inputs = self.tokenizer(prompt, return_tensors="pt")
    
    # Generate
    outputs = self.model.generate(
        **inputs,
        max_length=max_length,
        temperature=temperature,
        do_sample=True,
        top_p=0.95,
        top_k=50
    )
    
    # Decode output
    response = self.tokenizer.decode(outputs[0], skip_special_tokens=True)
    
    return {
        "text": response,
        "model": "elyza",
        "prompt_length": len(prompt),
        ...
    }
```

##### Using llama.cpp
```python
async def generate(self, prompt: str, max_length: int = 512, temperature: float = 0.7):
    if not self.model_loaded:
        return {"error": "Model not loaded"}
    
    response = self.model(
        prompt,
        max_tokens=max_length,
        temperature=temperature,
        stop=["</s>", "\n\n"],
        echo=False
    )
    
    return {
        "text": response["choices"][0]["text"],
        "model": "elyza",
        ...
    }
```

---

## Testing

After implementing any of these features, run the corresponding tests:

```bash
# Voice services
pytest tests/unit/test_text_to_speech.py -v
pytest tests/unit/test_transcription.py -v
pytest tests/unit/test_audio_processor.py -v

# Integration
pytest tests/unit/test_slack_adapter.py -v

# All new tests
pytest tests/unit/ -v
```

---

## Dependencies Summary

To implement all features, add these to `requirements.txt`:

```txt
# Voice Processing
openai>=1.0.0  # Already in requirements
gTTS>=2.3.0  # OR
pyttsx3>=2.90  # OR
openai-whisper>=20231117  # For local Whisper
librosa>=0.10.0
pydub>=0.25.0
soundfile>=0.12.0
ffmpeg-python>=0.2.0

# ELYZA Model
transformers>=4.30.0
torch>=2.0.0
accelerate>=0.20.0
# OR
llama-cpp-python>=0.2.0

# Integration
slack-sdk>=3.23.0
```

### System Dependencies

Some features require system-level installations:

```bash
# Ubuntu/Debian
sudo apt-get update
sudo apt-get install -y ffmpeg portaudio19-dev

# macOS
brew install ffmpeg portaudio

# Windows
# Download ffmpeg from https://ffmpeg.org/download.html
# Add to PATH
```

---

## Next Steps

1. Choose implementation options based on requirements (cloud vs local, etc.)
2. Install required dependencies
3. Update `.env` with appropriate configuration
4. Replace placeholder implementations in respective files
5. Run tests to verify implementations
6. Update documentation with actual behavior and examples

---

## Notes

- OpenAI API options require API key and have usage costs
- Local models require significant disk space and computational resources
- For production, consider using managed services (OpenAI, Google Cloud, etc.)
- For offline/privacy requirements, use local implementations
- Test thoroughly with sample data before deploying to production
