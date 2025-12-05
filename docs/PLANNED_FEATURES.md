# Planned Features

This document outlines features that are currently in planning or partial implementation stages.

## Overview

The Universal Chat System has several features in various stages of development. This document provides details on planned features, their current status, and implementation roadmaps.

## Voice Processing Features

### Status
**Framework**: ✅ Complete  
**Implementation**: ⏳ Planned  
**Priority**: Medium

### Description

Voice processing capabilities for speech-to-text and text-to-speech functionality.

### Current State

The framework is in place with the following modules:

- `voice/text_to_speech.py` - TTS service framework
- `voice/transcription.py` - STT service framework  
- `voice/audio_processor.py` - Audio processing utilities

Currently returns placeholder responses.

### Implementation Plan

#### Phase 1: Text-to-Speech (TTS)

**Option 1: OpenAI TTS API** (Recommended)
```bash
pip install openai
```

```python
from openai import OpenAI

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

async def generate_speech(text: str, voice: str = "alloy"):
    response = client.audio.speech.create(
        model="tts-1",
        voice=voice,
        input=text
    )
    
    response.stream_to_file("output.mp3")
    return "output.mp3"
```

**Option 2: Google Cloud TTS**
```bash
pip install google-cloud-texttospeech
```

**Option 3: Local TTS (pyttsx3)**
```bash
pip install pyttsx3
```

#### Phase 2: Speech-to-Text (STT)

**Option 1: OpenAI Whisper API** (Recommended)
```bash
pip install openai
```

```python
async def transcribe_audio(audio_file: str):
    with open(audio_file, "rb") as f:
        transcript = client.audio.transcriptions.create(
            model="whisper-1",
            file=f
        )
    return transcript.text
```

**Option 2: Local Whisper**
```bash
pip install openai-whisper
```

```python
import whisper

model = whisper.load_model("base")

def transcribe_local(audio_file: str):
    result = model.transcribe(audio_file)
    return result["text"]
```

#### Phase 3: Audio Processing

Features to implement:
- Audio format conversion
- Noise reduction
- Audio normalization
- Voice activity detection

**Libraries**:
```bash
pip install pydub librosa soundfile
```

### Configuration

Add to `.env`:
```bash
# Voice Processing
TTS_ENABLED=true
TTS_ENGINE=openai  # openai, google, pyttsx3
TTS_VOICE=alloy
TTS_FORMAT=mp3

WHISPER_ENABLED=true
WHISPER_MODEL=base  # tiny, base, small, medium, large
WHISPER_LOCAL=false  # Use local model vs API

OPENAI_API_KEY=your-key-here
```

### Estimated Effort
- Implementation: 20-24 hours
- Testing: 4-6 hours
- Documentation: 2 hours

## ELYZA Model Integration

### Status
**Framework**: ✅ Complete  
**Implementation**: ⏳ Planned  
**Priority**: Low

### Description

ELYZA is a Japanese language model that could serve as an offline fallback for AI functionality.

### Current State

Framework exists in `elyza/elyza_model.py`:
- Model loading stub
- Inference placeholder
- Fallback mode management

### Decision Required

**Questions to answer:**
1. Is ELYZA model needed for this use case?
2. What languages are primarily supported?
3. Is Ollama sufficient for offline operation?
4. Are there specific Japanese language requirements?

### Implementation Options

#### Option 1: Full Implementation

If Japanese language support is required:

```python
import transformers

class ELYZAModel:
    def _initialize_model(self):
        self.tokenizer = transformers.AutoTokenizer.from_pretrained(
            "elyza/ELYZA-japanese-Llama-2-7b"
        )
        self.model = transformers.AutoModelForCausalLM.from_pretrained(
            "elyza/ELYZA-japanese-Llama-2-7b"
        )
    
    async def generate(self, prompt: str, max_length: int = 512):
        inputs = self.tokenizer(prompt, return_tensors="pt")
        outputs = self.model.generate(
            inputs.input_ids,
            max_length=max_length,
            temperature=0.7
        )
        return self.tokenizer.decode(outputs[0])
```

#### Option 2: Use Ollama Instead

Ollama supports multiple models and provides similar offline capabilities:

```bash
# Install Ollama
curl https://ollama.ai/install.sh | sh

# Pull models
ollama pull llama3
ollama pull mistral
ollama pull codellama
```

Already integrated via `services/ai_service.py`.

#### Option 3: Remove Framework

If not needed, can be marked as deprecated and removed.

### Recommendation

**Use Ollama** for offline AI capabilities instead of ELYZA unless:
- Specific Japanese language requirements exist
- ELYZA provides unique capabilities not available in Ollama models

### Estimated Effort
- Full Implementation: 20-30 hours
- Ollama Migration: 2-4 hours
- Removal: 1 hour

## Workflow Automation

### Status
**Framework**: ✅ Complete  
**Implementation**: ✅ Basic (Enhanced)  
**Priority**: Medium

### Description

Automation pipeline for executing multi-step workflows.

### Current State

**Completed:**
- Workflow creation and management
- Template system
- Sequential and parallel execution
- Step execution handlers for common types
- Error handling

**Enhanced Features (Just Added):**
- Step type handlers: upload, OCR, analyze, store, extract, transform, validate, load, notify, condition
- Conditional branching support
- Generic step execution

### Usage Examples

#### Document Processing Workflow

