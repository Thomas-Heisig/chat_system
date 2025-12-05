# 🧪 Testing Guide - Service Testing and Coverage

**Version:** 1.0.0  
**Last Updated:** 2025-12-05  
**Status:** Baseline Established (11% Coverage)

## Overview

This guide provides comprehensive testing strategies for the chat system, with focus on expanding test coverage for new services including Voice Processing, ELYZA Model, Workflow Automation, Integration adapters, and Plugin System.

## Table of Contents

- [Current Test Coverage](#current-test-coverage)
- [Testing Strategy](#testing-strategy)
- [Unit Testing](#unit-testing)
- [Integration Testing](#integration-testing)
- [Test Infrastructure](#test-infrastructure)
- [Best Practices](#best-practices)
- [Coverage Goals](#coverage-goals)

---

## Current Test Coverage

### Baseline Metrics (2025-12-05)

- **Overall Coverage:** 11%
- **Total Statements:** 7,788
- **Missed Statements:** 6,910
- **Tests Passing:** 25
- **Tests Failing:** 2

### Coverage by Module

| Module | Coverage | Priority |
|--------|----------|----------|
| Core Services | 15% | 🔴 Critical |
| Voice Processing | 0% | 🔴 Critical |
| ELYZA Model | 0% | 🔴 Critical |
| Workflow Automation | 0% | 🔴 Critical |
| Integration Adapters | 0% | 🔴 Critical |
| Plugin System | 0% | 🔴 Critical |
| RAG System | 0% | 🟡 High |
| User Authentication | 0% | 🟡 High |
| Database Layer | 25% | 🟢 Medium |
| Utilities | 40% | 🟢 Medium |

---

## Testing Strategy

### Test Pyramid

```
        ┌─────────────┐
        │     E2E     │  < 10% - Full user flows
        │   Tests     │
        └─────────────┘
       ┌───────────────┐
       │ Integration   │  ~30% - Component interaction
       │    Tests      │
       └───────────────┘
      ┌─────────────────┐
      │   Unit Tests    │  ~60% - Individual components
      └─────────────────┘
```

### Testing Priorities

1. **Critical Path First** (Week 1-2)
   - Voice Processing services
   - ELYZA Model integration
   - Core workflow execution
   - Primary integration adapters
   - Plugin lifecycle

2. **Feature Completion** (Week 3-4)
   - Error handling paths
   - Edge cases
   - Configuration variations
   - Performance tests

3. **Coverage Expansion** (Week 5-6)
   - Utility functions
   - Helper classes
   - Documentation examples
   - Integration scenarios

---

## Unit Testing

### Test Structure

```
tests/
├── unit/                      # Unit tests
│   ├── test_voice_processing.py
│   ├── test_elyza_model.py
│   ├── test_workflow.py
│   ├── test_integrations.py
│   └── test_plugins.py
├── integration/               # Integration tests
│   ├── test_voice_integration.py
│   ├── test_workflow_integration.py
│   └── test_plugin_integration.py
├── e2e/                      # End-to-end tests
│   └── test_complete_flows.py
├── fixtures/                 # Test fixtures
│   ├── audio_samples/
│   ├── test_plugins/
│   └── mock_responses/
└── conftest.py              # Shared fixtures
```

### Voice Processing Tests

**File:** `tests/unit/test_voice_processing.py`

```python
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from voice.text_to_speech import TextToSpeechService, get_tts_service
from voice.transcription import TranscriptionService, get_transcription_service
from voice.audio_processor import AudioProcessor, get_audio_processor


class TestTextToSpeechService:
    """Test TTS service functionality"""
    
    @pytest.fixture
    def tts_service(self):
        return TextToSpeechService()
    
    def test_initialization(self, tts_service):
        """Test service initializes correctly"""
        assert tts_service is not None
        assert tts_service.output_format == "mp3"
    
    @pytest.mark.asyncio
    async def test_generate_speech_disabled(self, tts_service):
        """Test TTS when disabled"""
        tts_service.tts_enabled = False
        result = await tts_service.generate_speech("Test text")
        assert "error" in result
        assert "disabled" in result["error"]
    
    @pytest.mark.asyncio
    async def test_generate_speech_empty_text(self, tts_service):
        """Test TTS with empty text"""
        tts_service.tts_enabled = True
        result = await tts_service.generate_speech("")
        assert "error" in result
    
    @pytest.mark.asyncio
    async def test_generate_speech_success(self, tts_service):
        """Test successful TTS generation"""
        tts_service.tts_enabled = True
        result = await tts_service.generate_speech(
            text="Hello world",
            voice="alloy",
            speed=1.0
        )
        assert "text" in result
        assert result["voice"] == "alloy"
        assert result["speed"] == 1.0
    
    def test_get_available_voices(self, tts_service):
        """Test voice list retrieval"""
        tts_service.tts_engine = "openai"
        voices = tts_service.get_available_voices()
        assert len(voices) > 0
        assert any(v["id"] == "alloy" for v in voices)
    
    def test_get_service_info(self, tts_service):
        """Test service info"""
        info = tts_service.get_service_info()
        assert info["service"] == "text_to_speech"
        assert "enabled" in info
        assert "engine" in info
    
    def test_singleton(self):
        """Test singleton pattern"""
        service1 = get_tts_service()
        service2 = get_tts_service()
        assert service1 is service2


class TestTranscriptionService:
    """Test transcription service functionality"""
    
    @pytest.fixture
    def transcription_service(self):
        return TranscriptionService()
    
    @pytest.fixture
    def temp_audio_file(self, tmp_path):
        """Create temporary audio file for testing"""
        audio_file = tmp_path / "test.wav"
        audio_file.write_bytes(b"fake audio data")
        return str(audio_file)
    
    @pytest.mark.asyncio
    async def test_transcribe_missing_file(self, transcription_service):
        """Test transcription with missing file"""
        result = await transcription_service.transcribe_audio("nonexistent.wav")
        assert "error" in result
        assert "not found" in result["error"]
    
    @pytest.mark.asyncio
    async def test_transcribe_disabled(self, transcription_service, temp_audio_file):
        """Test transcription when disabled"""
        transcription_service.whisper_enabled = False
        result = await transcription_service.transcribe_audio(temp_audio_file)
        assert "error" in result
        assert "disabled" in result["error"]
    
    @pytest.mark.asyncio
    async def test_transcribe_with_language(self, transcription_service, temp_audio_file):
        """Test transcription with specified language"""
        transcription_service.whisper_enabled = True
        result = await transcription_service.transcribe_audio(
            temp_audio_file,
            language="de"
        )
        assert "text" in result
        assert result["language"] == "de"
    
    @pytest.mark.asyncio
    async def test_transcribe_with_timestamps(self, transcription_service, temp_audio_file):
        """Test transcription with timestamps"""
        transcription_service.whisper_enabled = True
        result = await transcription_service.transcribe_audio(
            temp_audio_file,
            include_timestamps=True
        )
        assert "timestamps" in result
    
    def test_get_supported_languages(self, transcription_service):
        """Test language list"""
        languages = transcription_service.get_supported_languages()
        assert len(languages) > 0
        assert any(lang["code"] == "de" for lang in languages)


class TestAudioProcessor:
    """Test audio processor functionality"""
    
    @pytest.fixture
    def audio_processor(self):
        return AudioProcessor()
    
    @pytest.fixture
    def temp_audio_file(self, tmp_path):
        """Create temporary audio file"""
        audio_file = tmp_path / "test.mp3"
        audio_file.write_bytes(b"fake audio data")
        return str(audio_file)
    
    @pytest.mark.asyncio
    async def test_process_missing_file(self, audio_processor):
        """Test processing missing file"""
        result = await audio_processor.process_upload("nonexistent.mp3")
        assert "error" in result
    
    @pytest.mark.asyncio
    async def test_process_file_too_large(self, audio_processor, tmp_path):
        """Test file size limit"""
        large_file = tmp_path / "large.mp3"
        large_file.write_bytes(b"x" * (audio_processor.max_file_size + 1))
        
        result = await audio_processor.process_upload(str(large_file))
        assert "error" in result
        assert "too large" in result["error"]
    
    @pytest.mark.asyncio
    async def test_process_valid_file(self, audio_processor, temp_audio_file):
        """Test processing valid file"""
        result = await audio_processor.process_upload(temp_audio_file)
        assert "file_size" in result
        assert result["format"] == "mp3"
    
    @pytest.mark.asyncio
    async def test_convert_format(self, audio_processor, temp_audio_file):
        """Test format conversion"""
        result = await audio_processor.convert_format(temp_audio_file, "wav")
        assert result["output_format"] == "wav"
    
    @pytest.mark.asyncio
    async def test_convert_unsupported_format(self, audio_processor, temp_audio_file):
        """Test unsupported format"""
        result = await audio_processor.convert_format(temp_audio_file, "xyz")
        assert "error" in result
    
    def test_is_supported_format(self, audio_processor):
        """Test format validation"""
        assert audio_processor.is_supported_format("test.mp3") is True
        assert audio_processor.is_supported_format("test.wav") is True
        assert audio_processor.is_supported_format("test.xyz") is False


# Run tests with coverage
# pytest tests/unit/test_voice_processing.py --cov=voice --cov-report=html
```

### ELYZA Model Tests

**File:** `tests/unit/test_elyza_model.py`

```python
import pytest
from unittest.mock import patch, MagicMock
from elyza.elyza_model import ELYZAModel, get_elyza_model


class TestELYZAModel:
    """Test ELYZA model functionality"""
    
    @pytest.fixture
    def elyza_model(self):
        return ELYZAModel()
    
    def test_initialization(self, elyza_model):
        """Test model initializes correctly"""
        assert elyza_model is not None
        assert elyza_model.fallback_active is False
    
    @pytest.mark.asyncio
    async def test_generate_disabled(self, elyza_model):
        """Test generation when disabled"""
        elyza_model.enabled = False
        result = await elyza_model.generate("Test prompt")
        assert "error" in result
    
    @pytest.mark.asyncio
    async def test_generate_not_loaded(self, elyza_model):
        """Test generation when model not loaded"""
        elyza_model.enabled = True
        elyza_model.model_loaded = False
        result = await elyza_model.generate("Test prompt")
        assert "error" in result
    
    @pytest.mark.asyncio
    async def test_generate_success(self, elyza_model):
        """Test successful generation"""
        elyza_model.enabled = True
        elyza_model.model_loaded = True
        result = await elyza_model.generate("Test prompt")
        assert "text" in result
        assert result["model"] == "elyza"
    
    def test_activate_fallback(self, elyza_model):
        """Test fallback activation"""
        elyza_model.activate_fallback()
        assert elyza_model.fallback_active is True
    
    def test_deactivate_fallback(self, elyza_model):
        """Test fallback deactivation"""
        elyza_model.fallback_active = True
        elyza_model.deactivate_fallback()
        assert elyza_model.fallback_active is False
    
    def test_is_available(self, elyza_model):
        """Test availability check"""
        elyza_model.enabled = True
        elyza_model.model_loaded = True
        assert elyza_model.is_available() is True
        
        elyza_model.enabled = False
        assert elyza_model.is_available() is False
    
    def test_get_model_info(self, elyza_model):
        """Test model info"""
        info = elyza_model.get_model_info()
        assert info["model"] == "ELYZA"
        assert "enabled" in info
        assert "loaded" in info
    
    @pytest.mark.asyncio
    async def test_health_check(self, elyza_model):
        """Test health check"""
        health = await elyza_model.health_check()
        assert "status" in health
        assert "model_loaded" in health


# Run tests: pytest tests/unit/test_elyza_model.py --cov=elyza
```

### Workflow Automation Tests

**File:** `tests/unit/test_workflow.py`

```python
import pytest
from unittest.mock import AsyncMock, patch
from workflow.automation_pipeline import AutomationPipeline, WorkflowStatus


class TestAutomationPipeline:
    """Test workflow automation functionality"""
    
    @pytest.fixture
    def pipeline(self):
        return AutomationPipeline()
    
    @pytest.mark.asyncio
    async def test_create_workflow(self, pipeline):
        """Test workflow creation"""
        workflow_id = await pipeline.create_workflow(
            name="Test Workflow",
            steps=[
                {"type": "step1", "name": "First Step"},
                {"type": "step2", "name": "Second Step"}
            ]
        )
        assert workflow_id is not None
        assert workflow_id in pipeline.workflows
    
    @pytest.mark.asyncio
    async def test_create_workflow_from_template(self, pipeline):
        """Test workflow creation from template"""
        workflow_id = await pipeline.create_workflow(
            name="Doc Processing",
            template="document_processing"
        )
        workflow = pipeline.workflows[workflow_id]
        assert len(workflow["steps"]) > 0
    
    @pytest.mark.asyncio
    async def test_execute_workflow(self, pipeline):
        """Test workflow execution"""
        workflow_id = await pipeline.create_workflow(
            name="Test",
            steps=[{"type": "test", "name": "Test Step"}]
        )
        
        execution_id = await pipeline.execute_workflow(workflow_id)
        assert execution_id is not None
    
    @pytest.mark.asyncio
    async def test_get_execution_status(self, pipeline):
        """Test execution status retrieval"""
        workflow_id = await pipeline.create_workflow(
            name="Test",
            steps=[{"type": "test", "name": "Test"}]
        )
        execution_id = await pipeline.execute_workflow(workflow_id)
        
        status = await pipeline.get_execution_status(execution_id)
        assert "status" in status
    
    def test_list_workflows(self, pipeline):
        """Test workflow listing"""
        workflows = pipeline.list_workflows()
        assert isinstance(workflows, list)


# Run tests: pytest tests/unit/test_workflow.py --cov=workflow
```

### Integration Adapter Tests

**File:** `tests/unit/test_integrations.py`

```python
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from integration.messaging_bridge import MessagingBridge, get_messaging_bridge
from integration.adapters.slack_adapter import SlackAdapter


class TestMessagingBridge:
    """Test messaging bridge functionality"""
    
    @pytest.fixture
    def bridge(self):
        return MessagingBridge()
    
    @pytest.fixture
    def mock_adapter(self):
        adapter = MagicMock()
        adapter.send = AsyncMock(return_value={"success": True})
        adapter.normalize = AsyncMock(return_value={"text": "Normalized"})
        return adapter
    
    def test_register_adapter(self, bridge, mock_adapter):
        """Test adapter registration"""
        bridge.register_adapter("test", mock_adapter)
        assert "test" in bridge.adapters
    
    @pytest.mark.asyncio
    async def test_send_message_success(self, bridge, mock_adapter):
        """Test successful message sending"""
        bridge.register_adapter("test", mock_adapter)
        
        result = await bridge.send_message(
            "test",
            {"text": "Hello"},
            target="channel"
        )
        assert result["success"] is True
    
    @pytest.mark.asyncio
    async def test_send_message_unknown_platform(self, bridge):
        """Test sending to unknown platform"""
        result = await bridge.send_message(
            "unknown",
            {"text": "Hello"}
        )
        assert "error" in result
    
    @pytest.mark.asyncio
    async def test_receive_message(self, bridge, mock_adapter):
        """Test message reception"""
        bridge.register_adapter("test", mock_adapter)
        
        result = await bridge.receive_message(
            "test",
            {"raw": "data"}
        )
        assert "text" in result
    
    def test_get_supported_platforms(self, bridge, mock_adapter):
        """Test platform listing"""
        bridge.register_adapter("test", mock_adapter)
        platforms = bridge.get_supported_platforms()
        assert "test" in platforms


class TestSlackAdapter:
    """Test Slack adapter functionality"""
    
    @pytest.fixture
    def adapter(self):
        return SlackAdapter(token="test-token", signing_secret="test-secret")
    
    @pytest.mark.asyncio
    async def test_normalize_message(self, adapter):
        """Test Slack message normalization"""
        raw = {
            "text": "Hello <@U123|john>!",
            "user": "U456",
            "ts": "1701781200.123456",
            "channel": "C789"
        }
        
        normalized = await adapter.normalize(raw)
        assert "@john" in normalized["text"]
        assert normalized["user_id"] == "U456"
        assert normalized["platform"] == "slack"


# Run tests: pytest tests/unit/test_integrations.py --cov=integration
```

### Plugin System Tests

**File:** `tests/unit/test_plugins.py`

```python
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from services.plugin_service import PluginService, PluginStatus


class TestPluginService:
    """Test plugin service functionality"""
    
    @pytest.fixture
    def service(self):
        return PluginService()
    
    @pytest.fixture
    def test_plugin_path(self, tmp_path):
        """Create test plugin archive"""
        plugin_dir = tmp_path / "test-plugin"
        plugin_dir.mkdir()
        
        # Create plugin.yaml
        (plugin_dir / "plugin.yaml").write_text("""
name: test-plugin
version: 1.0.0
description: Test plugin
permissions:
  - chat_access
""")
        
        # Create main.py
        (plugin_dir / "main.py").write_text("""
class TestPlugin:
    async def initialize(self):
        return True
""")
        
        return plugin_dir
    
    @pytest.mark.asyncio
    async def test_install_plugin(self, service, test_plugin_path):
        """Test plugin installation"""
        plugin_id = await service.install_plugin(str(test_plugin_path))
        assert plugin_id is not None
    
    @pytest.mark.asyncio
    async def test_enable_plugin(self, service, test_plugin_path):
        """Test plugin enabling"""
        plugin_id = await service.install_plugin(str(test_plugin_path))
        await service.enable_plugin(plugin_id)
        
        info = await service.get_plugin_info(plugin_id)
        assert info["status"] == PluginStatus.ENABLED
    
    @pytest.mark.asyncio
    async def test_disable_plugin(self, service, test_plugin_path):
        """Test plugin disabling"""
        plugin_id = await service.install_plugin(str(test_plugin_path))
        await service.enable_plugin(plugin_id)
        await service.disable_plugin(plugin_id)
        
        info = await service.get_plugin_info(plugin_id)
        assert info["status"] == PluginStatus.DISABLED


# Run tests: pytest tests/unit/test_plugins.py --cov=services.plugin_service
```

---

## Integration Testing

### Voice Integration Test

```python
# tests/integration/test_voice_integration.py
import pytest
from voice.text_to_speech import get_tts_service
from voice.transcription import get_transcription_service
from voice.audio_processor import get_audio_processor


@pytest.mark.asyncio
async def test_tts_to_transcription_roundtrip():
    """Test TTS generation and transcription roundtrip"""
    tts = get_tts_service()
    transcription = get_transcription_service()
    processor = get_audio_processor()
    
    # Generate speech
    tts_result = await tts.generate_speech("Hello world")
    audio_file = tts_result.get("file_path")
    
    if audio_file:
        # Process audio
        proc_result = await processor.process_upload(audio_file)
        assert proc_result["format"] in ["mp3", "wav"]
        
        # Transcribe
        trans_result = await transcription.transcribe_audio(audio_file)
        assert "text" in trans_result
```

---

## Test Infrastructure

### Shared Fixtures (conftest.py)

```python
# tests/conftest.py
import pytest
import tempfile
import shutil
from pathlib import Path


@pytest.fixture(scope="session")
def test_data_dir():
    """Temporary directory for test data"""
    temp_dir = tempfile.mkdtemp()
    yield Path(temp_dir)
    shutil.rmtree(temp_dir)


@pytest.fixture
def mock_audio_file(test_data_dir):
    """Create mock audio file"""
    audio_file = test_data_dir / "test.wav"
    audio_file.write_bytes(b"fake audio data")
    return str(audio_file)


@pytest.fixture
def mock_config():
    """Mock configuration"""
    return {
        "TTS_ENABLED": "true",
        "WHISPER_ENABLED": "true",
        "SLACK_ENABLED": "false"
    }
```

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=. --cov-report=html --cov-report=term

# Run specific test file
pytest tests/unit/test_voice_processing.py -v

# Run specific test
pytest tests/unit/test_voice_processing.py::TestTextToSpeechService::test_initialization -v

# Run with markers
pytest -m asyncio  # Only async tests
pytest -m "not slow"  # Exclude slow tests

# Generate coverage report
pytest --cov=. --cov-report=html
# View: open htmlcov/index.html
```

---

## Best Practices

### 1. Test Isolation

```python
# Good: Each test is independent
def test_feature_a():
    service = MyService()
    result = service.do_something()
    assert result == expected

def test_feature_b():
    service = MyService()
    result = service.do_something_else()
    assert result == expected
```

### 2. Use Fixtures

```python
# Good: Reusable test setup
@pytest.fixture
def service():
    svc = MyService()
    yield svc
    svc.cleanup()

def test_with_fixture(service):
    assert service.is_ready()
```

### 3. Mock External Dependencies

```python
@pytest.mark.asyncio
@patch('integration.adapters.slack_adapter.AsyncWebClient')
async def test_slack_send(mock_client):
    """Mock external API calls"""
    mock_client.return_value.chat_postMessage = AsyncMock(
        return_value={"ts": "123"}
    )
    
    adapter = SlackAdapter("token", "secret")
    result = await adapter.send({"text": "Test"}, "#channel")
    assert result["message_id"] == "123"
```

### 4. Test Error Paths

```python
def test_error_handling():
    """Test error conditions"""
    service = MyService()
    
    # Test invalid input
    with pytest.raises(ValueError):
        service.process(None)
    
    # Test error result
    result = service.process_invalid("bad")
    assert result["success"] is False
```

---

## Coverage Goals

### Target Coverage (6 Months)

| Module | Current | Target | Priority |
|--------|---------|--------|----------|
| Voice Processing | 0% | 80% | 🔴 Critical |
| ELYZA Model | 0% | 75% | 🔴 Critical |
| Workflow Automation | 0% | 80% | 🔴 Critical |
| Integration Adapters | 0% | 75% | 🔴 Critical |
| Plugin System | 0% | 70% | 🔴 Critical |
| Core Services | 15% | 85% | 🟡 High |
| RAG System | 0% | 75% | 🟡 High |
| User Authentication | 0% | 90% | 🟡 High |
| Database Layer | 25% | 80% | 🟢 Medium |
| Utilities | 40% | 70% | 🟢 Medium |

### Overall Goal

- **Current:** 11%
- **6 Months:** 75%
- **12 Months:** 85%

---

**Last Updated:** 2025-12-05  
**Version:** 1.0.0  
**Status:** Documentation Complete - Tests To Be Written
