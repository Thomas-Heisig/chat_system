# Advanced Features Guide

**Version:** 2.0.0  
**Last Updated:** 2025-12-06  
**Estimated Reading Time:** 35 minutes

## 📋 Table of Contents

- [Overview](#overview)
- [WebSocket Real-Time Communication](#websocket-real-time-communication)
- [Advanced Authentication](#advanced-authentication)
- [Plugin System](#plugin-system)
- [Workflow Automation](#workflow-automation)
- [Performance Monitoring](#performance-monitoring)
- [Advanced Security](#advanced-security)
- [Scalability Features](#scalability-features)

## Overview

This guide covers advanced features of the Universal Chat System, including real-time communication, authentication strategies, plugin development, workflow automation, and system optimization techniques.

### Advanced Capabilities

**Real-Time**:
- WebSocket bidirectional communication
- Connection pooling and management
- Message queuing and delivery guarantees
- Presence and typing indicators

**Extensibility**:
- Plugin architecture
- Custom AI model integration
- Workflow automation
- External service integration

**Enterprise**:
- Advanced authentication (OAuth, SAML)
- Multi-tenancy support
- Audit logging
- Compliance features

## WebSocket Real-Time Communication

### 1. WebSocket Architecture

```python
# Connection lifecycle
class WebSocketConnection:
    """Manages individual WebSocket connections"""
    
    def __init__(self, websocket, user_id):
        self.websocket = websocket
        self.user_id = user_id
        self.connected_at = datetime.now()
        self.last_ping = None
        self.message_count = 0
    
    async def send(self, message):
        """Send message to client"""
        try:
            await self.websocket.send_json(message)
            self.message_count += 1
            return True
        except Exception as e:
            logger.error(f"Send failed: {e}")
            return False
    
    async def receive(self):
        """Receive message from client"""
        try:
            data = await self.websocket.receive_json()
            return data
        except Exception as e:
            logger.error(f"Receive failed: {e}")
            return None
    
    async def ping(self):
        """Send ping to check connection"""
        try:
            await self.websocket.send_json({"type": "ping"})
            self.last_ping = datetime.now()
            return True
        except:
            return False
    
    def is_alive(self):
        """Check if connection is still alive"""
        if not self.last_ping:
            return True
        
        timeout = timedelta(seconds=30)
        return datetime.now() - self.last_ping < timeout
```

### 2. Connection Manager

```python
class ConnectionManager:
    """Manages all WebSocket connections"""
    
    def __init__(self):
        self.active_connections: Dict[str, List[WebSocketConnection]] = {}
        self.user_channels: Dict[str, Set[str]] = {}
        self.lock = asyncio.Lock()
    
    async def connect(self, websocket, user_id, channel="general"):
        """Register new connection"""
        async with self.lock:
            conn = WebSocketConnection(websocket, user_id)
            
            # Add to active connections
            if user_id not in self.active_connections:
                self.active_connections[user_id] = []
            self.active_connections[user_id].append(conn)
            
            # Subscribe to channel
            if user_id not in self.user_channels:
                self.user_channels[user_id] = set()
            self.user_channels[user_id].add(channel)
            
            logger.info(f"User {user_id} connected to {channel}")
            
            # Notify others
            await self.broadcast_presence(user_id, "online", channel)
            
            return conn
    
    async def disconnect(self, user_id, connection):
        """Remove connection"""
        async with self.lock:
            if user_id in self.active_connections:
                self.active_connections[user_id].remove(connection)
                
                # Clean up if no more connections
                if not self.active_connections[user_id]:
                    del self.active_connections[user_id]
                    channels = self.user_channels.get(user_id, set())
                    
                    for channel in channels:
                        await self.broadcast_presence(user_id, "offline", channel)
                    
                    if user_id in self.user_channels:
                        del self.user_channels[user_id]
    
    async def send_to_user(self, user_id, message):
        """Send message to specific user (all connections)"""
        if user_id in self.active_connections:
            tasks = []
            for conn in self.active_connections[user_id]:
                tasks.append(conn.send(message))
            await asyncio.gather(*tasks, return_exceptions=True)
    
    async def broadcast_to_channel(self, channel, message, exclude_user=None):
        """Broadcast to all users in a channel"""
        tasks = []
        
        for user_id, channels in self.user_channels.items():
            if channel in channels and user_id != exclude_user:
                for conn in self.active_connections.get(user_id, []):
                    tasks.append(conn.send(message))
        
        await asyncio.gather(*tasks, return_exceptions=True)
    
    async def broadcast_presence(self, user_id, status, channel):
        """Broadcast user presence update"""
        message = {
            "type": "presence",
            "user_id": user_id,
            "status": status,
            "timestamp": datetime.now().isoformat()
        }
        await self.broadcast_to_channel(channel, message, exclude_user=user_id)
    
    def get_online_users(self, channel=None):
        """Get list of online users"""
        if channel:
            return [
                user_id for user_id, channels in self.user_channels.items()
                if channel in channels
            ]
        return list(self.active_connections.keys())
    
    async def cleanup_stale_connections(self):
        """Remove dead connections"""
        async with self.lock:
            to_remove = []
            
            for user_id, connections in self.active_connections.items():
                for conn in connections:
                    if not conn.is_alive():
                        to_remove.append((user_id, conn))
            
            for user_id, conn in to_remove:
                await self.disconnect(user_id, conn)
```

### 3. Message Delivery Guarantees

```python
class MessageQueue:
    """Queue for guaranteed message delivery"""
    
    def __init__(self):
        self.queues: Dict[str, asyncio.Queue] = {}
        self.persistence = MessagePersistence()
    
    async def enqueue(self, user_id, message):
        """Add message to user's queue"""
        # Ensure queue exists
        if user_id not in self.queues:
            self.queues[user_id] = asyncio.Queue()
        
        # Persist message
        msg_id = await self.persistence.save(user_id, message)
        message['id'] = msg_id
        
        await self.queues[user_id].put(message)
        logger.debug(f"Enqueued message {msg_id} for user {user_id}")
    
    async def dequeue(self, user_id):
        """Get next message for user"""
        if user_id not in self.queues:
            return None
        
        try:
            message = await asyncio.wait_for(
                self.queues[user_id].get(),
                timeout=0.1
            )
            return message
        except asyncio.TimeoutError:
            return None
    
    async def acknowledge(self, user_id, message_id):
        """Mark message as delivered"""
        await self.persistence.mark_delivered(message_id)
        logger.debug(f"Acknowledged message {message_id}")
    
    async def get_undelivered(self, user_id):
        """Get all undelivered messages for user"""
        return await self.persistence.get_undelivered(user_id)
    
    async def retry_failed(self):
        """Retry failed message deliveries"""
        failed = await self.persistence.get_failed_messages()
        
        for msg in failed:
            user_id = msg['user_id']
            await self.enqueue(user_id, msg['content'])

# Usage in WebSocket handler
async def websocket_handler(websocket, user_id):
    """Handle WebSocket connection with delivery guarantees"""
    conn_manager = get_connection_manager()
    msg_queue = get_message_queue()
    
    # Connect
    conn = await conn_manager.connect(websocket, user_id)
    
    # Send any queued messages
    undelivered = await msg_queue.get_undelivered(user_id)
    for msg in undelivered:
        await conn.send(msg)
        await msg_queue.acknowledge(user_id, msg['id'])
    
    try:
        while True:
            # Receive from client
            data = await conn.receive()
            if not data:
                break
            
            # Process message
            await process_message(data)
            
            # Check for outgoing messages
            msg = await msg_queue.dequeue(user_id)
            if msg:
                success = await conn.send(msg)
                if success:
                    await msg_queue.acknowledge(user_id, msg['id'])
    
    finally:
        await conn_manager.disconnect(user_id, conn)
```

### 4. Typing Indicators

```python
class TypingIndicatorManager:
    """Manage typing indicators"""
    
    def __init__(self):
        self.typing_users: Dict[str, Dict[str, float]] = {}
        self.timeout = 3.0  # 3 seconds
    
    def start_typing(self, user_id, channel):
        """User started typing"""
        if channel not in self.typing_users:
            self.typing_users[channel] = {}
        
        self.typing_users[channel][user_id] = time.time()
        
        return {
            "type": "typing_start",
            "user_id": user_id,
            "channel": channel
        }
    
    def stop_typing(self, user_id, channel):
        """User stopped typing"""
        if channel in self.typing_users:
            self.typing_users[channel].pop(user_id, None)
        
        return {
            "type": "typing_stop",
            "user_id": user_id,
            "channel": channel
        }
    
    def get_typing_users(self, channel):
        """Get currently typing users"""
        if channel not in self.typing_users:
            return []
        
        now = time.time()
        typing = []
        expired = []
        
        for user_id, timestamp in self.typing_users[channel].items():
            if now - timestamp < self.timeout:
                typing.append(user_id)
            else:
                expired.append(user_id)
        
        # Clean up expired
        for user_id in expired:
            del self.typing_users[channel][user_id]
        
        return typing
    
    async def cleanup_loop(self):
        """Periodically clean up expired typing indicators"""
        while True:
            await asyncio.sleep(1.0)
            
            for channel in list(self.typing_users.keys()):
                self.get_typing_users(channel)  # Triggers cleanup
```

## Advanced Authentication

### 1. OAuth 2.0 Integration

```python
from authlib.integrations.starlette_client import OAuth

# Configure OAuth
oauth = OAuth()

# Google OAuth
oauth.register(
    name='google',
    client_id='YOUR_CLIENT_ID',
    client_secret='YOUR_CLIENT_SECRET',
    server_metadata_url='https://accounts.google.com/.well-known/openid-configuration',
    client_kwargs={'scope': 'openid email profile'}
)

# GitHub OAuth
oauth.register(
    name='github',
    client_id='YOUR_CLIENT_ID',
    client_secret='YOUR_CLIENT_SECRET',
    access_token_url='https://github.com/login/oauth/access_token',
    authorize_url='https://github.com/login/oauth/authorize',
    api_base_url='https://api.github.com/',
    client_kwargs={'scope': 'user:email'}
)

# OAuth routes
@app.get('/auth/{provider}/login')
async def oauth_login(request: Request, provider: str):
    """Initiate OAuth login"""
    redirect_uri = request.url_for('oauth_callback', provider=provider)
    return await oauth.create_client(provider).authorize_redirect(request, redirect_uri)

@app.get('/auth/{provider}/callback')
async def oauth_callback(request: Request, provider: str):
    """Handle OAuth callback"""
    client = oauth.create_client(provider)
    token = await client.authorize_access_token(request)
    user_info = token.get('userinfo')
    
    # Create or get user
    user = await get_or_create_oauth_user(provider, user_info)
    
    # Generate JWT
    access_token = create_access_token({"sub": user.username})
    
    return {"access_token": access_token, "token_type": "bearer"}
```

### 2. SAML Integration (Enterprise)

```python
from onelogin.saml2.auth import OneLogin_Saml2_Auth

class SAMLAuth:
    """SAML 2.0 authentication"""
    
    def __init__(self, settings):
        self.settings = settings
    
    def initiate_login(self, request):
        """Start SAML login flow"""
        auth = OneLogin_Saml2_Auth(request, self.settings)
        return auth.login()
    
    def process_response(self, request):
        """Process SAML response"""
        auth = OneLogin_Saml2_Auth(request, self.settings)
        auth.process_response()
        
        if not auth.is_authenticated():
            raise AuthenticationError("SAML authentication failed")
        
        # Get user attributes
        attributes = auth.get_attributes()
        user_data = {
            "username": attributes.get("uid", [None])[0],
            "email": attributes.get("email", [None])[0],
            "name": attributes.get("name", [None])[0]
        }
        
        return user_data

# SAML settings
saml_settings = {
    "sp": {
        "entityId": "https://your-app.com/saml/metadata",
        "assertionConsumerService": {
            "url": "https://your-app.com/saml/acs",
            "binding": "urn:oasis:names:tc:SAML:2.0:bindings:HTTP-POST"
        }
    },
    "idp": {
        "entityId": "https://idp.example.com",
        "singleSignOnService": {
            "url": "https://idp.example.com/sso",
            "binding": "urn:oasis:names:tc:SAML:2.0:bindings:HTTP-Redirect"
        },
        "x509cert": "MIID..."
    }
}
```

### 3. Multi-Factor Authentication (MFA)

```python
import pyotp
import qrcode
from io import BytesIO

class MFAManager:
    """Manage multi-factor authentication"""
    
    def setup_totp(self, user_id, username):
        """Set up TOTP (Time-based One-Time Password)"""
        # Generate secret
        secret = pyotp.random_base32()
        
        # Store secret (encrypted)
        store_user_mfa_secret(user_id, secret)
        
        # Generate QR code for authenticator apps
        totp = pyotp.TOTP(secret)
        provisioning_uri = totp.provisioning_uri(
            name=username,
            issuer_name="Universal Chat System"
        )
        
        # Create QR code
        qr = qrcode.QRCode(version=1, box_size=10, border=5)
        qr.add_data(provisioning_uri)
        qr.make(fit=True)
        
        img = qr.make_image(fill_color="black", back_color="white")
        buffer = BytesIO()
        img.save(buffer, format='PNG')
        qr_code = buffer.getvalue()
        
        return {
            "secret": secret,
            "qr_code": qr_code,
            "provisioning_uri": provisioning_uri
        }
    
    def verify_totp(self, user_id, token):
        """Verify TOTP token"""
        secret = get_user_mfa_secret(user_id)
        if not secret:
            return False
        
        totp = pyotp.TOTP(secret)
        return totp.verify(token, valid_window=1)
    
    def setup_sms(self, user_id, phone_number):
        """Set up SMS-based MFA"""
        # Store phone number
        store_user_phone(user_id, phone_number)
        
        # Generate and send verification code
        code = self.generate_verification_code()
        send_sms(phone_number, f"Your verification code: {code}")
        
        # Store code temporarily
        store_verification_code(user_id, code, expires_in=300)  # 5 minutes
        
        return True
    
    def verify_sms(self, user_id, code):
        """Verify SMS code"""
        stored_code = get_verification_code(user_id)
        return stored_code and stored_code == code
    
    def generate_backup_codes(self, user_id, count=10):
        """Generate backup codes"""
        import secrets
        
        codes = []
        for _ in range(count):
            code = secrets.token_hex(4).upper()
            codes.append(code)
        
        # Store hashed codes
        store_backup_codes(user_id, codes)
        
        return codes
    
    def verify_backup_code(self, user_id, code):
        """Verify and consume backup code"""
        return consume_backup_code(user_id, code)

# MFA-protected login
@app.post("/auth/login")
async def login_with_mfa(username: str, password: str, mfa_token: str = None):
    """Login with MFA"""
    # Verify username/password
    user = authenticate_user(username, password)
    if not user:
        raise HTTPException(401, "Invalid credentials")
    
    # Check if MFA is enabled
    if user.mfa_enabled:
        if not mfa_token:
            return {
                "status": "mfa_required",
                "user_id": user.id
            }
        
        # Verify MFA token
        mfa = MFAManager()
        if not mfa.verify_totp(user.id, mfa_token):
            raise HTTPException(401, "Invalid MFA token")
    
    # Generate JWT
    access_token = create_access_token({"sub": user.username})
    return {"access_token": access_token, "token_type": "bearer"}
```

### 4. API Key Management

```python
import secrets

class APIKeyManager:
    """Manage API keys for programmatic access"""
    
    def generate_api_key(self, user_id, name, permissions=None):
        """Generate new API key"""
        # Generate secure key
        key = f"csk_{secrets.token_urlsafe(32)}"
        
        # Store hashed version
        api_key = {
            "key_hash": hash_api_key(key),
            "user_id": user_id,
            "name": name,
            "permissions": permissions or ["read"],
            "created_at": datetime.now(),
            "last_used": None,
            "expires_at": None
        }
        
        store_api_key(api_key)
        
        # Return actual key (only time it's shown)
        return {
            "key": key,
            "name": name,
            "permissions": permissions
        }
    
    def verify_api_key(self, key):
        """Verify API key and get associated user"""
        key_hash = hash_api_key(key)
        api_key = get_api_key_by_hash(key_hash)
        
        if not api_key:
            return None
        
        # Check expiration
        if api_key.get("expires_at"):
            if datetime.now() > api_key["expires_at"]:
                return None
        
        # Update last used
        update_api_key_last_used(key_hash)
        
        return {
            "user_id": api_key["user_id"],
            "permissions": api_key["permissions"]
        }
    
    def revoke_api_key(self, key_hash):
        """Revoke API key"""
        delete_api_key(key_hash)
    
    def list_user_keys(self, user_id):
        """List all API keys for a user"""
        return get_api_keys_by_user(user_id)

# API key authentication dependency
async def get_current_user_api(api_key: str = Header(..., alias="X-API-Key")):
    """Authenticate via API key"""
    manager = APIKeyManager()
    result = manager.verify_api_key(api_key)
    
    if not result:
        raise HTTPException(401, "Invalid API key")
    
    return result["user_id"]

# Protected API route
@app.get("/api/v1/data")
async def get_data(user_id: str = Depends(get_current_user_api)):
    """API endpoint protected by API key"""
    return {"data": "sensitive information", "user_id": user_id}
```

## Plugin System

### 1. Plugin Architecture

```python
from abc import ABC, abstractmethod

class Plugin(ABC):
    """Base plugin interface"""
    
    def __init__(self, config):
        self.config = config
        self.name = self.__class__.__name__
        self.version = "1.0.0"
        self.enabled = True
    
    @abstractmethod
    async def initialize(self):
        """Initialize plugin"""
        pass
    
    @abstractmethod
    async def execute(self, context):
        """Execute plugin logic"""
        pass
    
    @abstractmethod
    async def cleanup(self):
        """Cleanup resources"""
        pass
    
    def get_info(self):
        """Get plugin information"""
        return {
            "name": self.name,
            "version": self.version,
            "enabled": self.enabled
        }

class PluginManager:
    """Manage plugins"""
    
    def __init__(self):
        self.plugins: Dict[str, Plugin] = {}
        self.hooks: Dict[str, List[Plugin]] = {}
    
    def register(self, plugin: Plugin, hooks: List[str] = None):
        """Register a plugin"""
        self.plugins[plugin.name] = plugin
        
        # Register for hooks
        if hooks:
            for hook in hooks:
                if hook not in self.hooks:
                    self.hooks[hook] = []
                self.hooks[hook].append(plugin)
        
        logger.info(f"Registered plugin: {plugin.name}")
    
    async def initialize_all(self):
        """Initialize all plugins"""
        for plugin in self.plugins.values():
            try:
                await plugin.initialize()
                logger.info(f"Initialized: {plugin.name}")
            except Exception as e:
                logger.error(f"Failed to initialize {plugin.name}: {e}")
                plugin.enabled = False
    
    async def execute_hook(self, hook_name, context):
        """Execute all plugins registered for a hook"""
        if hook_name not in self.hooks:
            return context
        
        for plugin in self.hooks[hook_name]:
            if not plugin.enabled:
                continue
            
            try:
                context = await plugin.execute(context)
            except Exception as e:
                logger.error(f"Plugin {plugin.name} failed on {hook_name}: {e}")
        
        return context
    
    def get_plugin(self, name):
        """Get plugin by name"""
        return self.plugins.get(name)
    
    def list_plugins(self):
        """List all plugins"""
        return [p.get_info() for p in self.plugins.values()]
```

### 2. Example Plugin: Message Translator

```python
class TranslatorPlugin(Plugin):
    """Translate messages to multiple languages"""
    
    async def initialize(self):
        """Initialize translator"""
        from googletrans import Translator
        self.translator = Translator()
        self.target_languages = self.config.get("languages", ["es", "fr", "de"])
    
    async def execute(self, context):
        """Translate message"""
        message = context.get("message")
        if not message:
            return context
        
        # Detect source language
        detection = self.translator.detect(message["content"])
        source_lang = detection.lang
        
        # Translate to target languages
        translations = {}
        for lang in self.target_languages:
            if lang != source_lang:
                result = self.translator.translate(
                    message["content"],
                    src=source_lang,
                    dest=lang
                )
                translations[lang] = result.text
        
        # Add translations to message
        message["translations"] = translations
        context["message"] = message
        
        return context
    
    async def cleanup(self):
        """Cleanup"""
        pass

# Register plugin
plugin_manager = PluginManager()
translator = TranslatorPlugin({"languages": ["es", "fr", "de"]})
plugin_manager.register(translator, hooks=["message_created"])

# Use in message handler
async def handle_message(message):
    context = {"message": message}
    context = await plugin_manager.execute_hook("message_created", context)
    return context["message"]
```

### 3. Example Plugin: Sentiment Analysis

```python
class SentimentPlugin(Plugin):
    """Analyze message sentiment"""
    
    async def initialize(self):
        """Initialize sentiment analyzer"""
        from textblob import TextBlob
        self.analyzer = TextBlob
    
    async def execute(self, context):
        """Analyze sentiment"""
        message = context.get("message")
        if not message:
            return context
        
        # Analyze
        blob = self.analyzer(message["content"])
        sentiment = blob.sentiment
        
        # Add sentiment data
        message["sentiment"] = {
            "polarity": sentiment.polarity,  # -1 to 1
            "subjectivity": sentiment.subjectivity,  # 0 to 1
            "label": self._get_sentiment_label(sentiment.polarity)
        }
        
        context["message"] = message
        return context
    
    def _get_sentiment_label(self, polarity):
        """Convert polarity to label"""
        if polarity > 0.3:
            return "positive"
        elif polarity < -0.3:
            return "negative"
        else:
            return "neutral"
    
    async def cleanup(self):
        """Cleanup"""
        pass
```

## Workflow Automation

### 1. Workflow Engine

```python
class WorkflowStep:
    """Single workflow step"""
    
    def __init__(self, name, action, condition=None):
        self.name = name
        self.action = action
        self.condition = condition
    
    async def can_execute(self, context):
        """Check if step should execute"""
        if not self.condition:
            return True
        return await self.condition(context)
    
    async def execute(self, context):
        """Execute step"""
        if await self.can_execute(context):
            return await self.action(context)
        return context

class Workflow:
    """Workflow definition"""
    
    def __init__(self, name, trigger):
        self.name = name
        self.trigger = trigger
        self.steps: List[WorkflowStep] = []
    
    def add_step(self, name, action, condition=None):
        """Add step to workflow"""
        step = WorkflowStep(name, action, condition)
        self.steps.append(step)
        return self
    
    async def execute(self, context):
        """Execute all steps"""
        for step in self.steps:
            try:
                context = await step.execute(context)
            except Exception as e:
                logger.error(f"Workflow {self.name} failed at {step.name}: {e}")
                context["error"] = str(e)
                break
        
        return context

class WorkflowEngine:
    """Workflow execution engine"""
    
    def __init__(self):
        self.workflows: Dict[str, List[Workflow]] = {}
    
    def register(self, workflow: Workflow):
        """Register workflow for trigger"""
        trigger = workflow.trigger
        if trigger not in self.workflows:
            self.workflows[trigger] = []
        self.workflows[trigger].append(workflow)
    
    async def trigger(self, event_type, context):
        """Trigger workflows for event"""
        if event_type not in self.workflows:
            return
        
        for workflow in self.workflows[event_type]:
            try:
                await workflow.execute(context.copy())
            except Exception as e:
                logger.error(f"Workflow {workflow.name} failed: {e}")
```

### 2. Example Workflow: Auto-Ticket Creation

```python
# Create workflow
workflow = Workflow(
    name="auto_ticket_creation",
    trigger="message_with_bug_keyword"
)

# Step 1: Extract bug details
async def extract_bug_details(context):
    message = context["message"]
    
    # Use AI to extract structured data
    ai_service = get_ai_service()
    prompt = f"""Extract bug details from this message:
{message['content']}

Return JSON with: title, description, severity, steps_to_reproduce"""
    
    response = await ai_service.generate(prompt, model="gpt-3.5-turbo")
    bug_details = json.loads(response.content)
    
    context["bug_details"] = bug_details
    return context

workflow.add_step("extract_details", extract_bug_details)

# Step 2: Create ticket
async def create_bug_ticket(context):
    bug_details = context["bug_details"]
    message = context["message"]
    
    ticket_service = get_ticket_service()
    ticket = await ticket_service.create_ticket(
        title=bug_details["title"],
        description=bug_details["description"],
        type="bug",
        priority=bug_details.get("severity", "medium"),
        reporter_id=message["user_id"],
        metadata={
            "message_id": message["id"],
            "steps_to_reproduce": bug_details.get("steps_to_reproduce")
        }
    )
    
    context["ticket"] = ticket
    return context

workflow.add_step("create_ticket", create_bug_ticket)

# Step 3: Notify team
async def notify_team(context):
    ticket = context["ticket"]
    
    notification = {
        "type": "bug_reported",
        "ticket_id": ticket["id"],
        "title": ticket["title"],
        "priority": ticket["priority"]
    }
    
    # Send to team channel
    conn_manager = get_connection_manager()
    await conn_manager.broadcast_to_channel("team", notification)
    
    return context

workflow.add_step("notify", notify_team)

# Register workflow
engine = WorkflowEngine()
engine.register(workflow)

# Trigger when bug keyword detected
async def on_message(message):
    if any(keyword in message["content"].lower() 
           for keyword in ["bug", "error", "crash", "broken"]):
        await engine.trigger("message_with_bug_keyword", {"message": message})
```

### 3. Example Workflow: Scheduled Reports

```python
from apscheduler.schedulers.asyncio import AsyncIOScheduler

# Create scheduler
scheduler = AsyncIOScheduler()

# Daily report workflow
async def generate_daily_report():
    """Generate and send daily report"""
    # Gather metrics
    stats = {
        "messages": await get_message_count(today()),
        "active_users": await get_active_user_count(today()),
        "ai_requests": await get_ai_request_count(today()),
        "tickets_created": await get_ticket_count(today()),
        "tickets_resolved": await get_resolved_ticket_count(today())
    }
    
    # Generate report
    report = f"""Daily Report - {today().strftime('%Y-%m-%d')}

📊 Statistics:
- Messages: {stats['messages']}
- Active Users: {stats['active_users']}
- AI Requests: {stats['ai_requests']}
- Tickets Created: {stats['tickets_created']}
- Tickets Resolved: {stats['tickets_resolved']}

📈 Trends:
- Message growth: {calculate_growth('messages')}%
- User engagement: {calculate_engagement()}%
"""
    
    # Send report
    await send_report_to_channel("reports", report)
    await email_report_to_admins(report)

# Schedule daily at 9 AM
scheduler.add_job(
    generate_daily_report,
    'cron',
    hour=9,
    minute=0
)

scheduler.start()
```

## Performance Monitoring

### 1. Metrics Collection

```python
from prometheus_client import Counter, Histogram, Gauge
import time

# Define metrics
request_count = Counter(
    'http_requests_total',
    'Total HTTP requests',
    ['method', 'endpoint', 'status']
)

request_duration = Histogram(
    'http_request_duration_seconds',
    'HTTP request duration',
    ['method', 'endpoint']
)

websocket_connections = Gauge(
    'websocket_connections_active',
    'Active WebSocket connections'
)

ai_request_duration = Histogram(
    'ai_request_duration_seconds',
    'AI request duration',
    ['model']
)

# Middleware for tracking
@app.middleware("http")
async def metrics_middleware(request, call_next):
    """Track request metrics"""
    start_time = time.time()
    
    response = await call_next(request)
    
    duration = time.time() - start_time
    
    # Record metrics
    request_count.labels(
        method=request.method,
        endpoint=request.url.path,
        status=response.status_code
    ).inc()
    
    request_duration.labels(
        method=request.method,
        endpoint=request.url.path
    ).observe(duration)
    
    return response
```

### 2. Custom Monitoring

```python
class PerformanceMonitor:
    """Custom performance monitoring"""
    
    def __init__(self):
        self.metrics = {}
        self.alerts = []
    
    def track_metric(self, name, value, tags=None):
        """Track custom metric"""
        if name not in self.metrics:
            self.metrics[name] = []
        
        self.metrics[name].append({
            "value": value,
            "timestamp": datetime.now(),
            "tags": tags or {}
        })
    
    def get_average(self, name, window_seconds=3600):
        """Get average over time window"""
        if name not in self.metrics:
            return 0
        
        cutoff = datetime.now() - timedelta(seconds=window_seconds)
        recent = [
            m["value"] for m in self.metrics[name]
            if m["timestamp"] > cutoff
        ]
        
        return sum(recent) / len(recent) if recent else 0
    
    def check_thresholds(self):
        """Check if metrics exceed thresholds"""
        thresholds = {
            "response_time": 1.0,  # 1 second
            "error_rate": 0.05,    # 5%
            "memory_usage": 0.90   # 90%
        }
        
        for metric, threshold in thresholds.items():
            avg = self.get_average(metric)
            if avg > threshold:
                self.alert(f"{metric} exceeded threshold: {avg} > {threshold}")
    
    def alert(self, message):
        """Send alert"""
        logger.warning(f"ALERT: {message}")
        self.alerts.append({
            "message": message,
            "timestamp": datetime.now()
        })
        
        # Send notification (email, Slack, etc.)
        send_alert_notification(message)
```

## Advanced Security

### 1. Rate Limiting

```python
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address

# Initialize rate limiter
limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# Apply rate limits
@app.post("/api/v1/messages")
@limiter.limit("60/minute")  # 60 requests per minute
async def send_message(request: Request, message: MessageCreate):
    """Rate-limited message endpoint"""
    return await create_message(message)

@app.post("/api/v1/ai/generate")
@limiter.limit("10/minute")  # 10 AI requests per minute
async def generate_ai(request: Request, prompt: str):
    """Rate-limited AI endpoint"""
    return await ai_generate(prompt)

# Custom rate limiting per user
class UserRateLimiter:
    """Per-user rate limiting"""
    
    def __init__(self):
        self.limits = {}
        self.reset_interval = 60  # seconds
    
    def check_limit(self, user_id, limit):
        """Check if user is within rate limit"""
        now = time.time()
        
        if user_id not in self.limits:
            self.limits[user_id] = {
                "count": 0,
                "reset_at": now + self.reset_interval
            }
        
        user_limit = self.limits[user_id]
        
        # Reset if interval passed
        if now > user_limit["reset_at"]:
            user_limit["count"] = 0
            user_limit["reset_at"] = now + self.reset_interval
        
        # Check limit
        if user_limit["count"] >= limit:
            raise RateLimitExceeded(f"Rate limit exceeded: {limit}/minute")
        
        user_limit["count"] += 1
        return True
```

### 2. Input Validation

```python
from pydantic import BaseModel, validator, Field
import re

class SecureMessageCreate(BaseModel):
    """Validated message input"""
    
    content: str = Field(..., min_length=1, max_length=10000)
    channel: str = Field(..., pattern=r'^[a-z0-9_-]+$')
    
    @validator('content')
    def validate_content(cls, v):
        """Validate message content"""
        # Check for SQL injection patterns
        sql_patterns = [
            r'(\bUNION\b|\bSELECT\b|\bDROP\b|\bDELETE\b)',
            r'(--|\/\*|\*\/)',
            r'(\bOR\b.*=.*\bOR\b)'
        ]
        
        for pattern in sql_patterns:
            if re.search(pattern, v, re.IGNORECASE):
                raise ValueError("Potentially malicious content detected")
        
        # Check for XSS patterns
        xss_patterns = [
            r'<script[^>]*>.*?</script>',
            r'javascript:',
            r'on\w+\s*=',
        ]
        
        for pattern in xss_patterns:
            if re.search(pattern, v, re.IGNORECASE):
                raise ValueError("Potentially malicious content detected")
        
        return v
    
    @validator('channel')
    def validate_channel(cls, v):
        """Validate channel name"""
        if len(v) < 1 or len(v) > 50:
            raise ValueError("Channel name must be 1-50 characters")
        return v.lower()
```

### 3. Audit Logging

```python
class AuditLogger:
    """Security audit logging"""
    
    def __init__(self):
        self.logger = logging.getLogger("audit")
    
    def log_auth_attempt(self, username, success, ip_address, metadata=None):
        """Log authentication attempt"""
        self.logger.info(
            "AUTH_ATTEMPT",
            extra={
                "event": "authentication",
                "username": username,
                "success": success,
                "ip_address": ip_address,
                "timestamp": datetime.now().isoformat(),
                "metadata": metadata or {}
            }
        )
    
    def log_permission_check(self, user_id, resource, action, granted):
        """Log permission check"""
        self.logger.info(
            "PERMISSION_CHECK",
            extra={
                "event": "permission",
                "user_id": user_id,
                "resource": resource,
                "action": action,
                "granted": granted,
                "timestamp": datetime.now().isoformat()
            }
        )
    
    def log_data_access(self, user_id, resource_type, resource_id, action):
        """Log data access"""
        self.logger.info(
            "DATA_ACCESS",
            extra={
                "event": "data_access",
                "user_id": user_id,
                "resource_type": resource_type,
                "resource_id": resource_id,
                "action": action,
                "timestamp": datetime.now().isoformat()
            }
        )
```

## Scalability Features

### 1. Load Balancing

```python
# Load balancer configuration
from fastapi import FastAPI
import uvicorn

# Worker configuration
workers = 4  # Number of worker processes

# Start with multiple workers
if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        workers=workers,
        log_level="info"
    )

# Nginx configuration for load balancing
"""
upstream chat_backend {
    least_conn;  # Use least connections algorithm
    server 127.0.0.1:8001;
    server 127.0.0.1:8002;
    server 127.0.0.1:8003;
    server 127.0.0.1:8004;
}

server {
    listen 80;
    server_name chat.example.com;
    
    location / {
        proxy_pass http://chat_backend;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
    
    location /ws {
        proxy_pass http://chat_backend;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }
}
"""
```

### 2. Caching Layer

```python
import redis
from functools import wraps

class CacheManager:
    """Distributed cache management"""
    
    def __init__(self):
        self.redis = redis.Redis(host='localhost', port=6379, decode_responses=True)
        self.default_ttl = 3600  # 1 hour
    
    def get(self, key):
        """Get from cache"""
        value = self.redis.get(key)
        if value:
            return json.loads(value)
        return None
    
    def set(self, key, value, ttl=None):
        """Set in cache"""
        ttl = ttl or self.default_ttl
        self.redis.setex(key, ttl, json.dumps(value))
    
    def delete(self, key):
        """Delete from cache"""
        self.redis.delete(key)
    
    def cache_decorator(self, ttl=None):
        """Decorator for caching function results"""
        def decorator(func):
            @wraps(func)
            async def wrapper(*args, **kwargs):
                # Generate cache key
                key = f"{func.__name__}:{str(args)}:{str(kwargs)}"
                
                # Check cache
                cached = self.get(key)
                if cached is not None:
                    return cached
                
                # Execute function
                result = await func(*args, **kwargs)
                
                # Store in cache
                self.set(key, result, ttl)
                
                return result
            
            return wrapper
        return decorator

# Usage
cache = CacheManager()

@cache.cache_decorator(ttl=300)  # Cache for 5 minutes
async def get_user_profile(user_id):
    """Get user profile (cached)"""
    return await db.get_user(user_id)
```

### 3. Database Sharding

```python
class ShardManager:
    """Manage database sharding"""
    
    def __init__(self, shard_count=4):
        self.shard_count = shard_count
        self.shards = [
            create_engine(f"postgresql://...db_shard_{i}")
            for i in range(shard_count)
        ]
    
    def get_shard(self, key):
        """Get shard for key"""
        shard_id = hash(key) % self.shard_count
        return self.shards[shard_id]
    
    async def insert(self, table, data, shard_key):
        """Insert into appropriate shard"""
        shard = self.get_shard(shard_key)
        async with shard.begin() as conn:
            await conn.execute(table.insert().values(**data))
    
    async def query(self, table, shard_key, **filters):
        """Query from appropriate shard"""
        shard = self.get_shard(shard_key)
        async with shard.begin() as conn:
            result = await conn.execute(
                table.select().where(**filters)
            )
            return result.fetchall()
    
    async def query_all_shards(self, table, **filters):
        """Query all shards and combine results"""
        results = []
        
        for shard in self.shards:
            async with shard.begin() as conn:
                result = await conn.execute(
                    table.select().where(**filters)
                )
                results.extend(result.fetchall())
        
        return results
```

## Next Steps

- **[Examples Directory](examples/)** - Practical code examples
- **[API Reference](docs/04-api-reference/README.md)** - Complete API documentation
- **[Operations Guide](docs/06-operations/README.md)** - Deployment and operations
- **[Architecture Documentation](docs/05-architecture/README.md)** - System architecture

---

**Need Help?** Check the [documentation](docs/) or [open an issue](https://github.com/Thomas-Heisig/chat_system/issues).