```python
from workflow.automation_pipeline import get_automation_pipeline

pipeline = get_automation_pipeline()

# Create workflow from template
workflow_id = await pipeline.create_workflow(
    name="Process Invoice",
    template="document_processing",
    description="Extract and analyze invoice data"
)

# Execute workflow
result = await pipeline.execute_workflow(
    workflow_id,
    input_data={"file_path": "/uploads/invoice.pdf"}
)

print(f"Workflow status: {result['status']}")
print(f"Results: {result['results']}")
```

#### Custom Workflow

```python
# Create custom workflow
workflow_id = await pipeline.create_workflow(
    name="User Onboarding",
    steps=[
        {"type": "validate", "name": "Validate User Data", "config": {}},
        {"type": "store", "name": "Create User Account", "config": {}},
        {"type": "notify", "name": "Send Welcome Email", "config": {
            "recipients": ["user@example.com"]
        }},
        {"type": "condition", "name": "Check Premium", "config": {
            "condition": "premium == True"
        }}
    ]
)
```

### Future Enhancements

#### Scheduled Workflows

```python
from apscheduler.schedulers.asyncio import AsyncIOScheduler

scheduler = AsyncIOScheduler()

@scheduler.scheduled_job('cron', hour=2)
async def daily_backup():
    pipeline = get_automation_pipeline()
    await pipeline.execute_workflow(
        "backup_workflow_id",
        input_data={"timestamp": datetime.now()}
    )

scheduler.start()
```

#### Event-Driven Triggers

```python
@app.post("/api/webhooks/file-uploaded")
async def on_file_uploaded(event: FileUploadEvent):
    """Trigger workflow on file upload"""
    pipeline = get_automation_pipeline()
    
    await pipeline.execute_workflow(
        "file_processing_workflow",
        input_data={"file_id": event.file_id}
    )
```

#### Workflow Builder UI

Create visual workflow builder with drag-and-drop interface:
- Step library
- Connection editor
- Configuration panel
- Execution monitoring

### Integration Points

- **Chat System**: Automate message processing
- **File System**: Process uploaded documents
- **AI Services**: Multi-step AI pipelines
- **Database**: Data ETL workflows
- **Notifications**: Alert workflows

### Estimated Effort for Enhancements
- Scheduled workflows: 6-8 hours
- Event triggers: 4-6 hours
- Workflow UI: 30-40 hours
- Advanced error handling: 8-10 hours

## Plugin System Enhancements

### Status
**Framework**: ✅ Complete  
**Docker Cleanup**: ✅ Implemented  
**Full Isolation**: ⏳ Planned

### Current State

**Completed:**
- Plugin registry and lifecycle
- Permission system
- Sandbox framework
- Docker container cleanup (just added)

**Needs Implementation:**
- Actual Docker container execution
- Resource limits
- Network isolation
- Syscall filtering

### Full Docker Isolation

To implement full plugin isolation:

```python
import docker
import tempfile

class PluginSandbox:
    def __init__(self, plugin: Plugin):
        self.plugin = plugin
        self.client = docker.from_env()
        self.container = None
    
    async def execute(self, function_name: str, args=None, kwargs=None, timeout=30):
        """Execute plugin in Docker container"""
        
        # Create temporary directory for plugin code
        with tempfile.TemporaryDirectory() as tmpdir:
            # Copy plugin files
            plugin_path = self.plugin_dir / self.plugin.plugin_id
            shutil.copytree(plugin_path, tmpdir)
            
            # Start container
            self.container = self.client.containers.run(
                "python:3.11-slim",
                command=["python", self.plugin.entry_point, function_name],
                volumes={tmpdir: {'bind': '/app', 'mode': 'ro'}},
                working_dir='/app',
                mem_limit='256m',
                cpu_quota=50000,
                network_mode='none' if 'network_access' not in self.plugin.permissions else 'bridge',
                detach=True,
                remove=False
            )
            
            # Wait for completion
            try:
                exit_code = self.container.wait(timeout=timeout)
                logs = self.container.logs().decode('utf-8')
                
                return {
                    "success": exit_code == 0,
                    "output": logs,
                    "exit_code": exit_code
                }
            finally:
                self.container.stop()
                self.container.remove()
```

### Estimated Effort
- Full Docker isolation: 12-16 hours
- Resource monitoring: 4-6 hours
- Security hardening: 8-10 hours

## Future Features

### GraphQL API

**Status**: Planned  
**Priority**: Low  
**Effort**: 24-32 hours

See [INTEGRATIONS.md](INTEGRATIONS.md#graphql-api-planned) for details.

### Mobile Optimization

**Status**: Partial  
**Priority**: Medium  
**Effort**: 8-12 hours

See [INTEGRATIONS.md](INTEGRATIONS.md#mobile-optimization) for optimization strategies.

### Distributed Tracing

**Status**: Planned  
**Priority**: Low  
**Effort**: 8-12 hours

See [MONITORING.md](MONITORING.md#distributed-tracing-planned) for implementation guide.

### Prometheus Metrics

**Status**: Planned  
**Priority**: Medium  
**Effort**: 4-6 hours

See [MONITORING.md](MONITORING.md#prometheus-metrics-planned) for setup instructions.

## Feature Request Process

To request a new feature:

1. Check if it's already in this document
2. Create a GitHub issue with:
   - Feature description
   - Use case / business value
   - Proposed implementation (if technical)
   - Priority justification
3. Team reviews and prioritizes
4. Approved features added to roadmap

## Contributing

See [CONTRIBUTING.md](../CONTRIBUTING.md) for guidelines on implementing features.

## References

- [Product Roadmap](../ROADMAP.md)
- [Architecture Documentation](../ARCHITECTURE.md)
- [API Documentation](../README.md#api-documentation)
