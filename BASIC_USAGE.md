# Basic Usage Guide

**Version:** 2.0.0  
**Last Updated:** 2025-12-06  
**Estimated Reading Time:** 25 minutes

## 📋 Table of Contents

- [Chat System Lifecycle](#chat-system-lifecycle)
- [User Management](#user-management)
- [Messaging Operations](#messaging-operations)
- [File Management](#file-management)
- [Search and Filtering](#search-and-filtering)
- [Common Workflows](#common-workflows)
- [Best Practices](#best-practices)

## Chat System Lifecycle

### System Initialization

The chat system follows a structured lifecycle from startup to shutdown:

#### 1. Startup Sequence

```python
# Server startup process
1. Load configuration from .env
2. Initialize database connection
3. Create tables if not exists
4. Load AI models (if enabled)
5. Initialize RAG system (if enabled)
6. Start WebSocket manager
7. Begin HTTP server
8. Ready to accept connections
```

#### 2. Connection Flow

```
Client -> HTTP Request -> Authentication -> JWT Token
      -> WebSocket Connection -> Connection Manager
      -> Message Handler -> AI/RAG Processing -> Response
```

#### 3. Shutdown Sequence

```bash
# Graceful shutdown
1. Stop accepting new connections
2. Complete in-flight requests
3. Close WebSocket connections
4. Flush message queues
5. Close database connections
6. Save state (if needed)
7. Exit
```

### Starting the Server

```bash
# Standard mode
python main.py

# Production mode with Uvicorn
uvicorn main:app --host 0.0.0.0 --port 8000 --workers 4

# Development mode with auto-reload
uvicorn main:app --reload --log-level debug

# Docker mode
docker-compose up -d
```

### Stopping the Server

```bash
# Graceful shutdown (Ctrl+C)
^C

# Or send SIGTERM
kill -TERM $(pgrep -f "python main.py")

# Docker stop
docker-compose down
```

## User Management

### Creating Users

#### Via Web Interface

1. Login as admin
2. Navigate to **Users** tab
3. Click **Add User**
4. Fill in details:
   - Username
   - Email
   - Password
   - Role (User, Moderator, Manager, Admin)
5. Click **Create**

#### Via API

```bash
curl -X POST http://localhost:8000/api/v1/users \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "username": "newuser",
    "email": "newuser@example.com",
    "password": "SecurePassword123!",
    "role": "user"
  }'
```

#### Via Python Script

```python
from database.repositories import UserRepository
from database.models import UserRole

repo = UserRepository()
user = repo.create_user(
    username="newuser",
    email="newuser@example.com",
    password="SecurePassword123!",
    role=UserRole.USER
)
print(f"Created user: {user.username}")
```

### User Roles

**Admin**: Full system access
- User management
- System configuration
- All features unlocked

**Manager**: Project and team management
- Create projects
- Assign tasks
- View analytics

**Moderator**: Content moderation
- Review messages
- Manage files
- Basic user management

**User**: Standard access
- Send messages
- Upload files (with limits)
- Create tickets

### Password Management

#### Change Password

```bash
# Via web interface
Settings -> Security -> Change Password

# Via API
curl -X PUT http://localhost:8000/api/v1/users/me/password \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "current_password": "OldPassword123!",
    "new_password": "NewPassword123!"
  }'
```

#### Reset Password (Admin)

```python
from database.repositories import UserRepository

repo = UserRepository()
repo.reset_user_password(
    username="targetuser",
    new_password="TempPassword123!",
    force_change=True  # User must change on next login
)
```

## Messaging Operations

### Sending Messages

#### Text Messages

```python
# Via WebSocket
{
  "type": "chat_message",
  "content": "Hello, world!",
  "channel": "general"
}
```

```bash
# Via REST API
curl -X POST http://localhost:8000/api/v1/messages \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "content": "Hello, world!",
    "channel": "general"
  }'
```

#### Messages with AI

```python
# AI-enabled message
{
  "type": "chat_message",
  "content": "What is artificial intelligence?",
  "use_ai": true,
  "model": "llama2"
}
```

#### Rich Messages

```python
# Message with formatting
{
  "type": "chat_message",
  "content": "**Bold** and *italic* text",
  "format": "markdown"
}

# Code snippet
{
  "type": "chat_message",
  "content": "```python\nprint('Hello')\n```",
  "format": "markdown"
}
```

### Receiving Messages

#### WebSocket Listener

```javascript
// JavaScript client
const ws = new WebSocket('ws://localhost:8000/ws');

ws.onmessage = (event) => {
  const message = JSON.parse(event.data);
  console.log('Received:', message);
  
  // Handle different message types
  switch(message.type) {
    case 'chat_message':
      displayChatMessage(message);
      break;
    case 'system_notification':
      showNotification(message);
      break;
    case 'ai_response':
      displayAIResponse(message);
      break;
  }
};
```

#### REST API Polling

```bash
# Get recent messages
curl http://localhost:8000/api/v1/messages?limit=50 \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"

# Get messages since timestamp
curl "http://localhost:8000/api/v1/messages?since=2025-12-06T00:00:00Z" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"
```

### Message History

#### Retrieve History

```bash
# Last 100 messages
curl http://localhost:8000/api/v1/messages?limit=100 \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"

# Paginated results
curl "http://localhost:8000/api/v1/messages?page=1&per_page=50" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"

# Filter by channel
curl "http://localhost:8000/api/v1/messages?channel=general" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"
```

#### Search Messages

```bash
# Search by content
curl "http://localhost:8000/api/v1/messages/search?q=python" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"

# Search by user
curl "http://localhost:8000/api/v1/messages?user_id=123" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"

# Date range
curl "http://localhost:8000/api/v1/messages?start=2025-12-01&end=2025-12-06" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"
```

### Message Analysis

```python
from database.repositories import MessageRepository

repo = MessageRepository()

# Get message statistics
stats = repo.get_message_stats(
    start_date="2025-12-01",
    end_date="2025-12-06"
)

print(f"Total messages: {stats['total']}")
print(f"AI messages: {stats['ai_messages']}")
print(f"Users active: {stats['active_users']}")
```

## File Management

### Uploading Files

#### Via Web Interface

1. Click file upload button (📎)
2. Select file(s)
3. Add optional description
4. Click Upload
5. Wait for processing

#### Via API

```bash
curl -X POST http://localhost:8000/api/v1/files \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -F "file=@document.pdf" \
  -F "description=Important document"
```

#### Supported File Types

**Documents**: PDF, DOCX, DOC, TXT, MD, RTF  
**Images**: JPG, PNG, GIF, BMP, SVG  
**Archives**: ZIP, TAR, GZ  
**Data**: CSV, JSON, XML  
**Code**: PY, JS, HTML, CSS, etc.

### File Limits

```bash
# Default limits (configurable)
MAX_FILE_SIZE=10MB          # Single file
MAX_TOTAL_SIZE=100MB        # Per user
MAX_FILES_PER_UPLOAD=10     # Batch upload
```

### File Organization

```
uploads/
├── users/
│   ├── user123/
│   │   ├── documents/
│   │   ├── images/
│   │   └── archives/
├── projects/
│   ├── project456/
│   │   └── attachments/
└── temporary/
    └── processing/
```

### File Operations

#### List Files

```bash
# List user files
curl http://localhost:8000/api/v1/files \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"

# Filter by type
curl "http://localhost:8000/api/v1/files?type=document" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"

# Search files
curl "http://localhost:8000/api/v1/files/search?q=budget" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"
```

#### Download Files

```bash
# Download file
curl -O http://localhost:8000/api/v1/files/123/download \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"

# Get file metadata
curl http://localhost:8000/api/v1/files/123 \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"
```

#### Delete Files

```bash
# Delete single file
curl -X DELETE http://localhost:8000/api/v1/files/123 \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"

# Bulk delete
curl -X DELETE http://localhost:8000/api/v1/files/bulk \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"file_ids": [123, 456, 789]}'
```

### Document Processing (RAG)

When RAG is enabled, documents are automatically processed:

```python
# Upload triggers:
1. File upload accepted
2. Text extraction (PDF/DOCX)
3. Chunking (configurable size)
4. Embedding generation
5. Vector storage
6. Indexing complete
7. Ready for retrieval
```

## Search and Filtering

### Message Search

#### Full-Text Search

```bash
# Search messages
curl "http://localhost:8000/api/v1/search?q=python+tutorial" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"

# Advanced search
curl "http://localhost:8000/api/v1/search" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "machine learning",
    "filters": {
      "type": "message",
      "date_from": "2025-12-01",
      "date_to": "2025-12-06",
      "user_id": 123
    },
    "sort": "relevance"
  }'
```

#### Semantic Search (RAG)

```bash
# Semantic document search
curl "http://localhost:8000/api/v1/rag/search?query=explain+neural+networks" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"

# Returns most relevant document chunks with similarity scores
```

### Filtering Options

```python
# Available filters
{
  "date_range": ["2025-12-01", "2025-12-06"],
  "user_ids": [123, 456],
  "channels": ["general", "technical"],
  "has_attachments": true,
  "message_type": ["user", "ai"],
  "min_length": 10,
  "max_length": 1000
}
```

## Common Workflows

### Workflow 1: Daily Team Standup

```bash
# 1. Start of day
# Users join chat

# 2. Moderator posts standup questions
"What did you do yesterday?"
"What will you do today?"
"Any blockers?"

# 3. Team members respond
# Messages automatically logged

# 4. AI summarizes (optional)
"@ai summarize today's standup"

# 5. Summary posted to project board
```

### Workflow 2: Document Q&A

```bash
# 1. Upload document
curl -X POST http://localhost:8000/api/v1/files \
  -F "file=@technical_spec.pdf"

# 2. Wait for RAG processing
# (automatic, ~5-30 seconds)

# 3. Ask questions
"What are the technical requirements?"
"Explain the architecture diagram."
"What's the deployment process?"

# 4. AI responds with document context
# (includes citations and relevant excerpts)
```

### Workflow 3: Project Task Management

```bash
# 1. Create project
curl -X POST http://localhost:8000/api/v1/projects \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Website Redesign",
    "description": "Q1 2025 redesign project"
  }'

# 2. Create tickets
curl -X POST http://localhost:8000/api/v1/tickets \
  -d '{
    "project_id": 123,
    "title": "Update homepage design",
    "type": "task",
    "priority": "high",
    "assignee_id": 456
  }'

# 3. Track progress
# Users update ticket status
# Chat discussions linked to tickets

# 4. Generate reports
curl http://localhost:8000/api/v1/projects/123/report
```

### Workflow 4: AI-Assisted Development

```bash
# 1. Ask for code help
"How do I implement JWT authentication in Python?"

# 2. AI provides code example
# (syntax highlighted, with explanations)

# 3. Ask follow-up questions
"How do I handle token refresh?"
"What about CORS configuration?"

# 4. Save useful responses
# (bookmark feature or copy to docs)
```

## Best Practices

### Messaging Best Practices

1. **Use Clear, Descriptive Messages**
   ```
   ❌ "It's broken"
   ✅ "Login form returns 500 error when submitting"
   ```

2. **Tag Appropriately**
   ```
   @user - Direct mention
   @ai - Invoke AI assistant
   #tag - Topic classification
   ```

3. **Format Code Properly**
   ````
   Use triple backticks for code:
   ```python
   def hello():
       return "world"
   ```
   ````

4. **Respect Rate Limits**
   ```
   - Max 60 messages/minute
   - Max 10 AI requests/minute
   - Max 5 file uploads/minute
   ```

### File Management Best Practices

1. **Organize Files**
   - Use descriptive names
   - Add descriptions
   - Tag appropriately

2. **Optimize File Sizes**
   - Compress images
   - Use PDF instead of DOCX for final docs
   - Archive old files

3. **Security**
   - Don't upload sensitive data
   - Use encrypted channels for confidential files
   - Set appropriate permissions

### Performance Optimization

1. **Message Retrieval**
   ```python
   # ❌ Don't retrieve all messages
   messages = get_all_messages()
   
   # ✅ Use pagination
   messages = get_messages(page=1, per_page=50)
   ```

2. **WebSocket Connections**
   ```python
   # ✅ Reuse connections
   # ❌ Create new connection per message
   ```

3. **AI Usage**
   ```python
   # ❌ Don't send every message to AI
   # ✅ Only invoke AI when needed (@ai or button)
   ```

### Security Best Practices

1. **Authentication**
   - Use strong passwords
   - Enable 2FA (if available)
   - Rotate JWT tokens regularly

2. **Data Privacy**
   - Don't share JWT tokens
   - Clear session on logout
   - Don't log sensitive data

3. **Access Control**
   - Use least privilege principle
   - Audit user permissions regularly
   - Review access logs

## Monitoring and Analytics

### System Health

```bash
# Check system status
curl http://localhost:8000/api/v1/health

# Detailed metrics
curl http://localhost:8000/api/v1/metrics \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"
```

### Usage Analytics

```python
# View dashboard
Web Interface -> Monitoring Tab

# Metrics available:
- Active users
- Messages per day
- AI usage
- Storage usage
- Response times
- Error rates
```

### Log Analysis

```bash
# View logs
tail -f logs/chat_system.log

# Search logs
grep ERROR logs/chat_system.log

# Structured query
python -c "from analytics import get_error_summary; print(get_error_summary())"
```

## Troubleshooting Common Issues

### Connection Issues

**Problem**: WebSocket disconnects frequently

```bash
# Check network stability
ping localhost

# Increase timeout
WEBSOCKET_TIMEOUT=300  # 5 minutes

# Check firewall rules
```

### Performance Issues

**Problem**: Slow message delivery

```bash
# Check database performance
python -c "from database.performance_monitor import run_diagnostics; run_diagnostics()"

# Add indexes if needed
# Check message queue size
# Scale workers if needed
```

### AI Issues

**Problem**: AI not responding or slow

```bash
# Check Ollama status
curl http://localhost:11434/api/tags

# Restart Ollama
systemctl restart ollama

# Use different model
DEFAULT_MODEL=llama2:7b  # Smaller, faster model
```

## Next Steps

- **[AI_INTEGRATION.md](AI_INTEGRATION.md)** - Learn about AI and RAG features
- **[ADVANCED_FEATURES.md](ADVANCED_FEATURES.md)** - Explore advanced capabilities
- **[KNOWLEDGE_DATABASE.md](KNOWLEDGE_DATABASE.md)** - Deep dive into RAG system
- **[TASK_SYSTEM.md](TASK_SYSTEM.md)** - Master project and ticket management

---

**Need Help?** Check the [documentation](docs/) or [open an issue](https://github.com/Thomas-Heisig/chat_system/issues).
