# Integration Guide

This document covers external service integrations for the Universal Chat System.

## Overview

The system supports various external integrations to extend functionality:

- Slack integration for team communication
- GraphQL API for flexible data querying (planned)
- Mobile-optimized endpoints
- Third-party AI services

## Slack Integration

### Prerequisites

To integrate with Slack, you need:

1. A Slack workspace
2. Slack App credentials (Bot Token, Signing Secret)
3. Appropriate Slack permissions

### Setup

#### 1. Create a Slack App

1. Go to [Slack API Apps](https://api.slack.com/apps)
2. Click "Create New App" → "From scratch"
3. Name your app (e.g., "Universal Chat Bot")
4. Select your workspace

#### 2. Configure Bot Permissions

Add these OAuth scopes under "OAuth & Permissions":

**Bot Token Scopes**:
- `chat:write` - Send messages
- `chat:write.public` - Send messages to public channels
- `channels:read` - View basic channel info
- `groups:read` - View private channel info
- `im:read` - View direct messages
- `mpim:read` - View group messages
- `users:read` - View users
- `files:write` - Upload files

#### 3. Install App to Workspace

1. Go to "Install App" in your Slack app settings
2. Click "Install to Workspace"
3. Authorize the app
4. Copy the "Bot User OAuth Token" (starts with `xoxb-`)

#### 4. Get Signing Secret

1. Go to "Basic Information"
2. Find "Signing Secret" under "App Credentials"
3. Click "Show" and copy the secret

#### 5. Configure Environment Variables

Add to your `.env` file:

```bash
# Slack Configuration
SLACK_BOT_TOKEN=xoxb-your-token-here
SLACK_SIGNING_SECRET=your-signing-secret
SLACK_APP_ID=your-app-id

# Enable Slack integration
ENABLE_SLACK_INTEGRATION=true
```

### Implementation

The Slack adapter is already scaffolded in `integration/adapters/slack_adapter.py`.

#### Complete Implementation

To fully implement Slack integration, install the SDK:

```bash
pip install slack-sdk
```

Update `slack_adapter.py`:

```python
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError

class SlackAdapter(BaseAdapter):
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        config = config or {
            "token": os.getenv("SLACK_BOT_TOKEN"),
            "signing_secret": os.getenv("SLACK_SIGNING_SECRET"),
        }
        super().__init__(config)
        self.client = None
        self.authenticated = False

    async def authenticate(self) -> bool:
        """Authenticate with Slack"""
        token = self.config.get("token")
        if not token:
            logger.warning("⚠️ Slack token not configured")
            return False

        try:
            self.client = WebClient(token=token)
            response = self.client.auth_test()
            
            self.authenticated = True
            logger.info(f"✅ Slack authenticated as {response['user']}")
            return True
            
        except SlackApiError as e:
            logger.error(f"❌ Slack auth failed: {e.response['error']}")
            return False

    async def send(self, message: Dict[str, Any], target: Optional[str] = None) -> Dict[str, Any]:
        """Send message to Slack channel"""
        if not self.authenticated:
            await self.authenticate()

        channel = target or message.get("channel")
        text = message.get("text", "")
        
        try:
            response = self.client.chat_postMessage(
                channel=channel,
                text=text,
                blocks=message.get("blocks"),
                attachments=message.get("attachments")
            )
            
            return {
                "status": "success",
                "platform": "slack",
                "channel": channel,
                "message_id": response["ts"],
                "timestamp": response["ts"]
            }
            
        except SlackApiError as e:
            logger.error(f"❌ Slack send failed: {e.response['error']}")
            return {
                "status": "error",
                "error": e.response['error']
            }
```

#### Event Handling

Set up event subscriptions:

1. In Slack app settings, go to "Event Subscriptions"
2. Enable events
3. Set Request URL to: `https://your-domain.com/api/slack/events`
4. Subscribe to bot events:
   - `message.channels` - Messages in channels
   - `message.groups` - Messages in private channels
   - `message.im` - Direct messages

Create event handler:

```python
from slack_sdk.signature import SignatureVerifier

@app.post("/api/slack/events")
async def slack_events(request: Request):
    """Handle Slack events"""
    
    # Verify request signature
    verifier = SignatureVerifier(os.getenv("SLACK_SIGNING_SECRET"))
    
    body = await request.body()
    timestamp = request.headers.get("X-Slack-Request-Timestamp")
    signature = request.headers.get("X-Slack-Signature")
    
    if not verifier.is_valid(body, timestamp, signature):
        raise HTTPException(403, "Invalid signature")
    
    # Parse event
    event_data = await request.json()
    
    # Handle URL verification
    if event_data.get("type") == "url_verification":
        return {"challenge": event_data["challenge"]}
    
    # Handle event
    if event_data.get("type") == "event_callback":
        event = event_data["event"]
        await handle_slack_event(event)
    
    return {"status": "ok"}


async def handle_slack_event(event: dict):
    """Process Slack event"""
    event_type = event.get("type")
    
    if event_type == "message":
        # Ignore bot messages
        if event.get("bot_id"):
            return
        
        # Process message
        text = event.get("text")
        user = event.get("user")
        channel = event.get("channel")
        
        # Send to chat system
        await process_slack_message(text, user, channel)
```

#### Slash Commands

Create slash commands for interactive features:

1. In Slack app settings, go to "Slash Commands"
2. Create command (e.g., `/chat`)
3. Set Request URL to: `https://your-domain.com/api/slack/commands`

Handle command:

```python
@app.post("/api/slack/commands")
async def slack_command(request: Request):
    """Handle Slack slash commands"""
    
    form_data = await request.form()
    command = form_data.get("command")
    text = form_data.get("text")
    user_id = form_data.get("user_id")
    
    if command == "/chat":
        # Process chat command
        response = await process_chat_command(text, user_id)
        
        return {
            "response_type": "in_channel",
            "text": response
        }
```

### Usage Examples

#### Send Message to Slack

```python
from integration.adapters.slack_adapter import SlackAdapter

adapter = SlackAdapter()
await adapter.authenticate()

# Send simple message
await adapter.send({
    "channel": "#general",
    "text": "Hello from Universal Chat System!"
})

# Send rich message with blocks
await adapter.send({
    "channel": "#general",
    "text": "Project Update",
    "blocks": [
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": "*Project Status*\nAll systems operational ✅"
            }
        }
    ]
})
```

#### Receive Messages from Slack

Messages from Slack are automatically normalized and can be processed through the chat system's normal message pipeline.

## GraphQL API (Planned)

### Overview

GraphQL provides a flexible alternative to REST APIs, allowing clients to request exactly the data they need.

### Installation

```bash
pip install strawberry-graphql[fastapi]
```

### Basic Setup

```python
import strawberry
from strawberry.fastapi import GraphQLRouter

@strawberry.type
class User:
    id: int
    username: str
    email: str

@strawberry.type
class Message:
    id: int
    text: str
    user: User
    created_at: str

@strawberry.type
class Query:
    @strawberry.field
    async def user(self, id: int) -> User:
        # Fetch user from database
        return await get_user(id)
    
    @strawberry.field
    async def messages(self, limit: int = 10) -> list[Message]:
        # Fetch messages
        return await get_messages(limit)

@strawberry.type
class Mutation:
    @strawberry.mutation
    async def send_message(self, text: str, user_id: int) -> Message:
        # Create message
        return await create_message(text, user_id)

schema = strawberry.Schema(query=Query, mutation=Mutation)
graphql_app = GraphQLRouter(schema)

app.include_router(graphql_app, prefix="/graphql")
```

### Example Queries

```graphql
# Get user with specific fields
query {
  user(id: 1) {
    username
    email
  }
}

# Get messages with nested user data
query {
  messages(limit: 5) {
    id
    text
    user {
      username
    }
    created_at
  }
}

# Send message
mutation {
  sendMessage(text: "Hello!", userId: 1) {
    id
    text
    created_at
  }
}
```

## Mobile Optimization

### API Response Optimization

Optimize responses for mobile clients:

#### Pagination

```python
@app.get("/api/messages")
async def get_messages(
    page: int = 1,
    per_page: int = 20,
    fields: Optional[str] = None  # Specify fields: "id,text,created_at"
):
    """Paginated message retrieval with field selection"""
    
    # Parse requested fields
    selected_fields = fields.split(",") if fields else None
    
    messages = await fetch_messages(page, per_page)
    
    # Filter fields if specified
    if selected_fields:
        messages = [
            {k: v for k, v in msg.items() if k in selected_fields}
            for msg in messages
        ]
    
    return {
        "messages": messages,
        "page": page,
        "per_page": per_page,
        "total": await count_messages()
    }
```

#### Response Compression

```python
from fastapi.middleware.gzip import GZIPMiddleware

app.add_middleware(GZIPMiddleware, minimum_size=1000)
```

#### Image Optimization

```python
from PIL import Image
import io

@app.post("/api/upload/image")
async def upload_image(file: UploadFile):
    """Upload and optimize image for mobile"""
    
    # Load image
    image = Image.open(file.file)
    
    # Create thumbnails for different sizes
    thumbnails = {
        "small": (150, 150),
        "medium": (300, 300),
        "large": (600, 600)
    }
    
    results = {}
    for size_name, dimensions in thumbnails.items():
        # Resize maintaining aspect ratio
        thumb = image.copy()
        thumb.thumbnail(dimensions, Image.LANCZOS)
        
        # Save optimized
        output = io.BytesIO()
        thumb.save(output, format='JPEG', quality=85, optimize=True)
        
        # Upload to storage
        url = await upload_to_storage(output.getvalue(), f"thumb_{size_name}.jpg")
        results[size_name] = url
    
    return results
```

#### Offline Support

Add endpoints for offline-first mobile apps:

```python
@app.get("/api/sync")
async def sync_data(
    last_sync: datetime,
    user_id: int
):
    """Sync data since last sync timestamp"""
    
    changes = {
        "messages": await get_messages_since(last_sync, user_id),
        "users": await get_updated_users_since(last_sync),
        "deleted_ids": await get_deleted_messages_since(last_sync)
    }
    
    return {
        "changes": changes,
        "sync_timestamp": datetime.now().isoformat()
    }
```

## Third-Party AI Services

### OpenAI Integration

Already implemented via `services/ai_service.py`.

### Anthropic Claude

Add Claude support:

```python
import anthropic

client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

async def generate_with_claude(prompt: str, model: str = "claude-3-opus-20240229"):
    """Generate response using Claude"""
    
    message = client.messages.create(
        model=model,
        max_tokens=1024,
        messages=[
            {"role": "user", "content": prompt}
        ]
    )
    
    return message.content[0].text
```

### Google Gemini

Add Gemini support:

```python
import google.generativeai as genai

genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))

async def generate_with_gemini(prompt: str):
    """Generate response using Gemini"""
    
    model = genai.GenerativeModel('gemini-pro')
    response = model.generate_content(prompt)
    
    return response.text
```

## Testing Integrations

### Slack Testing

Use Slack's test mode:

```python
from slack_sdk.web.client import WebClient
from slack_sdk.socket_mode import SocketModeClient

# For development/testing
client = SocketModeClient(
    app_token=os.getenv("SLACK_APP_TOKEN"),
    web_client=WebClient(token=os.getenv("SLACK_BOT_TOKEN"))
)
```

### Mock Integrations

Create mocks for testing:

```python
class MockSlackAdapter(BaseAdapter):
    """Mock Slack adapter for testing"""
    
    async def send(self, message: dict, target: str = None):
        return {
            "status": "success",
            "mock": True,
            "message": message
        }
```

## References

- [Slack API Documentation](https://api.slack.com/)
- [Strawberry GraphQL](https://strawberry.rocks/)
- [FastAPI with GraphQL](https://strawberry.rocks/docs/integrations/fastapi)
- [Mobile API Best Practices](https://restfulapi.net/)
