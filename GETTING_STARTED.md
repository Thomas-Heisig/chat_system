# Getting Started with Universal Chat System

**Version:** 2.0.0  
**Last Updated:** 2025-12-06  
**Estimated Reading Time:** 20 minutes

## 📋 Table of Contents

- [Overview](#overview)
- [Prerequisites](#prerequisites)
- [Quick Start](#quick-start)
- [Installation](#installation)
- [Configuration](#configuration)
- [First Chat Session](#first-chat-session)
- [Web Interface](#web-interface)
- [Next Steps](#next-steps)

## Overview

The Universal Chat System is a modern, enterprise-grade chat platform with AI integration, real-time communication, and comprehensive project management features. This guide will walk you through installation, configuration, and your first chat session.

### What You'll Learn

- How to install and configure the chat system
- Understanding core concepts and architecture
- Creating your first chat session
- Using the web interface
- Integrating AI models and RAG capabilities

### Key Concepts

**Real-time Communication**: WebSocket-based messaging with low latency  
**AI Integration**: Support for multiple AI providers (Ollama, OpenAI)  
**RAG System**: Retrieval-Augmented Generation for knowledge-based responses  
**Project Management**: Integrated ticketing and project organization  
**Security**: JWT authentication with role-based access control

## Prerequisites

### System Requirements

**Hardware:**
- CPU: 2+ cores recommended (4+ for AI features)
- RAM: 4GB minimum (8GB+ recommended with AI)
- Storage: 5GB minimum (more for document storage)

**Software:**
- Python 3.9 or higher
- pip (Python package manager)
- Git (for cloning repository)
- Docker (optional, for containerized deployment)

**Optional for AI Features:**
- Ollama (for local AI models)
- GPU with CUDA support (for faster AI inference)

### Network Requirements

- Internet connection for package installation
- Port 8000 available for web server
- Port 5432 for PostgreSQL (if using external database)

## Quick Start

Get up and running in 5 minutes:

```bash
# 1. Clone the repository
git clone https://github.com/Thomas-Heisig/chat_system.git
cd chat_system

# 2. Install dependencies
pip install -r requirements.txt

# 3. Set up environment
cp .env.example .env

# 4. Initialize database
python -c "from database.connection import init_db; init_db()"

# 5. Start the server
python main.py
```

Open your browser to: **http://localhost:8000**

Default credentials:
- **Username:** admin
- **Password:** admin (you'll be forced to change this on first login)

## Installation

### Standard Installation

#### Step 1: Clone Repository

```bash
git clone https://github.com/Thomas-Heisig/chat_system.git
cd chat_system
```

#### Step 2: Create Virtual Environment (Recommended)

```bash
# Create virtual environment
python -m venv venv

# Activate it
# On Linux/Mac:
source venv/bin/activate
# On Windows:
venv\Scripts\activate
```

#### Step 3: Install Dependencies

```bash
pip install -r requirements.txt
```

#### Step 4: Verify Installation

```bash
python -c "import fastapi; import sqlalchemy; print('✅ Installation successful!')"
```

### Docker Installation

For a containerized setup:

```bash
# Build and start services
docker-compose up -d

# Check logs
docker-compose logs -f

# Access application
# http://localhost:8000
```

### Development Installation

For development with additional tools:

```bash
# Install development dependencies
pip install -r requirements.txt
pip install pytest black flake8 mypy

# Set up pre-commit hooks
pre-commit install
```

## Configuration

### Environment Variables

Copy the example environment file:

```bash
cp .env.example .env
```

### Essential Configuration

Edit `.env` with your settings:

```bash
# Application Settings
APP_NAME=Universal Chat System
HOST=0.0.0.0
PORT=8000
DEBUG=false

# Security
SECRET_KEY=your-secret-key-here  # Change this!
ADMIN_PASSWORD=admin              # Change on first login

# Database
DATABASE_URL=sqlite:///./chat.db
# Or for PostgreSQL:
# DATABASE_URL=postgresql://user:password@localhost/chatdb

# AI Integration (Optional)
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_ENABLED=true
DEFAULT_MODEL=llama2

# RAG System (Optional)
RAG_ENABLED=true
VECTOR_DB_TYPE=chromadb
VECTOR_DB_PATH=./data/vectordb
```

### Database Configuration

#### SQLite (Default)

No additional setup needed. Database file created automatically.

```bash
DATABASE_URL=sqlite:///./chat.db
```

#### PostgreSQL (Production)

```bash
# Install PostgreSQL client
pip install psycopg2-binary

# Configure connection
DATABASE_URL=postgresql://user:password@localhost:5432/chatdb

# Create database
createdb chatdb

# Initialize schema
python -c "from database.connection import init_db; init_db()"
```

#### MongoDB (Alternative)

```bash
# Install MongoDB driver
pip install pymongo

# Configure connection
DATABASE_TYPE=mongodb
MONGODB_URL=mongodb://localhost:27017/chatdb
```

### AI Configuration

#### Ollama Setup

```bash
# Install Ollama
curl https://ollama.ai/install.sh | sh

# Pull a model
ollama pull llama2

# Verify it's running
curl http://localhost:11434/api/tags
```

#### OpenAI Setup

```bash
# Add to .env
OPENAI_API_KEY=your-api-key-here
OPENAI_ENABLED=true
DEFAULT_MODEL=gpt-3.5-turbo
```

### RAG System Configuration

```bash
# Enable RAG
RAG_ENABLED=true

# Choose vector database
VECTOR_DB_TYPE=chromadb  # or qdrant, pinecone

# Configure chunking
CHUNK_SIZE=1000
CHUNK_OVERLAP=200

# Configure retrieval
TOP_K_DOCUMENTS=5
SIMILARITY_THRESHOLD=0.7
```

## First Chat Session

### Step 1: Start the Server

```bash
python main.py
```

You should see:

```
INFO:     Started server process
INFO:     Waiting for application startup.
INFO:     Application startup complete.
INFO:     Uvicorn running on http://0.0.0.0:8000
```

### Step 2: Access Web Interface

Open your browser to: **http://localhost:8000**

### Step 3: Login

Use default credentials (first-time only):
- Username: `admin`
- Password: `admin`

You'll be prompted to change the password immediately.

### Step 4: Send Your First Message

1. In the chat interface, type a message
2. Press Enter or click Send
3. You'll see your message appear in the chat

### Step 5: Try AI Integration

If AI is configured:

```
You: Hello, AI!
AI: Hello! How can I help you today?
```

### Step 6: Upload a Document (RAG)

If RAG is enabled:

1. Click the file upload button
2. Select a PDF, DOCX, or TXT file
3. Wait for processing
4. Ask questions about the document:

```
You: What is this document about?
AI: [AI provides summary based on document content]
```

## Web Interface

### Admin Dashboard

The admin dashboard provides tabbed access to all features:

#### Chat Tab
- Real-time messaging
- File attachments
- AI interactions
- Message history

#### Settings Tab
- System configuration
- User preferences
- Feature toggles
- Security settings

#### RAG System Tab
- Document management
- Vector database status
- Upload new documents
- Configure chunking and retrieval

#### Database Tab
- Connection status
- Schema management
- Backups and maintenance
- Performance metrics

#### Projects Tab
- Create and manage projects
- Ticket system
- Task assignments
- Project analytics

#### Files Tab
- File browser
- Upload management
- Storage analytics
- File search

#### Users Tab
- User management
- Role assignment
- Access control
- Activity monitoring

#### Monitoring Tab
- System health
- Performance metrics
- Log viewer
- Error tracking

#### Integrations Tab
- External services
- API connections
- Webhook configuration
- Plugin management

### Keyboard Shortcuts

- `Ctrl + Enter` - Send message
- `Ctrl + /` - Focus chat input
- `Ctrl + ,` - Open settings
- `Esc` - Close modal/dialog

### Dark Mode

Toggle dark mode in Settings tab:
1. Click Settings
2. Appearance section
3. Toggle "Dark Mode"

## Next Steps

### Learn More

- **[BASIC_USAGE.md](BASIC_USAGE.md)** - Learn basic operations and workflows
- **[AI_INTEGRATION.md](AI_INTEGRATION.md)** - Deep dive into AI and RAG features
- **[ADVANCED_FEATURES.md](ADVANCED_FEATURES.md)** - Explore advanced capabilities
- **[API Documentation](docs/04-api-reference/README.md)** - REST API reference

### Tutorials

- **[KNOWLEDGE_DATABASE.md](KNOWLEDGE_DATABASE.md)** - RAG system and document management
- **[TASK_SYSTEM.md](TASK_SYSTEM.md)** - Project and ticket management
- **[Developer Guide](docs/03-developer-guide/README.md)** - For developers

### Example Scripts

Check the `examples/` directory for:
- `ai_chat_example.py` - AI chat integration
- `rag_document_example.py` - Document processing
- `websocket_client_example.py` - WebSocket client

### Community

- **GitHub Issues**: Report bugs or request features
- **Discussions**: Ask questions and share ideas
- **Contributing**: See CONTRIBUTING.md

## Troubleshooting

### Server Won't Start

**Problem**: `Address already in use`

```bash
# Find process using port 8000
lsof -i :8000  # Linux/Mac
netstat -ano | findstr :8000  # Windows

# Kill the process or change port
PORT=8001 python main.py
```

### Database Connection Failed

**Problem**: Can't connect to database

```bash
# Check database URL
echo $DATABASE_URL

# For PostgreSQL, ensure server is running
sudo service postgresql status

# Re-initialize database
python -c "from database.connection import init_db; init_db()"
```

### AI Not Responding

**Problem**: AI features not working

```bash
# Check Ollama is running
curl http://localhost:11434/api/tags

# Verify configuration
grep OLLAMA .env

# Check model is pulled
ollama list
```

### RAG Documents Not Processing

**Problem**: Documents upload but can't query them

```bash
# Check RAG is enabled
grep RAG_ENABLED .env

# Verify vector database
python -c "from services.rag_service import get_rag_service; print(get_rag_service().get_status())"

# Re-index documents
# Use web interface: RAG System > Re-index All
```

## Security Considerations

### Production Deployment

Before deploying to production:

1. **Change Secret Key**
   ```bash
   # Generate a new secret key
   python -c "import secrets; print(secrets.token_urlsafe(32))"
   ```

2. **Set Debug to False**
   ```bash
   DEBUG=false
   ```

3. **Use Strong Passwords**
   - Change admin password immediately
   - Enforce password policies
   - Enable 2FA if available

4. **Configure HTTPS**
   - Use reverse proxy (nginx, Apache)
   - Obtain SSL certificate
   - Redirect HTTP to HTTPS

5. **Set Up Rate Limiting**
   ```bash
   RATE_LIMIT_ENABLED=true
   RATE_LIMIT_PER_MINUTE=60
   ```

6. **Review Security Settings**
   - See [SECURITY.md](SECURITY.md)
   - Enable security headers
   - Configure CORS properly

## Support

### Getting Help

- **Documentation**: [docs/](docs/)
- **Issues**: [GitHub Issues](https://github.com/Thomas-Heisig/chat_system/issues)
- **Discussions**: [GitHub Discussions](https://github.com/Thomas-Heisig/chat_system/discussions)

### Reporting Issues

When reporting issues, include:
- System information (OS, Python version)
- Steps to reproduce
- Error messages and logs
- Configuration (sanitized, no secrets)

## Summary

You now have:
- ✅ Chat system installed and running
- ✅ Basic configuration completed
- ✅ First chat session completed
- ✅ Understanding of core features
- ✅ Knowledge of where to learn more

**Next:** Continue with [BASIC_USAGE.md](BASIC_USAGE.md) to learn common operations and workflows.

---

**Questions or Issues?** Please refer to our [documentation](docs/) or [open an issue](https://github.com/Thomas-Heisig/chat_system/issues).
