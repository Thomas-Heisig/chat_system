# Universal Chat System

[![Python](https://img.shields.io/badge/Python-3.9%2B-blue.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.104%2B-009688.svg)](https://fastapi.tiangolo.com/)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

A modern, modular enterprise chat system with AI integration, RAG (Retrieval-Augmented Generation) capabilities, real-time WebSocket communication, and comprehensive project management features.

## 🎯 Overview

The Universal Chat System is a full-featured enterprise communication platform that combines real-time chat with advanced AI capabilities, document intelligence through RAG systems, and robust project management tools. Built with FastAPI and designed for scalability, it offers a complete solution for teams requiring intelligent, context-aware communication.

### Key Highlights

- 🚀 **Real-time Communication** - WebSocket-based chat with low-latency message delivery
- 🤖 **AI Integration** - Support for Ollama, OpenAI, and custom AI models
- 📚 **RAG System** - Semantic search with ChromaDB, Qdrant, and Pinecone
- 🔐 **Enterprise Security** - JWT authentication, bcrypt password hashing, rate limiting
- 🗄️ **Flexible Storage** - Support for SQLite, PostgreSQL, and MongoDB
- 📊 **Project Management** - Integrated ticketing system with file attachments
- 🎨 **Modern UI** - Tab-based admin dashboard with dark/light themes
- 🐳 **Production Ready** - Docker support, comprehensive monitoring, and logging

## 📋 Table of Contents

- [Features](#-features)
- [Architecture](#-architecture)
- [Prerequisites](#-prerequisites)
- [Installation](#-installation)
- [Configuration](#️-configuration)
- [Usage](#-usage)
- [API Documentation](#-api-documentation)
- [Development](#-development)
- [Testing](#-testing)
- [Deployment](#-deployment)
- [Security](#-security)
- [Contributing](#-contributing)
- [License](#-license)
- [Support](#-support)

## ✨ Features

### Core Communication
- **Real-time Chat**: WebSocket-based messaging with connection state management
- **Message Types**: Support for user, AI, system, command, and notification messages
- **Message Compression**: Automatic compression for large messages
- **File Attachments**: Upload and share documents, images, and other files
- **User Presence**: Real-time online/offline status tracking

### AI & Intelligence
- **Multiple AI Providers**: Seamless integration with Ollama, OpenAI, and custom models
- **RAG (Retrieval-Augmented Generation)**: 
  - Multiple vector databases (ChromaDB, Qdrant, Pinecone)
  - Document processing with configurable chunking
  - Semantic search with cosine similarity
  - Support for PDF, DOCX, TXT, and Markdown files
- **Context-Aware Responses**: AI leverages conversation history and uploaded documents
- **Model Selection**: Dynamic switching between different AI models

### Project & Ticket Management
- **Project Organization**: Create and manage multiple projects
- **Ticket System**: 
  - Multiple ticket types (Task, Bug, Feature, Question, Incident)
  - Priority levels (Low, Medium, High, Critical)
  - Status tracking (Open, In Progress, Resolved, Closed)
  - Assignment and due dates
- **File Management**: Attach files to tickets and projects
- **Activity Tracking**: Audit trail for all project changes

### Security & Authentication
- **JWT Authentication**: Secure token-based authentication
- **Password Security**: bcrypt hashing with configurable rounds
- **Forced Password Change**: Admins must change default passwords on first login
- **Role-Based Access Control**: User, Moderator, Manager, and Admin roles
- **Rate Limiting**: Configurable API rate limiting to prevent abuse
- **CORS Support**: Flexible cross-origin resource sharing configuration

### Admin Dashboard
- **Tabbed Interface**: 
  - Chat - Main communication interface
  - Settings - System configuration
  - RAG System - Document and vector database management
  - Database - Administration and optimization
  - Projects - Project and ticket management
  - Files - File browser and management
  - Users - User administration
  - Monitoring - System health and logs
  - Integrations - External service connections
- **Dark/Light Themes**: User preference-based theming
- **Real-time Updates**: Live system metrics and notifications

### Storage & Database
- **Multi-Database Support**: 
  - SQLite (development, small deployments)
  - PostgreSQL (production, high-performance)
  - MongoDB (document-oriented workloads)
- **Connection Pooling**: Efficient database connection management
- **Migration Support**: Alembic-based schema migrations
- **Backup & Restore**: Built-in database backup utilities

### Integration & Extensibility
- **Plugin System**: Docker-based plugin isolation and management
- **Messaging Bridge**: Unified interface for external platforms (Slack, Discord, Teams)
- **Agent Framework**: Modular agent system for automation
- **Workflow Automation**: Configurable automation pipelines
- **Voice Processing**: Framework for TTS and transcription (extensible)

### Monitoring & Observability
- **Structured Logging**: JSON-based logs with multiple severity levels
- **Health Checks**: Comprehensive system health endpoints
- **Metrics Export**: Ready for Prometheus integration
- **Error Tracking**: Sentry support for production monitoring
- **Performance Monitoring**: Request timing and performance metrics

## 🏗️ Architecture

The system follows a modular, layered architecture:

```
┌─────────────────────────────────────────────────────────────┐
│                      Frontend Layer                          │
│  Templates (Jinja2) + Static Assets (HTML/CSS/JS)          │
└────────────────────┬────────────────────────────────────────┘
                     │
┌────────────────────┴────────────────────────────────────────┐
│                      API Layer (FastAPI)                     │
│  Routes: Chat, Messages, RAG, Settings, Admin, Projects    │
└────────────────────┬────────────────────────────────────────┘
                     │
┌────────────────────┴────────────────────────────────────────┐
│                    Service Layer                             │
│  AI Service, Auth, RAG, Message, File, Project Services    │
└────────┬────────────────────────────────┬───────────────────┘
         │                                │
┌────────┴─────────────┐    ┌────────────┴────────────────────┐
│  WebSocket Manager   │    │    Database Layer               │
│  Connection Handling │    │  Repositories + Models          │
└──────────────────────┘    └─────────────┬───────────────────┘
                                          │
                            ┌─────────────┴───────────────┐
                            │   Storage Adapters          │
                            │  SQLite, PostgreSQL, MongoDB│
                            └─────────────────────────────┘
```

For detailed architecture documentation, see [ARCHITECTURE.md](ARCHITECTURE.md).

## 🔧 Prerequisites

### Required
- **Python**: 3.9 or higher
- **pip**: Latest version
- **Git**: For version control

### Optional (for enhanced features)
- **Docker & Docker Compose**: For containerized deployment
- **PostgreSQL**: For production database
- **Redis**: For caching and session management
- **Ollama**: For local AI model hosting

## 📦 Installation

### Quick Start (Local Development)

1. **Clone the Repository**
```bash
git clone https://github.com/Thomas-Heisig/chat_system.git
cd chat_system
```

2. **Create Virtual Environment**
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. **Install Dependencies**
```bash
# Core dependencies
pip install -r requirements.txt

# Or install with optional features
pip install -e ".[all]"  # Installs all optional dependencies
```

4. **Configure Environment**
```bash
cp .env.example .env
# Edit .env with your configuration (see Configuration section)
```

5. **Initialize Database**
```bash
python main.py
# Database will be automatically initialized on first run
```

6. **Access the Application**
- Open browser: http://localhost:8000
- Default credentials: `admin` / `admin123` (you will be prompted to change this)
- API Documentation: http://localhost:8000/docs

### Docker Installation

For production deployments, Docker is recommended:

```bash
# Start all services (app, database, redis, ollama, vector db)
docker-compose up -d

# View logs
docker-compose logs -f app

# Stop services
docker-compose down
```

For detailed setup instructions, see [SETUP.md](SETUP.md).

## ⚙️ Configuration

### Environment Variables

Create a `.env` file in the project root (use `.env.example` as template):

```bash
# Application Settings
APP_NAME="Universal Chat System"
APP_ENVIRONMENT=development  # development, staging, production
APP_DEBUG=true
APP_SECRET_KEY=your-secret-key-change-in-production

# Server Configuration
HOST=0.0.0.0
PORT=8000
RELOAD=true  # Set to false in production

# Database Configuration
DATABASE_TYPE=sqlite  # sqlite, postgresql, mongodb
DATABASE_URL=sqlite:///./chat.db
# For PostgreSQL: postgresql://user:password@localhost:5432/chatdb
# For MongoDB: mongodb://localhost:27017/chatdb

# Vector Database (RAG System)
RAG_ENABLED=true
VECTOR_DB_TYPE=chroma  # chroma, qdrant, pinecone
CHROMA_DB_PATH=./chroma_db
QDRANT_URL=http://localhost:6333
PINECONE_API_KEY=your-pinecone-key

# AI Configuration
AI_ENABLED=true
OLLAMA_URL=http://localhost:11434
OLLAMA_MODEL=llama2
OPENAI_API_KEY=your-openai-key-if-using-openai

# Security Settings
JWT_SECRET_KEY=your-jwt-secret-key-minimum-32-chars
JWT_ALGORITHM=HS256
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=30
CORS_ORIGINS=["http://localhost:3000"]

# Performance & Limits
RATE_LIMIT_ENABLED=true
MAX_MESSAGE_LENGTH=10000
MAX_FILE_SIZE_MB=50

# Logging
LOG_LEVEL=INFO  # DEBUG, INFO, WARNING, ERROR, CRITICAL
LOG_FILE=logs/chat_system.log
```

### Configuration Files

- **`.flake8`**: Python code style configuration
- **`pyproject.toml`**: Project metadata and tool configuration
- **`docker-compose.yml`**: Multi-service Docker orchestration

For advanced configuration options, see [DEPLOYMENT.md](DEPLOYMENT.md).

## 🚀 Usage

### Starting the Application

**Development Mode** (with auto-reload):
```bash
python main.py
```

**Production Mode** (using uvicorn directly):
```bash
uvicorn main:app --host 0.0.0.0 --port 8000 --workers 4
```

**With Makefile** (if available):
```bash
make run       # Development mode
make serve     # Production mode
make test      # Run tests
make lint      # Check code style
```

### Using the Web Interface

1. **Login**: Navigate to http://localhost:8000 and login with your credentials
2. **Chat**: Use the Chat tab to send messages and interact with AI
3. **Upload Documents**: Use RAG System tab to upload documents for semantic search
4. **Manage Projects**: Create projects and tickets in the Projects tab
5. **Configure**: Adjust settings in the Settings tab

### Using the API

**Authentication**:
```bash
# Login to get JWT token
curl -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"your-new-password"}'

# Use token in subsequent requests
TOKEN="your-jwt-token"
curl -H "Authorization: Bearer $TOKEN" \
  http://localhost:8000/api/messages
```

**Send a Message**:
```bash
curl -X POST http://localhost:8000/api/messages \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","message":"Hello from API"}'
```

**Query RAG System**:
```bash
curl -X POST http://localhost:8000/api/rag/query \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"query":"What is the system architecture?","top_k":5}'
```

For comprehensive API documentation, visit http://localhost:8000/docs (Swagger UI) or http://localhost:8000/redoc (ReDoc).

## 📚 API Documentation

### Main Endpoints

| Endpoint | Method | Description | Auth Required |
|----------|--------|-------------|---------------|
| `/` | GET | Admin dashboard | No |
| `/health` | GET | Health check | No |
| `/status` | GET | Detailed system status | No |
| `/docs` | GET | OpenAPI documentation | No |
| `/api/auth/login` | POST | User authentication | No |
| `/api/messages` | GET, POST | Message operations | Yes |
| `/api/rag/documents` | GET, POST, DELETE | Document management | Yes |
| `/api/rag/query` | POST | Semantic search | Yes |
| `/api/projects` | GET, POST | Project management | Yes |
| `/api/settings/*` | GET, PUT | Configuration management | Yes (Admin) |
| `/ws` | WebSocket | Real-time chat connection | Yes |

### Response Format

All API responses follow a consistent format:

**Success Response**:
```json
{
  "success": true,
  "data": {...},
  "message": "Operation completed successfully"
}
```

**Error Response**:
```json
{
  "success": false,
  "error": "Error description",
  "details": {...}
}
```

For detailed API reference, see [docs/API.md](docs/API.md).

## 🛠️ Development

### Project Structure

```
chat_system/
├── agents/               # Agent framework and examples
├── analytics/            # Event tracking and A/B testing
├── config/              # Configuration management
├── core/                # Core utilities
├── database/            # Database models, repositories, adapters
├── docs/                # Documentation
├── elyza/               # ELYZA model integration
├── frontend/            # Frontend source (if separate)
├── integration/         # External service integrations
├── k8s/                 # Kubernetes manifests
├── logs/                # Application logs
├── memory/              # Memory and personalization
├── routes/              # API route handlers
├── services/            # Business logic services
│   └── rag/            # RAG system implementations
├── static/              # Static assets (CSS, JS, images)
├── templates/           # Jinja2 HTML templates
├── tests/               # Test suite
│   ├── unit/           # Unit tests
│   ├── integration/    # Integration tests
│   └── e2e/            # End-to-end tests
├── utils/               # Utility functions
├── voice/               # Voice processing framework
├── websocket/           # WebSocket handlers
├── workflow/            # Workflow automation
├── workspace/           # Workspace management
├── main.py              # Application entry point
├── requirements.txt     # Python dependencies
├── pyproject.toml       # Project metadata
├── docker-compose.yml   # Docker orchestration
└── Dockerfile           # Container image definition
```

### Code Style

This project follows PEP 8 style guidelines with the following tools:

- **Black**: Code formatting (line length: 100)
- **isort**: Import sorting
- **flake8**: Style guide enforcement
- **mypy**: Static type checking

```bash
# Format code
black --line-length 100 .

# Sort imports
isort --profile black .

# Check style
flake8 .

# Type check
mypy .
```

### Pre-commit Hooks

Install pre-commit hooks to ensure code quality:

```bash
pip install pre-commit
pre-commit install
```

### Adding Features

1. Create feature branch: `git checkout -b feature/your-feature`
2. Implement changes following project structure
3. Add tests for new functionality
4. Update documentation
5. Run linters and tests
6. Submit pull request

For contribution guidelines, see [CONTRIBUTING.md](CONTRIBUTING.md).

## 🧪 Testing

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=. --cov-report=html

# Run specific test file
pytest tests/unit/test_message_service.py

# Run specific test
pytest tests/unit/test_message_service.py::test_create_message

# Run in verbose mode
pytest -v

# Run with output
pytest -s
```

### Test Structure

- **Unit Tests**: Test individual components in isolation
- **Integration Tests**: Test component interactions
- **End-to-End Tests**: Test complete user workflows

### Writing Tests

```python
import pytest
from services.message_service import MessageService

@pytest.fixture
def message_service():
    return MessageService()

def test_create_message(message_service):
    message = message_service.create_message(
        username="testuser",
        content="Test message"
    )
    assert message.username == "testuser"
    assert message.message == "Test message"
```

## 🚢 Deployment

### Production Checklist

Before deploying to production:

- [ ] Change all default passwords
- [ ] Set strong `APP_SECRET_KEY` and `JWT_SECRET_KEY`
- [ ] Set `APP_DEBUG=false` and `APP_ENVIRONMENT=production`
- [ ] Use PostgreSQL or MongoDB instead of SQLite
- [ ] Enable HTTPS/TLS
- [ ] Configure proper CORS origins
- [ ] Set up monitoring and logging
- [ ] Configure automated backups
- [ ] Review and configure rate limits
- [ ] Set up reverse proxy (nginx, Caddy)
- [ ] Configure firewall rules

### Docker Production Deployment

```bash
# Use production compose file
docker-compose -f docker-compose.prod.yml up -d

# Scale workers
docker-compose -f docker-compose.prod.yml up -d --scale app=4

# View production logs
docker-compose -f docker-compose.prod.yml logs -f
```

### Kubernetes Deployment

Kubernetes manifests are available in the `k8s/` directory:

```bash
# Apply configurations
kubectl apply -f k8s/

# Check deployment status
kubectl get pods
kubectl get services

# View logs
kubectl logs -f deployment/chat-system
```

For comprehensive deployment guide, see [DEPLOYMENT.md](DEPLOYMENT.md).

## 🔒 Security

### Security Features

- **JWT Authentication**: Secure token-based authentication with expiration
- **Password Security**: bcrypt hashing with configurable cost factor
- **Forced Password Change**: Default admin password must be changed on first login
- **Rate Limiting**: Prevent brute-force and DoS attacks
- **CORS Configuration**: Control cross-origin access
- **Input Validation**: Pydantic-based request validation
- **SQL Injection Prevention**: Parameterized queries
- **XSS Protection**: Template auto-escaping

### Security Best Practices

1. **Never commit secrets**: Use environment variables
2. **Rotate keys regularly**: Especially JWT and API keys
3. **Monitor logs**: Watch for suspicious activity
4. **Keep dependencies updated**: Regularly update packages
5. **Use HTTPS**: Always in production
6. **Implement backup strategy**: Regular database backups
7. **Review access logs**: Monitor authentication attempts

### Reporting Security Issues

For security vulnerabilities, please email security@example.com instead of using the issue tracker. See [SECURITY.md](SECURITY.md) for details.

## 🤝 Contributing

We welcome contributions! Here's how you can help:

### Ways to Contribute

- 🐛 Report bugs
- 💡 Suggest new features
- 📝 Improve documentation
- 🔧 Submit pull requests
- ⭐ Star the repository

### Contribution Process

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/AmazingFeature`)
3. Make your changes
4. Add tests for new functionality
5. Ensure all tests pass (`pytest`)
6. Format code (`black .` and `isort .`)
7. Commit changes (`git commit -m 'Add AmazingFeature'`)
8. Push to branch (`git push origin feature/AmazingFeature`)
9. Open a Pull Request

### Code Review Process

- All submissions require review
- CI/CD checks must pass
- Code coverage should not decrease
- Follow existing code style
- Update documentation as needed

For detailed guidelines, see [CONTRIBUTING.md](CONTRIBUTING.md).

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 📞 Support

### Getting Help

- 📖 **Documentation**: Check the docs/ directory
- 💬 **Discussions**: Use GitHub Discussions for questions
- 🐛 **Bug Reports**: Open an issue with details and logs
- 📧 **Email**: support@example.com

### Useful Links

- [GitHub Repository](https://github.com/Thomas-Heisig/chat_system)
- [Issue Tracker](https://github.com/Thomas-Heisig/chat_system/issues)
- [Changelog](CHANGES.md)
- [Roadmap](ROADMAP.md)

## 🙏 Acknowledgments

- FastAPI for the excellent web framework
- Ollama for local AI model hosting
- ChromaDB for vector database capabilities
- All contributors and users of this project

---

**Made with ❤️ by Thomas Heisig**

For more information, visit the [documentation](docs/) or check out the [ARCHITECTURE.md](ARCHITECTURE.md) for system design details.
