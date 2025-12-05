# ⚙️ Workflow Automation Documentation

**Version:** 1.0.0  
**Last Updated:** 2025-12-05  
**Status:** Feature Implementation Pending

## Overview

The Workflow Automation Pipeline provides a flexible system for orchestrating multi-step automated tasks, enabling users to create, execute, and monitor complex workflows within the chat system.

## Table of Contents

- [Architecture](#architecture)
- [Features](#features)
- [Configuration](#configuration)
- [Workflow Templates](#workflow-templates)
- [API Reference](#api-reference)
- [Integration Guide](#integration-guide)
- [Best Practices](#best-practices)
- [Troubleshooting](#troubleshooting)

---

## Architecture

### Component Structure

```
workflow/
├── automation_pipeline.py  # Core workflow engine
├── __init__.py            # Module initialization
└── templates/             # Workflow templates (future)
    ├── document_processing.yaml
    ├── data_pipeline.yaml
    └── notification_flow.yaml
```

### Workflow Engine Architecture

```
┌─────────────────────────────────────────────────┐
│          Workflow Automation Engine              │
├─────────────────────────────────────────────────┤
│                                                  │
│  ┌──────────────┐     ┌──────────────┐         │
│  │   Workflow   │────→│    Step      │         │
│  │   Manager    │     │   Executor   │         │
│  └──────┬───────┘     └──────┬───────┘         │
│         │                     │                  │
│         │                     │                  │
│  ┌──────▼────────┐    ┌──────▼───────┐         │
│  │   Template    │    │    Event     │         │
│  │   Registry    │    │   Handler    │         │
│  └───────────────┘    └──────────────┘         │
│                                                  │
└─────────────────────────────────────────────────┘
```

### Execution Flow

```
Create Workflow
    │
    ▼
┌────────────┐
│  Validate  │
└─────┬──────┘
      │
      ▼
┌────────────┐
│   Queue    │
└─────┬──────┘
      │
      ▼
┌────────────────┐
│  Execute Steps │←─────┐
└─────┬──────────┘      │
      │                  │
      ├─→ Success ──┐   │
      │              │   │
      ├─→ Failed ───┼→ Retry?
      │              │   
      └─→ Next Step ┘   
      
      ▼
┌────────────┐
│  Complete  │
└────────────┘
```

---

## Features

### Core Capabilities

1. **Workflow Management**
   - Create custom workflows
   - Use predefined templates
   - Edit and update workflows
   - Delete workflows

2. **Step Execution**
   - Sequential execution
   - Parallel execution (planned)
   - Conditional branching
   - Error handling and retries

3. **Workflow Templates**
   - Document processing pipeline
   - Data ETL pipeline
   - Notification workflows
   - Custom templates

4. **Execution Control**
   - Start/stop workflows
   - Pause/resume execution
   - Monitor progress
   - View execution history

5. **Event-Driven Triggers**
   - Schedule-based triggers
   - Event-based triggers
   - Manual triggers
   - Webhook triggers (planned)

### Implementation Status

- ✅ Workflow data structures
- ✅ Template system
- ✅ Status management
- ⏸️ Step execution logic
- ⏸️ Error handling and retries
- ⏸️ Parallel execution
- ⏸️ Event triggers
- ⏸️ Monitoring and logging

---

## Configuration

### Environment Variables

```bash
# .env configuration
WORKFLOW_ENABLED=true
WORKFLOW_MAX_CONCURRENT=5           # Max concurrent workflows
WORKFLOW_STEP_TIMEOUT=300           # Step timeout (seconds)
WORKFLOW_RETRY_COUNT=3              # Retry failed steps
WORKFLOW_RETRY_DELAY=5              # Delay between retries (seconds)
WORKFLOW_STORAGE_PATH=./workflows  # Workflow storage directory
```

### Workflow Storage

```
workflows/
├── definitions/           # Workflow definitions
│   ├── workflow_123.json
│   └── workflow_456.json
├── executions/           # Execution logs
│   ├── exec_789.json
│   └── exec_012.json
└── templates/            # Custom templates
    ├── custom_template_1.yaml
    └── custom_template_2.yaml
```

---

## Workflow Templates

### 1. Document Processing Template

Automates document upload, OCR, analysis, and storage.

```yaml
name: Document Processing
description: OCR, extract, and analyze documents
steps:
  - type: upload
    name: Upload Document
    config:
      max_size: 10485760  # 10MB
      allowed_types: [pdf, docx, jpg, png]
  
  - type: ocr
    name: Extract Text
    config:
      engine: tesseract
      languages: [eng, deu]
  
  - type: analyze
    name: Analyze Content
    config:
      extract_entities: true
      sentiment_analysis: true
  
  - type: store
    name: Store Results
    config:
      destination: database
      vector_store: true
```

**Usage:**
```python
from workflow.automation_pipeline import AutomationPipeline

pipeline = AutomationPipeline()

# Create workflow from template
workflow_id = await pipeline.create_workflow(
    name="Process Invoice",
    template="document_processing"
)

# Execute
result = await pipeline.execute_workflow(workflow_id)
```

### 2. Data Pipeline Template

ETL workflow for data extraction, transformation, and loading.

```yaml
name: Data Pipeline
description: Extract, transform, and load data
steps:
  - type: extract
    name: Extract Data
    config:
      source: api
      endpoint: /api/data
      method: GET
  
  - type: transform
    name: Transform Data
    config:
      operations:
        - normalize
        - deduplicate
        - enrich
  
  - type: validate
    name: Validate Data
    config:
      schema: data_schema.json
      strict: true
  
  - type: load
    name: Load Data
    config:
      destination: database
      table: processed_data
      mode: append
```

### 3. Notification Flow Template

Multi-channel notification workflow.

```yaml
name: Notification Flow
description: Send notifications across multiple channels
steps:
  - type: prepare
    name: Prepare Message
    config:
      template: notification_template
      variables: dynamic
  
  - type: email
    name: Send Email
    config:
      to: recipients
      subject: dynamic
      
  - type: slack
    name: Post to Slack
    config:
      channel: notifications
      
  - type: webhook
    name: Call Webhook
    config:
      url: https://api.example.com/notify
      method: POST
```

### 4. Custom Workflow Template

Create workflows programmatically:

```python
workflow_id = await pipeline.create_workflow(
    name="Custom Processing",
    description="Custom multi-step workflow",
    steps=[
        {
            "type": "fetch",
            "name": "Fetch Data",
            "config": {"url": "https://api.example.com/data"}
        },
        {
            "type": "process",
            "name": "Process Data",
            "config": {"operation": "transform"}
        },
        {
            "type": "notify",
            "name": "Send Notification",
            "config": {"channel": "slack"}
        }
    ]
)
```

---

## API Reference

### Python API

#### Create Workflow

```python
from workflow.automation_pipeline import AutomationPipeline

pipeline = AutomationPipeline()

# From template
workflow_id = await pipeline.create_workflow(
    name="My Workflow",
    template="document_processing"
)

# Custom steps
workflow_id = await pipeline.create_workflow(
    name="My Workflow",
    steps=[
        {"type": "step1", "name": "First Step"},
        {"type": "step2", "name": "Second Step"}
    ],
    description="Custom workflow"
)
```

#### Execute Workflow

```python
# Start execution
execution_id = await pipeline.execute_workflow(
    workflow_id="workflow_123",
    inputs={"file_path": "/path/to/file.pdf"}
)

# Check status
status = await pipeline.get_execution_status(execution_id)

# Wait for completion
result = await pipeline.wait_for_completion(
    execution_id,
    timeout=300
)
```

#### Manage Workflows

```python
# List workflows
workflows = await pipeline.list_workflows()

# Get workflow details
workflow = await pipeline.get_workflow(workflow_id)

# Update workflow
await pipeline.update_workflow(
    workflow_id,
    steps=[...]  # Updated steps
)

# Delete workflow
await pipeline.delete_workflow(workflow_id)
```

#### Control Execution

```python
# Pause execution
await pipeline.pause_execution(execution_id)

# Resume execution
await pipeline.resume_execution(execution_id)

# Cancel execution
await pipeline.cancel_execution(execution_id)

# Retry failed step
await pipeline.retry_step(execution_id, step_index=2)
```

### REST API Endpoints

#### POST /api/workflow/create

Create a new workflow.

**Request:**
```json
{
  "name": "My Workflow",
  "description": "Workflow description",
  "template": "document_processing",
  "steps": []
}
```

**Response:**
```json
{
  "workflow_id": "wf_123456",
  "name": "My Workflow",
  "status": "created",
  "created_at": "2025-12-05T10:00:00Z"
}
```

#### POST /api/workflow/{workflow_id}/execute

Execute a workflow.

**Request:**
```json
{
  "inputs": {
    "file_path": "/path/to/file.pdf",
    "options": {}
  }
}
```

**Response:**
```json
{
  "execution_id": "exec_789012",
  "workflow_id": "wf_123456",
  "status": "running",
  "started_at": "2025-12-05T10:05:00Z"
}
```

#### GET /api/workflow/{workflow_id}/status

Get workflow execution status.

**Response:**
```json
{
  "execution_id": "exec_789012",
  "workflow_id": "wf_123456",
  "status": "running",
  "current_step": 2,
  "total_steps": 4,
  "progress": 50,
  "started_at": "2025-12-05T10:05:00Z",
  "steps": [
    {
      "index": 0,
      "name": "Upload Document",
      "status": "completed",
      "duration": 2.5
    },
    {
      "index": 1,
      "name": "Extract Text",
      "status": "running",
      "started_at": "2025-12-05T10:05:30Z"
    }
  ]
}
```

#### POST /api/workflow/{execution_id}/pause

Pause workflow execution.

#### POST /api/workflow/{execution_id}/resume

Resume paused workflow.

#### POST /api/workflow/{execution_id}/cancel

Cancel workflow execution.

#### GET /api/workflow/list

List all workflows.

**Response:**
```json
{
  "workflows": [
    {
      "id": "wf_123456",
      "name": "My Workflow",
      "template": "document_processing",
      "status": "active",
      "created_at": "2025-12-05T10:00:00Z"
    }
  ],
  "total": 1
}
```

---

## Integration Guide

### Chat Integration

Execute workflows from chat commands:

```python
from workflow.automation_pipeline import AutomationPipeline

async def handle_workflow_command(message: str, user: str):
    pipeline = AutomationPipeline()
    
    # Parse command: /workflow run document_processing
    if message.startswith("/workflow run"):
        template = message.split()[2]
        
        # Create and execute workflow
        workflow_id = await pipeline.create_workflow(
            name=f"{template}_{user}",
            template=template
        )
        
        execution_id = await pipeline.execute_workflow(workflow_id)
        
        return f"Workflow started: {execution_id}"
```

### File Upload Integration

Trigger workflow on file upload:

```python
from workflow.automation_pipeline import AutomationPipeline

async def on_file_upload(file_path: str, file_type: str):
    pipeline = AutomationPipeline()
    
    # Auto-trigger document processing
    if file_type in ["pdf", "docx"]:
        workflow_id = await pipeline.create_workflow(
            name="Auto Document Processing",
            template="document_processing"
        )
        
        await pipeline.execute_workflow(
            workflow_id,
            inputs={"file_path": file_path}
        )
```

### Scheduled Workflows

Schedule periodic workflows:

```python
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from workflow.automation_pipeline import AutomationPipeline

scheduler = AsyncIOScheduler()
pipeline = AutomationPipeline()

# Run daily at 2 AM
@scheduler.scheduled_job('cron', hour=2)
async def daily_data_pipeline():
    workflow_id = await pipeline.create_workflow(
        name="Daily ETL",
        template="data_pipeline"
    )
    await pipeline.execute_workflow(workflow_id)

scheduler.start()
```

### Event-Driven Triggers

Trigger workflows from system events:

```python
from workflow.automation_pipeline import AutomationPipeline

class EventHandler:
    def __init__(self):
        self.pipeline = AutomationPipeline()
    
    async def on_ticket_created(self, ticket_id: str):
        # Auto-create notification workflow
        workflow_id = await self.pipeline.create_workflow(
            name="Ticket Notification",
            template="notification_flow"
        )
        
        await self.pipeline.execute_workflow(
            workflow_id,
            inputs={"ticket_id": ticket_id}
        )
```

---

## Implementation Guide

### Step 1: Implement Step Execution

```python
# In workflow/automation_pipeline.py

async def _execute_step(self, step: Dict[str, Any], 
                       context: Dict[str, Any]) -> Dict[str, Any]:
    """Execute a single workflow step"""
    step_type = step["type"]
    step_config = step.get("config", {})
    
    # Get step handler
    handler = self._get_step_handler(step_type)
    if not handler:
        raise ValueError(f"Unknown step type: {step_type}")
    
    # Execute with timeout
    try:
        result = await asyncio.wait_for(
            handler(step_config, context),
            timeout=self.step_timeout
        )
        return {"status": "success", "result": result}
    
    except asyncio.TimeoutError:
        return {"status": "timeout", "error": "Step timeout"}
    
    except Exception as e:
        return {"status": "failed", "error": str(e)}
```

### Step 2: Implement Step Handlers

```python
def _get_step_handler(self, step_type: str):
    """Get handler function for step type"""
    handlers = {
        "upload": self._handle_upload,
        "ocr": self._handle_ocr,
        "analyze": self._handle_analyze,
        "store": self._handle_store,
        "extract": self._handle_extract,
        "transform": self._handle_transform,
        "validate": self._handle_validate,
        "load": self._handle_load,
        # Add more handlers
    }
    return handlers.get(step_type)

async def _handle_upload(self, config: Dict, context: Dict):
    """Handle file upload step"""
    # Implementation
    pass

async def _handle_ocr(self, config: Dict, context: Dict):
    """Handle OCR step"""
    # Implementation
    pass
```

### Step 3: Implement Retry Logic

```python
async def _execute_step_with_retry(self, step: Dict, context: Dict) -> Dict:
    """Execute step with retry logic"""
    max_retries = self.retry_count
    retry_delay = self.retry_delay
    
    for attempt in range(max_retries + 1):
        result = await self._execute_step(step, context)
        
        if result["status"] == "success":
            return result
        
        if attempt < max_retries:
            logger.warning(f"Step failed, retrying in {retry_delay}s...")
            await asyncio.sleep(retry_delay)
        else:
            logger.error(f"Step failed after {max_retries} retries")
            return result
```

### Step 4: Implement Parallel Execution

```python
async def _execute_parallel_steps(self, steps: List[Dict], 
                                  context: Dict) -> List[Dict]:
    """Execute multiple steps in parallel"""
    tasks = [
        self._execute_step_with_retry(step, context)
        for step in steps
    ]
    
    results = await asyncio.gather(*tasks, return_exceptions=True)
    
    return [
        r if not isinstance(r, Exception) 
        else {"status": "failed", "error": str(r)}
        for r in results
    ]
```

---

## Best Practices

### 1. Workflow Design

**Keep Steps Atomic:**
```python
# Good: Single responsibility
steps = [
    {"type": "fetch", "name": "Fetch Data"},
    {"type": "validate", "name": "Validate Data"},
    {"type": "process", "name": "Process Data"}
]

# Bad: Multiple responsibilities
steps = [
    {"type": "fetch_and_process", "name": "Fetch and Process"}
]
```

**Use Descriptive Names:**
```python
# Good
{"type": "ocr", "name": "Extract Text from Invoice PDF"}

# Bad
{"type": "ocr", "name": "Step 2"}
```

### 2. Error Handling

**Handle Errors Gracefully:**
```python
try:
    result = await pipeline.execute_workflow(workflow_id)
except WorkflowExecutionError as e:
    logger.error(f"Workflow failed: {e}")
    # Notify user
    await notify_user(f"Workflow failed: {e.message}")
```

**Implement Rollback:**
```python
async def execute_with_rollback(workflow_id: str):
    checkpoint = None
    try:
        checkpoint = await pipeline.create_checkpoint(workflow_id)
        result = await pipeline.execute_workflow(workflow_id)
        return result
    except Exception as e:
        if checkpoint:
            await pipeline.rollback(checkpoint)
        raise
```

### 3. Performance

**Use Parallel Execution When Possible:**
```python
# Mark steps as parallelizable
steps = [
    {"type": "fetch_api1", "parallel_group": 1},
    {"type": "fetch_api2", "parallel_group": 1},
    {"type": "merge", "parallel_group": 2}  # Wait for group 1
]
```

**Implement Caching:**
```python
async def execute_with_cache(workflow_id: str, inputs: Dict):
    cache_key = f"{workflow_id}:{hash(str(inputs))}"
    
    # Check cache
    cached = await cache.get(cache_key)
    if cached:
        return cached
    
    # Execute
    result = await pipeline.execute_workflow(workflow_id, inputs)
    
    # Cache result
    await cache.set(cache_key, result, ttl=3600)
    return result
```

### 4. Monitoring

**Add Progress Callbacks:**
```python
async def on_step_complete(step_index: int, step_name: str, result: Dict):
    logger.info(f"Step {step_index} ({step_name}) completed")
    await websocket.send_json({
        "type": "workflow_progress",
        "step": step_index,
        "result": result
    })

await pipeline.execute_workflow(
    workflow_id,
    on_step_complete=on_step_complete
)
```

---

## Testing

### Unit Tests

```python
# tests/unit/test_workflow_automation.py
import pytest
from workflow.automation_pipeline import AutomationPipeline

@pytest.fixture
def pipeline():
    return AutomationPipeline()

@pytest.mark.asyncio
async def test_create_workflow(pipeline):
    workflow_id = await pipeline.create_workflow(
        name="Test Workflow",
        steps=[{"type": "test", "name": "Test Step"}]
    )
    assert workflow_id is not None

@pytest.mark.asyncio
async def test_execute_workflow(pipeline):
    workflow_id = await pipeline.create_workflow(
        name="Test",
        template="document_processing"
    )
    execution_id = await pipeline.execute_workflow(workflow_id)
    assert execution_id is not None
```

### Integration Tests

```python
@pytest.mark.asyncio
async def test_full_workflow_execution():
    pipeline = AutomationPipeline()
    
    # Create workflow
    workflow_id = await pipeline.create_workflow(
        name="Integration Test",
        template="data_pipeline"
    )
    
    # Execute
    execution_id = await pipeline.execute_workflow(
        workflow_id,
        inputs={"source": "test_data"}
    )
    
    # Wait for completion
    result = await pipeline.wait_for_completion(execution_id)
    
    assert result["status"] == "completed"
```

---

## Troubleshooting

### Workflow Stuck in Running State

**Problem:** Workflow execution hangs

**Solutions:**
1. Check step timeout: `WORKFLOW_STEP_TIMEOUT=300`
2. Review logs for stuck step
3. Implement heartbeat monitoring
4. Add execution timeout

### High Memory Usage

**Problem:** Memory consumption increases during execution

**Solutions:**
1. Reduce concurrent workflows: `WORKFLOW_MAX_CONCURRENT=3`
2. Implement streaming for large data
3. Clear context between steps
4. Use pagination for large datasets

### Failed Step Retries Not Working

**Problem:** Retries don't execute

**Solutions:**
1. Check retry configuration: `WORKFLOW_RETRY_COUNT=3`
2. Verify retry delay: `WORKFLOW_RETRY_DELAY=5`
3. Ensure step is retryable
4. Check error type (some errors shouldn't retry)

---

## Roadmap

### Phase 1: Core Implementation (Current)
- [x] Workflow data structures
- [x] Template system
- [ ] Step execution engine
- [ ] Error handling and retries
- [ ] Execution monitoring

### Phase 2: Advanced Features
- [ ] Parallel step execution
- [ ] Conditional branching
- [ ] Nested workflows
- [ ] Dynamic step generation
- [ ] Workflow versioning

### Phase 3: Integration
- [ ] Event-driven triggers
- [ ] Webhook integrations
- [ ] Schedule-based execution
- [ ] External system connectors
- [ ] API gateway integration

### Phase 4: Enterprise Features
- [ ] Workflow marketplace
- [ ] Visual workflow designer
- [ ] A/B testing workflows
- [ ] Workflow analytics
- [ ] Multi-tenancy support

---

**Last Updated:** 2025-12-05  
**Version:** 1.0.0  
**Status:** Documentation Complete - Implementation Pending
