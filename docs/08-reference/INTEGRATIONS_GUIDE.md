# 🔌 Integration Guide - External Platform Connectivity

**Version:** 1.0.0  
**Last Updated:** 2025-12-05  
**Status:** Feature Implementation Pending

## Overview

The Integration module provides a unified bridge for connecting the chat system with external platforms like Slack, Microsoft Teams, Discord, and other messaging services. It enables bidirectional message flow and platform-specific feature integration.

## Table of Contents

- [Architecture](#architecture)
- [Messaging Bridge](#messaging-bridge)
- [Platform Adapters](#platform-adapters)
- [Configuration](#configuration)
- [API Reference](#api-reference)
- [Implementation Guide](#implementation-guide)
- [Best Practices](#best-practices)
- [Troubleshooting](#troubleshooting)

---

## Architecture

### Component Structure

```
integration/
├── messaging_bridge.py     # Central messaging gateway
├── adapters/              # Platform-specific adapters
│   ├── base_adapter.py    # Base adapter interface
│   ├── slack_adapter.py   # Slack integration
│   ├── teams_adapter.py   # Microsoft Teams (planned)
│   ├── discord_adapter.py # Discord (planned)
│   └── webhook_adapter.py # Generic webhook (planned)
└── __init__.py
```

### Integration Architecture

```
┌─────────────────────────────────────────────────┐
│              Chat System Core                    │
└──────────────────┬──────────────────────────────┘
                   │
                   ▼
         ┌─────────────────┐
         │ Messaging Bridge │
         │  (Central Hub)   │
         └────────┬─────────┘
                  │
     ┌────────────┼────────────┐
     │            │            │
     ▼            ▼            ▼
┌─────────┐  ┌─────────┐  ┌─────────┐
│  Slack  │  │  Teams  │  │ Discord │
│ Adapter │  │ Adapter │  │ Adapter │
└────┬────┘  └────┬────┘  └────┬────┘
     │            │            │
     ▼            ▼            ▼
┌─────────┐  ┌─────────┐  ┌─────────┐
│  Slack  │  │  Teams  │  │ Discord │
│   API   │  │   API   │  │   API   │
└─────────┘  └─────────┘  └─────────┘
```

### Message Flow

```
Incoming Message:
Platform → Adapter → Bridge → Normalize → Chat System

Outgoing Message:
Chat System → Bridge → Transform → Adapter → Platform
```

---

## Messaging Bridge

**File:** `integration/messaging_bridge.py`

### Features

- **Unified Message Format**: Standard internal message representation
- **Pluggable Adapters**: Easy addition of new platforms
- **Protocol Translation**: Platform-specific format conversion
- **Rate Limiting**: Per-platform rate limit enforcement
- **Message Queuing**: Reliable message delivery with retry
- **Error Handling**: Graceful degradation on failure

### Core Functionality

#### 1. Register Platform Adapter

```python
from integration.messaging_bridge import get_messaging_bridge
from integration.adapters.slack_adapter import SlackAdapter

bridge = get_messaging_bridge()

# Register Slack adapter
slack_adapter = SlackAdapter(
    token=os.getenv("SLACK_BOT_TOKEN"),
    signing_secret=os.getenv("SLACK_SIGNING_SECRET")
)

bridge.register_adapter(
    platform="slack",
    adapter=slack_adapter,
    rate_limit={
        "max_messages": 100,
        "window_seconds": 60
    }
)
```

#### 2. Send Message

```python
# Send message to external platform
result = await bridge.send_message(
    platform="slack",
    message={
        "text": "Hello from Chat System!",
        "user": "john_doe",
        "timestamp": "2025-12-05T10:00:00Z"
    },
    target="#general"  # Channel or user ID
)
```

#### 3. Receive Message

```python
# Receive and normalize message from platform
normalized = await bridge.receive_message(
    platform="slack",
    raw_message={
        "ts": "1701781200.123456",
        "text": "Hello!",
        "user": "U123456",
        "channel": "C789012"
    }
)

# Normalized format:
{
    "text": "Hello!",
    "user_id": "U123456",
    "channel_id": "C789012",
    "timestamp": "2025-12-05T10:00:00Z",
    "platform": "slack"
}
```

### Unified Message Format

All messages are normalized to this internal format:

```python
{
    "text": str,                    # Message content
    "user_id": str,                 # Platform user ID
    "username": str,                # Display name
    "channel_id": str,              # Channel/room ID
    "channel_name": str,            # Channel display name
    "timestamp": str,               # ISO 8601 timestamp
    "platform": str,                # Source platform
    "attachments": List[Dict],      # File attachments
    "thread_id": Optional[str],     # Thread/conversation ID
    "reply_to": Optional[str],      # Replied message ID
    "mentions": List[str],          # Mentioned users
    "reactions": List[Dict],        # Message reactions
    "metadata": Dict                # Platform-specific data
}
```

---

## Platform Adapters

### Base Adapter Interface

**File:** `integration/adapters/base_adapter.py`

All platform adapters implement this interface:

```python
from abc import ABC, abstractmethod
from typing import Any, Dict, Optional

class BasePlatformAdapter(ABC):
    """Base interface for platform adapters"""
    
    @abstractmethod
    async def send(self, message: Dict[str, Any], 
                   target: Optional[str] = None) -> Dict[str, Any]:
        """Send message to platform"""
        pass
    
    @abstractmethod
    async def normalize(self, raw_message: Dict[str, Any]) -> Dict[str, Any]:
        """Normalize platform message to unified format"""
        pass
    
    @abstractmethod
    async def authenticate(self) -> bool:
        """Authenticate with platform"""
        pass
    
    @abstractmethod
    def get_platform_name(self) -> str:
        """Get platform identifier"""
        pass
```

---

### Slack Adapter

**File:** `integration/adapters/slack_adapter.py`

#### Configuration

```bash
# .env
SLACK_ENABLED=true
SLACK_BOT_TOKEN=xoxb-your-bot-token
SLACK_SIGNING_SECRET=your-signing-secret
SLACK_APP_TOKEN=xapp-your-app-token  # For Socket Mode
SLACK_DEFAULT_CHANNEL=#general
```

#### Features

- **Bot Integration**: Post messages as bot
- **Event Subscriptions**: Receive real-time events
- **Slash Commands**: Custom command support
- **Interactive Components**: Buttons, menus, modals
- **File Sharing**: Upload/download files
- **Threading**: Reply in threads
- **Reactions**: Add/remove emoji reactions

#### Usage Example

```python
from integration.adapters.slack_adapter import SlackAdapter

# Initialize adapter
adapter = SlackAdapter(
    token=os.getenv("SLACK_BOT_TOKEN"),
    signing_secret=os.getenv("SLACK_SIGNING_SECRET")
)

# Authenticate
await adapter.authenticate()

# Send message
result = await adapter.send(
    message={"text": "Hello Slack!"},
    target="#general"
)

# Send with attachments
result = await adapter.send(
    message={
        "text": "Check out this file",
        "attachments": [{
            "filename": "report.pdf",
            "content": file_bytes
        }]
    },
    target="#general"
)

# Reply in thread
result = await adapter.send(
    message={
        "text": "Thread reply",
        "thread_id": "1701781200.123456"
    },
    target="#general"
)
```

#### Receiving Slack Events

```python
from fastapi import Request

@app.post("/api/integrations/slack/events")
async def slack_events(request: Request):
    """Handle Slack events webhook"""
    body = await request.json()
    
    # Verify request signature
    if not adapter.verify_signature(request.headers, await request.body()):
        return {"error": "Invalid signature"}
    
    # Handle URL verification
    if body.get("type") == "url_verification":
        return {"challenge": body["challenge"]}
    
    # Process event
    if body.get("type") == "event_callback":
        event = body["event"]
        
        # Normalize message
        normalized = await adapter.normalize(event)
        
        # Process in chat system
        await process_external_message(normalized)
    
    return {"ok": True}
```

#### Slack Message Transformations

**From Slack to Chat System:**
```python
# Slack format
{
    "type": "message",
    "text": "Hello <@U123|john>!",
    "user": "U456",
    "ts": "1701781200.123456",
    "channel": "C789"
}

# Transformed to unified format
{
    "text": "Hello @john!",
    "user_id": "U456",
    "timestamp": "2025-12-05T10:00:00Z",
    "channel_id": "C789",
    "platform": "slack",
    "mentions": ["U123"],
    "metadata": {"slack_ts": "1701781200.123456"}
}
```

**From Chat System to Slack:**
```python
# Unified format
{
    "text": "Hello @john!",
    "user": "jane_doe"
}

# Transformed to Slack format
{
    "text": "Hello <@U123>!",
    "username": "jane_doe (via Chat System)",
    "icon_emoji": ":robot_face:"
}
```

#### Implementation Status

- ✅ Adapter structure and interface
- ✅ Authentication framework
- ⏸️ Actual Slack API integration
- ⏸️ Event handling
- ⏸️ Message formatting
- ⏸️ File uploads
- ⏸️ Interactive components

#### Next Steps

1. **Install Slack SDK**
   ```bash
   pip install slack-sdk slack-bolt
   ```

2. **Implement Authentication**
   ```python
   from slack_sdk.web.async_client import AsyncWebClient
   
   async def authenticate(self) -> bool:
       try:
           self.client = AsyncWebClient(token=self.token)
           response = await self.client.auth_test()
           self.bot_user_id = response["user_id"]
           return True
       except Exception as e:
           logger.error(f"Slack auth failed: {e}")
           return False
   ```

3. **Implement Message Sending**
   ```python
   async def send(self, message: Dict, target: str) -> Dict:
       response = await self.client.chat_postMessage(
           channel=target,
           text=message["text"],
           thread_ts=message.get("thread_id")
       )
       return {"message_id": response["ts"]}
   ```

---

### Microsoft Teams Adapter (Planned)

**File:** `integration/adapters/teams_adapter.py`

#### Configuration

```bash
# .env
TEAMS_ENABLED=true
TEAMS_APP_ID=your-app-id
TEAMS_APP_PASSWORD=your-app-password
TEAMS_TENANT_ID=your-tenant-id
```

#### Features (Planned)

- **Bot Framework**: Teams Bot integration
- **Channels**: Post to Teams channels
- **Adaptive Cards**: Rich message formatting
- **Meetings**: Integration with Teams meetings
- **Tabs**: Custom tab applications
- **Activity Feed**: Notifications

#### Usage Example (Future)

```python
from integration.adapters.teams_adapter import TeamsAdapter

adapter = TeamsAdapter(
    app_id=os.getenv("TEAMS_APP_ID"),
    app_password=os.getenv("TEAMS_APP_PASSWORD")
)

await adapter.send(
    message={
        "text": "Hello Teams!",
        "card": {
            "type": "AdaptiveCard",
            "body": [...]
        }
    },
    target="channel_id"
)
```

---

### Discord Adapter (Planned)

**File:** `integration/adapters/discord_adapter.py`

#### Configuration

```bash
# .env
DISCORD_ENABLED=true
DISCORD_BOT_TOKEN=your-bot-token
DISCORD_DEFAULT_GUILD=your-guild-id
```

#### Features (Planned)

- **Bot Commands**: Slash commands and prefix commands
- **Embeds**: Rich embedded messages
- **Webhooks**: Simple webhook posting
- **Voice**: Voice channel integration
- **Roles**: Role-based permissions

---

### Generic Webhook Adapter (Planned)

**File:** `integration/adapters/webhook_adapter.py`

#### Configuration

```bash
# .env
WEBHOOK_ENABLED=true
WEBHOOK_URL=https://example.com/webhook
WEBHOOK_SECRET=your-secret
WEBHOOK_METHOD=POST
```

#### Usage Example (Future)

```python
from integration.adapters.webhook_adapter import WebhookAdapter

adapter = WebhookAdapter(
    url=os.getenv("WEBHOOK_URL"),
    secret=os.getenv("WEBHOOK_SECRET"),
    method="POST"
)

await adapter.send(
    message={"text": "Hello!", "custom_field": "value"}
)
```

---

## Configuration

### Environment Variables

Complete `.env` configuration for integrations:

```bash
# === Messaging Bridge Configuration ===
INTEGRATIONS_ENABLED=true
INTEGRATION_MAX_RETRIES=3
INTEGRATION_RETRY_DELAY=5
INTEGRATION_TIMEOUT=30

# === Slack Configuration ===
SLACK_ENABLED=true
SLACK_BOT_TOKEN=xoxb-your-bot-token
SLACK_SIGNING_SECRET=your-signing-secret
SLACK_APP_TOKEN=xapp-your-app-token
SLACK_DEFAULT_CHANNEL=#general
SLACK_RATE_LIMIT=100              # Messages per minute

# === Microsoft Teams Configuration ===
TEAMS_ENABLED=false
TEAMS_APP_ID=your-app-id
TEAMS_APP_PASSWORD=your-app-password
TEAMS_TENANT_ID=your-tenant-id

# === Discord Configuration ===
DISCORD_ENABLED=false
DISCORD_BOT_TOKEN=your-bot-token
DISCORD_DEFAULT_GUILD=your-guild-id

# === Generic Webhook Configuration ===
WEBHOOK_ENABLED=false
WEBHOOK_URL=https://example.com/webhook
WEBHOOK_SECRET=your-secret
WEBHOOK_METHOD=POST
```

### Dependencies

Add to `requirements.txt`:

```txt
# Integrations (when implementing)
slack-sdk>=3.23.0                  # Slack integration
slack-bolt>=1.18.0                 # Slack Bolt framework
botbuilder-core>=4.15.0            # Microsoft Bot Framework
discord.py>=2.3.0                  # Discord integration
aiohttp>=3.9.0                     # HTTP client for webhooks
cryptography>=41.0.0               # Request signing
```

---

## API Reference

### REST Endpoints

#### POST /api/integrations/send

Send message to external platform.

**Request:**
```json
{
  "platform": "slack",
  "target": "#general",
  "message": {
    "text": "Hello from API!",
    "attachments": []
  }
}
```

**Response:**
```json
{
  "success": true,
  "platform": "slack",
  "message_id": "1701781200.123456",
  "sent_at": "2025-12-05T10:00:00Z"
}
```

#### POST /api/integrations/{platform}/webhook

Receive webhook from external platform.

**Request:** Platform-specific format

**Response:**
```json
{
  "ok": true,
  "processed": true
}
```

#### GET /api/integrations/platforms

List available platforms and their status.

**Response:**
```json
{
  "platforms": [
    {
      "name": "slack",
      "enabled": true,
      "authenticated": true,
      "rate_limit": {
        "current": 45,
        "max": 100,
        "window_seconds": 60
      }
    },
    {
      "name": "teams",
      "enabled": false,
      "authenticated": false
    }
  ]
}
```

#### POST /api/integrations/{platform}/test

Test platform connection.

**Response:**
```json
{
  "platform": "slack",
  "connected": true,
  "latency_ms": 45,
  "bot_info": {
    "id": "B123456",
    "name": "Chat System Bot"
  }
}
```

---

## Implementation Guide

### Step 1: Implement Slack Integration

```bash
# Install dependencies
pip install slack-sdk slack-bolt

# Set environment variables
export SLACK_BOT_TOKEN="xoxb-your-token"
export SLACK_SIGNING_SECRET="your-secret"
```

### Step 2: Complete Slack Adapter

```python
# integration/adapters/slack_adapter.py

from slack_sdk.web.async_client import AsyncWebClient
from slack_sdk.signature import SignatureVerifier

class SlackAdapter(BasePlatformAdapter):
    def __init__(self, token: str, signing_secret: str):
        self.token = token
        self.signing_secret = signing_secret
        self.client = None
        self.verifier = SignatureVerifier(signing_secret)
    
    async def authenticate(self) -> bool:
        try:
            self.client = AsyncWebClient(token=self.token)
            response = await self.client.auth_test()
            self.bot_user_id = response["user_id"]
            logger.info(f"✅ Slack authenticated as {response['user']}")
            return True
        except Exception as e:
            logger.error(f"❌ Slack authentication failed: {e}")
            return False
    
    async def send(self, message: Dict[str, Any], 
                   target: Optional[str] = None) -> Dict[str, Any]:
        """Send message to Slack"""
        if not self.client:
            await self.authenticate()
        
        try:
            response = await self.client.chat_postMessage(
                channel=target or self.default_channel,
                text=message["text"],
                thread_ts=message.get("thread_id"),
                attachments=self._format_attachments(message.get("attachments", []))
            )
            
            return {
                "success": True,
                "message_id": response["ts"],
                "channel": response["channel"]
            }
        except Exception as e:
            logger.error(f"❌ Failed to send Slack message: {e}")
            return {"success": False, "error": str(e)}
    
    async def normalize(self, raw_message: Dict[str, Any]) -> Dict[str, Any]:
        """Normalize Slack message to unified format"""
        return {
            "text": self._parse_slack_text(raw_message.get("text", "")),
            "user_id": raw_message.get("user"),
            "channel_id": raw_message.get("channel"),
            "timestamp": self._parse_timestamp(raw_message.get("ts")),
            "platform": "slack",
            "thread_id": raw_message.get("thread_ts"),
            "mentions": self._extract_mentions(raw_message.get("text", "")),
            "metadata": {"slack_ts": raw_message.get("ts")}
        }
    
    def _parse_slack_text(self, text: str) -> str:
        """Convert Slack mentions to standard format"""
        import re
        # Convert <@U123|john> to @john
        text = re.sub(r'<@([UW][A-Z0-9]+)\|?([^>]*)>', r'@\2', text)
        # Convert <#C123|channel> to #channel
        text = re.sub(r'<#([C][A-Z0-9]+)\|?([^>]*)>', r'#\2', text)
        return text
```

### Step 3: Register Adapter with Bridge

```python
# In main.py or initialization code

from integration.messaging_bridge import get_messaging_bridge
from integration.adapters.slack_adapter import SlackAdapter

async def initialize_integrations():
    bridge = get_messaging_bridge()
    
    # Initialize Slack
    if os.getenv("SLACK_ENABLED", "false").lower() == "true":
        slack = SlackAdapter(
            token=os.getenv("SLACK_BOT_TOKEN"),
            signing_secret=os.getenv("SLACK_SIGNING_SECRET")
        )
        
        if await slack.authenticate():
            bridge.register_adapter(
                platform="slack",
                adapter=slack,
                rate_limit={
                    "max_messages": 100,
                    "window_seconds": 60
                }
            )
            logger.info("✅ Slack integration enabled")
```

### Step 4: Handle Webhook Events

```python
# In routes/integrations.py

from fastapi import APIRouter, Request, HTTPException
from integration.messaging_bridge import get_messaging_bridge

router = APIRouter(prefix="/api/integrations")

@router.post("/slack/events")
async def slack_events(request: Request):
    """Handle Slack event webhooks"""
    bridge = get_messaging_bridge()
    slack_adapter = bridge.adapters.get("slack")
    
    if not slack_adapter:
        raise HTTPException(status_code=503, detail="Slack not configured")
    
    # Verify signature
    body = await request.body()
    if not slack_adapter.verifier.is_valid_request(body, request.headers):
        raise HTTPException(status_code=401, detail="Invalid signature")
    
    data = await request.json()
    
    # URL verification
    if data.get("type") == "url_verification":
        return {"challenge": data["challenge"]}
    
    # Process event
    if data.get("type") == "event_callback":
        event = data["event"]
        
        # Ignore bot messages
        if event.get("bot_id"):
            return {"ok": True}
        
        # Normalize and process
        normalized = await bridge.receive_message("slack", event)
        await process_external_message(normalized)
    
    return {"ok": True}
```

---

## Best Practices

### 1. Error Handling

```python
async def send_with_retry(platform: str, message: Dict, retries: int = 3):
    bridge = get_messaging_bridge()
    
    for attempt in range(retries):
        try:
            result = await bridge.send_message(platform, message)
            if result.get("success"):
                return result
        except Exception as e:
            if attempt == retries - 1:
                logger.error(f"Failed after {retries} attempts: {e}")
                raise
            await asyncio.sleep(2 ** attempt)  # Exponential backoff
```

### 2. Rate Limiting

```python
# Respect platform rate limits
async def send_batch_messages(platform: str, messages: List[Dict]):
    bridge = get_messaging_bridge()
    
    for message in messages:
        # Check rate limit
        status = bridge.get_platform_status(platform)
        if status["rate_limit"]["current"] >= status["rate_limit"]["max"]:
            # Wait for window to reset
            await asyncio.sleep(status["rate_limit"]["window_seconds"])
        
        await bridge.send_message(platform, message)
```

### 3. Message Transformation

```python
def transform_rich_message(message: Dict, platform: str) -> Dict:
    """Transform rich content for platform"""
    if platform == "slack":
        # Convert to Slack blocks
        return {
            "text": message["text"],
            "blocks": create_slack_blocks(message)
        }
    elif platform == "teams":
        # Convert to Adaptive Card
        return {
            "type": "message",
            "attachments": [create_adaptive_card(message)]
        }
    return message
```

---

## Testing

### Unit Tests

```python
# tests/unit/test_integrations.py
import pytest
from integration.messaging_bridge import MessagingBridge
from integration.adapters.slack_adapter import SlackAdapter

@pytest.fixture
def bridge():
    return MessagingBridge()

@pytest.fixture
def slack_adapter():
    return SlackAdapter(token="test-token", signing_secret="test-secret")

def test_register_adapter(bridge, slack_adapter):
    bridge.register_adapter("slack", slack_adapter)
    assert "slack" in bridge.adapters

@pytest.mark.asyncio
async def test_slack_normalize(slack_adapter):
    raw = {
        "text": "Hello <@U123|john>!",
        "user": "U456",
        "ts": "1701781200.123456",
        "channel": "C789"
    }
    
    normalized = await slack_adapter.normalize(raw)
    assert "@john" in normalized["text"]
    assert normalized["user_id"] == "U456"
```

---

## Troubleshooting

### Slack Messages Not Sending

**Solutions:**
1. Verify `SLACK_BOT_TOKEN` is correct
2. Check bot has permission to post in channel
3. Verify bot is invited to channel
4. Check rate limits

### Webhook Signature Verification Fails

**Solutions:**
1. Verify `SLACK_SIGNING_SECRET` is correct
2. Check timestamp is within 5 minutes
3. Ensure raw body is used for signature
4. Review Slack signature docs

### Rate Limit Exceeded

**Solutions:**
1. Implement exponential backoff
2. Batch messages when possible
3. Increase rate limit window
4. Use different channels/workspaces

---

## Roadmap

### Phase 1: Core Implementation
- [x] Messaging bridge structure
- [x] Adapter interface
- [x] Slack adapter structure
- [ ] Slack API integration
- [ ] Webhook handling
- [ ] Message transformation

### Phase 2: Additional Platforms
- [ ] Microsoft Teams adapter
- [ ] Discord adapter
- [ ] Generic webhook adapter
- [ ] Email integration

### Phase 3: Advanced Features
- [ ] Two-way sync
- [ ] Rich message formatting
- [ ] File sharing
- [ ] Interactive components
- [ ] Presence sync

### Phase 4: Enterprise
- [ ] Multi-workspace support
- [ ] Advanced routing
- [ ] Message analytics
- [ ] Compliance features
- [ ] Audit logging

---

**Last Updated:** 2025-12-05  
**Version:** 1.0.0  
**Status:** Documentation Complete - Implementation Pending
