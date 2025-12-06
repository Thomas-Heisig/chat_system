# Universal Chat System - Examples

This directory contains comprehensive example scripts demonstrating various features and capabilities of the Universal Chat System.

## 📋 Table of Contents

- [Overview](#overview)
- [Setup](#setup)
- [Example Scripts](#example-scripts)
- [Running Examples](#running-examples)
- [Common Patterns](#common-patterns)
- [Troubleshooting](#troubleshooting)

## Overview

These examples demonstrate:
- **AI Integration**: Working with Ollama and OpenAI models
- **RAG System**: Document processing and knowledge-based Q&A
- **WebSocket Communication**: Real-time messaging and presence
- **Authentication**: JWT-based authentication
- **Error Handling**: Robust error handling patterns

## Setup

### Prerequisites

1. **Chat System Running**
   ```bash
   # Start the chat system
   python main.py
   
   # Or with Docker
   docker-compose up
   ```

2. **Install Dependencies**
   ```bash
   # Core dependencies (should already be installed)
   pip install -r requirements.txt
   
   # Additional for examples
   pip install aiohttp websockets
   ```

3. **Configuration**
   ```bash
   # Copy example environment file
   cp .env.example .env
   
   # Edit .env to enable features:
   # - OLLAMA_ENABLED=true (for AI examples)
   # - RAG_ENABLED=true (for RAG examples)
   # - RAG_VECTOR_DB=chromadb
   ```

4. **Optional: Install Ollama**
   ```bash
   # For AI examples
   curl https://ollama.ai/install.sh | sh
   ollama pull llama2
   ```

## Example Scripts

### 1. ai_chat_example.py

**Purpose**: Demonstrates AI integration with the chat system

**Features**:
- Basic AI chat
- Model comparison
- Streaming responses
- Code generation
- Multi-turn conversations
- Error handling
- Interactive chat session

**Usage**:
```bash
python examples/ai_chat_example.py
```

**Examples Included**:
- **Example 1**: Basic AI Chat - Simple question and answer
- **Example 2**: Model Comparison - Compare different AI models
- **Example 3**: Streaming Responses - Token-by-token output
- **Example 4**: Code Generation - Generate code with AI
- **Example 5**: Multi-Turn Conversation - Context-aware dialogue
- **Example 6**: Error Handling - Handle various error scenarios
- **Example 7**: Interactive Chat - Full interactive session

**Code Snippet**:
```python
async with AIChatExample() as chat:
    await chat.authenticate("admin", "admin")
    
    response = await chat.send_message(
        "What is Python?",
        model="llama2",
        temperature=0.7
    )
    
    print(f"AI: {response['response']}")
```

### 2. rag_document_example.py

**Purpose**: Demonstrates RAG (Retrieval-Augmented Generation) system

**Features**:
- Document upload and processing
- Semantic search
- RAG-enhanced Q&A
- Document management
- Batch upload
- Interactive RAG session

**Usage**:
```bash
python examples/rag_document_example.py
```

**Examples Included**:
- **Example 1**: Upload and Process Document - Document ingestion
- **Example 2**: Semantic Search - Find relevant document chunks
- **Example 3**: RAG-Enhanced Q&A - Ask questions with document context
- **Example 4**: Document Management - List, view, delete documents
- **Example 5**: Batch Upload - Upload multiple documents
- **Example 6**: Interactive RAG Session - Full interactive Q&A

**Code Snippet**:
```python
async with RAGDocumentExample() as rag:
    await rag.authenticate("admin", "admin")
    
    # Upload document
    result = await rag.upload_document(
        "document.pdf",
        title="My Document",
        tags=["important"]
    )
    
    # Ask question
    response = await rag.ask_question(
        "What does the document say about X?"
    )
    
    print(f"Answer: {response['answer']}")
    print(f"Sources: {response['sources']}")
```

### 3. websocket_client_example.py

**Purpose**: Demonstrates WebSocket real-time communication

**Features**:
- WebSocket connection
- Real-time messaging
- User presence tracking
- Typing indicators
- Multi-channel communication
- AI message integration
- Error handling and reconnection
- Interactive chat client

**Usage**:
```bash
python examples/websocket_client_example.py
```

**Examples Included**:
- **Example 1**: Basic Chat Messaging - Send/receive messages
- **Example 2**: User Presence Tracking - Track online users
- **Example 3**: Typing Indicators - Show typing status
- **Example 4**: Multi-Channel Communication - Multiple channels
- **Example 5**: AI Integration - AI messages via WebSocket
- **Example 6**: Error Handling - Reconnection logic
- **Example 7**: File Sharing - File share notifications
- **Example 8**: Interactive Chat - Full chat client

**Code Snippet**:
```python
client = WebSocketClient()

# Define message handler
async def on_message(data):
    print(f"{data['username']}: {data['content']}")

client.on("chat_message", on_message)

# Connect and send
await client.authenticate("admin", "admin")
await client.connect("general")
await client.send_message("Hello, World!")
```

## Running Examples

### Interactive Mode

All example scripts have an interactive menu:

```bash
# Run and select from menu
python examples/ai_chat_example.py

# Menu appears:
# 1. Basic AI Chat
# 2. Model Comparison
# ...
# Enter choice (1-8) [8]:
```

### Programmatic Usage

You can also import and use the example classes in your own scripts:

```python
from examples.ai_chat_example import AIChatExample

async def my_function():
    async with AIChatExample() as chat:
        await chat.authenticate("user", "pass")
        response = await chat.send_message("Hello!")
        print(response)
```

### Running All Examples

```bash
# Run all examples in sequence
python examples/ai_chat_example.py  # Choose option 8
python examples/rag_document_example.py  # Choose option 7
python examples/websocket_client_example.py  # Choose option 9
```

## Common Patterns

### 1. Authentication Pattern

All examples use the same authentication pattern:

```python
async with ExampleClass() as client:
    await client.authenticate("username", "password")
    # Use client methods
```

### 2. Error Handling Pattern

```python
try:
    await client.some_operation()
except Exception as e:
    print(f"Error: {e}")
    # Handle or retry
```

### 3. Async Context Manager Pattern

```python
async with ExampleClass() as client:
    # Automatic setup
    await client.do_something()
    # Automatic cleanup
```

### 4. Event Handler Pattern

```python
async def my_handler(data):
    print(f"Received: {data}")

client.on("event_type", my_handler)
```

## Configuration

### Environment Variables

Examples read from the same `.env` file as the main application:

```bash
# API Settings
HOST=localhost
PORT=8000

# Authentication
ADMIN_PASSWORD=admin

# AI Configuration
OLLAMA_ENABLED=true
OLLAMA_BASE_URL=http://localhost:11434
DEFAULT_MODEL=llama2

# RAG Configuration
RAG_ENABLED=true
VECTOR_DB_TYPE=chromadb
CHUNK_SIZE=1000
```

### Example-Specific Settings

You can override settings when initializing example classes:

```python
# Custom base URL
client = AIChatExample(base_url="http://192.168.1.100:8000")

# Custom API key (skip authentication)
client = AIChatExample(api_key="your-jwt-token")
```

## Advanced Usage

### Combining Examples

You can combine multiple example patterns:

```python
async def combined_example():
    # Setup AI client
    async with AIChatExample() as ai_chat:
        await ai_chat.authenticate("admin", "admin")
        
        # Setup RAG client
        async with RAGDocumentExample() as rag:
            rag.api_key = ai_chat.api_key  # Reuse token
            
            # Upload document
            await rag.upload_document("doc.pdf")
            
            # Ask question with RAG context
            response = await rag.ask_question("What is X?")
            
            # Use AI to summarize response
            summary = await ai_chat.send_message(
                f"Summarize this: {response['answer']}"
            )
            
            print(summary['response'])
```

### Custom Handlers

Create custom event handlers for specific needs:

```python
class MyCustomHandler:
    def __init__(self):
        self.message_count = 0
    
    async def handle_message(self, data):
        self.message_count += 1
        
        # Custom logic
        if "urgent" in data.get("content", "").lower():
            await self.send_alert()
        
        print(f"Total messages: {self.message_count}")

handler = MyCustomHandler()
client.on("chat_message", handler.handle_message)
```

## Troubleshooting

### Connection Issues

**Problem**: Cannot connect to server

```bash
# Check server is running
curl http://localhost:8000/health

# Check WebSocket endpoint
curl http://localhost:8000/ws
```

**Solution**:
- Ensure server is running: `python main.py`
- Check firewall settings
- Verify port is not in use: `lsof -i :8000`

### Authentication Failures

**Problem**: Authentication returns 401

**Solution**:
```bash
# Verify credentials in .env
cat .env | grep ADMIN_PASSWORD

# Or change password in example
await client.authenticate("admin", "your-actual-password")
```

### AI Not Responding

**Problem**: AI requests fail or timeout

**Solution**:
```bash
# Check Ollama is running
ollama list

# Verify configuration
grep OLLAMA .env

# Test Ollama directly
curl http://localhost:11434/api/tags
```

### RAG System Issues

**Problem**: Documents not processing or search returns no results

**Solution**:
```bash
# Check RAG is enabled
grep RAG_ENABLED .env

# Verify vector database
ls -la data/chromadb/  # Or your vector DB path

# Check logs
tail -f logs/chat_system.log
```

### WebSocket Connection Drops

**Problem**: WebSocket connection frequently disconnects

**Solution**:
```python
# Add retry logic
async def connect_with_retry(client, max_retries=3):
    for attempt in range(max_retries):
        try:
            await client.connect()
            return
        except Exception as e:
            if attempt < max_retries - 1:
                await asyncio.sleep(2 ** attempt)
            else:
                raise
```

### Dependency Issues

**Problem**: Missing module errors

**Solution**:
```bash
# Install all dependencies
pip install -r requirements.txt

# Install example-specific dependencies
pip install aiohttp websockets

# Or use virtual environment
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

## Testing Examples

### Unit Testing

You can write unit tests for example code:

```python
import pytest
from examples.ai_chat_example import AIChatExample

@pytest.mark.asyncio
async def test_authentication():
    async with AIChatExample() as chat:
        token = await chat.authenticate("admin", "admin")
        assert token is not None
        assert chat.api_key == token
```

### Integration Testing

Test against running server:

```bash
# Start server
python main.py &

# Run examples as integration tests
python examples/ai_chat_example.py
python examples/rag_document_example.py
python examples/websocket_client_example.py

# Check results
echo "All examples completed successfully!"
```

## Best Practices

1. **Always use async context managers**
   ```python
   async with ExampleClass() as client:
       # Ensures proper cleanup
   ```

2. **Handle errors gracefully**
   ```python
   try:
       await client.operation()
   except Exception as e:
       logger.error(f"Operation failed: {e}")
   ```

3. **Reuse authentication tokens**
   ```python
   # Don't re-authenticate for each request
   token = await client1.authenticate("user", "pass")
   client2.api_key = token  # Reuse token
   ```

4. **Use appropriate timeouts**
   ```python
   # Set timeouts for long-running operations
   response = await asyncio.wait_for(
       client.send_message("prompt"),
       timeout=30.0
   )
   ```

5. **Clean up resources**
   ```python
   try:
       # Do work
   finally:
       await client.disconnect()
       await client.cleanup()
   ```

## Additional Resources

- **[API Documentation](../docs/04-api-reference/README.md)** - Complete API reference
- **[Developer Guide](../docs/03-developer-guide/README.md)** - Development guidelines
- **[Architecture Overview](../docs/05-architecture/README.md)** - System architecture

## Support

Having issues with the examples?

- **Check the logs**: `logs/chat_system.log`
- **Review documentation**: `docs/`
- **Open an issue**: [GitHub Issues](https://github.com/Thomas-Heisig/chat_system/issues)
- **Ask in discussions**: [GitHub Discussions](https://github.com/Thomas-Heisig/chat_system/discussions)

## Contributing

Want to add more examples?

1. Follow the existing pattern
2. Add comprehensive docstrings
3. Include error handling
4. Add to this README
5. Submit a pull request

See [CONTRIBUTING.md](../CONTRIBUTING.md) for details.

---

**Happy Coding!** 🚀

For more information, visit the [main documentation](../docs/README.md).
