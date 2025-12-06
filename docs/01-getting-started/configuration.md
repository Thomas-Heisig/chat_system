# Configuration Guide

Complete configuration reference for the Universal Chat System.

## Table of Contents

- [Environment Variables](#environment-variables)
- [Configuration Files](#configuration-files)
- [Database Configuration](#database-configuration)
- [AI Configuration](#ai-configuration)
- [Security Configuration](#security-configuration)
- [Performance Configuration](#performance-configuration)

## Environment Variables

All configuration is managed through environment variables in the `.env` file.

### Application Settings

```bash
# Application Identity
APP_NAME="Universal Chat System"
APP_VERSION="2.0.0"
APP_ENVIRONMENT=development  # development, staging, production

# Debug Mode (disable in production!)
APP_DEBUG=true

# Server Configuration
HOST=0.0.0.0
PORT=8000
RELOAD=true  # Auto-reload on code changes (development only)
WORKERS=4    # Number of worker processes (production)

# Logging
LOG_LEVEL=INFO  # DEBUG, INFO, WARNING, ERROR, CRITICAL
LOG_FILE=logs/chat_system.log
LOG_FORMAT=json  # json or text
```

### Security Settings

```bash
# Secret Keys (MUST be changed in production!)
APP_SECRET_KEY=your-secret-key-minimum-32-characters-long
JWT_SECRET_KEY=your-jwt-secret-key-minimum-32-characters-long

# JWT Configuration
JWT_ALGORITHM=HS256
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=30
JWT_REFRESH_TOKEN_EXPIRE_DAYS=7

# Password Security
BCRYPT_ROUNDS=12  # Higher = more secure but slower

# CORS Configuration
CORS_ORIGINS=["http://localhost:3000","http://localhost:8080"]
CORS_ALLOW_CREDENTIALS=true

# Rate Limiting
RATE_LIMIT_ENABLED=true
RATE_LIMIT_PER_MINUTE=100
RATE_LIMIT_BURST=20
```

### Database Configuration

#### SQLite (Development)

```bash
DATABASE_TYPE=sqlite
DATABASE_URL=sqlite:///./chat.db
```

#### PostgreSQL (Production)

```bash
DATABASE_TYPE=postgresql
DATABASE_URL=postgresql://username:password@localhost:5432/chatdb

# Connection Pool Settings
DB_POOL_SIZE=20
DB_MAX_OVERFLOW=10
DB_POOL_TIMEOUT=30
DB_POOL_RECYCLE=3600
```

#### MongoDB (Document Store)

```bash
DATABASE_TYPE=mongodb
DATABASE_URL=mongodb://username:password@localhost:27017/chatdb

# MongoDB Settings
MONGODB_MAX_POOL_SIZE=100
MONGODB_MIN_POOL_SIZE=10
```

### AI Configuration

#### Ollama (Local AI)

```bash
AI_ENABLED=true
AI_PROVIDER=ollama

# Ollama Settings
OLLAMA_URL=http://localhost:11434
OLLAMA_MODEL=llama2
OLLAMA_TIMEOUT=120  # seconds
OLLAMA_TEMPERATURE=0.7
OLLAMA_MAX_TOKENS=2000
```

#### OpenAI

```bash
AI_ENABLED=true
AI_PROVIDER=openai

# OpenAI Settings
OPENAI_API_KEY=your-openai-api-key
OPENAI_MODEL=gpt-3.5-turbo
OPENAI_TEMPERATURE=0.7
OPENAI_MAX_TOKENS=2000
```

#### AI Fallback

```bash
# Use ELYZA as fallback when primary AI unavailable
AI_FALLBACK_ENABLED=true
ELYZA_MODEL_PATH=models/elyza-japanese-llama2-7b
```

### RAG System Configuration

#### ChromaDB (Default)

```bash
RAG_ENABLED=true
VECTOR_DB_TYPE=chroma

# ChromaDB Settings
CHROMA_DB_PATH=./chroma_db
CHROMA_COLLECTION_NAME=documents
CHROMA_EMBEDDING_MODEL=all-MiniLM-L6-v2
```

#### Qdrant

```bash
RAG_ENABLED=true
VECTOR_DB_TYPE=qdrant

# Qdrant Settings
QDRANT_URL=http://localhost:6333
QDRANT_API_KEY=your-qdrant-api-key
QDRANT_COLLECTION_NAME=documents
QDRANT_VECTOR_SIZE=384
```

#### Pinecone

```bash
RAG_ENABLED=true
VECTOR_DB_TYPE=pinecone

# Pinecone Settings
PINECONE_API_KEY=your-pinecone-api-key
PINECONE_ENVIRONMENT=us-west1-gcp
PINECONE_INDEX_NAME=chat-documents
```

### Feature Flags

```bash
# Core Features
FEATURE_USER_AUTHENTICATION=true
FEATURE_PROJECT_MANAGEMENT=true
FEATURE_TICKET_SYSTEM=true
FEATURE_FILE_UPLOAD=true
FEATURE_WEBSOCKET=true

# Advanced Features (planned)
FEATURE_VOICE_PROCESSING=false
FEATURE_WORKFLOW_AUTOMATION=false
FEATURE_PLUGIN_SYSTEM=false
FEATURE_EXTERNAL_INTEGRATIONS=false
```

### File Upload Configuration

```bash
# File Upload Settings
MAX_FILE_SIZE_MB=50
ALLOWED_FILE_EXTENSIONS=.pdf,.docx,.txt,.md,.jpg,.png
UPLOAD_DIRECTORY=uploads/
```

### WebSocket Configuration

```bash
WEBSOCKET_ENABLED=true
WEBSOCKET_PING_INTERVAL=30  # seconds
WEBSOCKET_PING_TIMEOUT=10   # seconds
WEBSOCKET_MAX_CONNECTIONS=1000
WEBSOCKET_MESSAGE_QUEUE_SIZE=100
```

### Redis Configuration (Optional)

```bash
# Redis for caching and sessions
REDIS_ENABLED=true
REDIS_URL=redis://localhost:6379/0
REDIS_MAX_CONNECTIONS=50
REDIS_SOCKET_TIMEOUT=5

# Cache TTL Settings
CACHE_DEFAULT_TTL=300  # 5 minutes
CACHE_USER_TTL=3600    # 1 hour
CACHE_CONFIG_TTL=7200  # 2 hours
```

### Monitoring Configuration

```bash
# Monitoring
MONITORING_ENABLED=true
METRICS_ENABLED=true
PROMETHEUS_PORT=9090

# Error Tracking (Sentry)
SENTRY_ENABLED=false
SENTRY_DSN=your-sentry-dsn
SENTRY_ENVIRONMENT=production
```

## Configuration Files

### pyproject.toml

Project metadata and tool configuration:

```toml
[project]
name = "chat-system"
version = "2.0.0"
description = "Universal Chat System with AI"

[tool.black]
line-length = 100
target-version = ['py39']

[tool.isort]
profile = "black"
line_length = 100

[tool.pytest.ini_options]
testpaths = ["tests"]
python_files = ["test_*.py"]
addopts = "-v --cov=. --cov-report=html"
```

### .flake8

Code style configuration:

```ini
[flake8]
max-line-length = 100
extend-ignore = E203, E266, E501, W503
exclude = 
    .git,
    __pycache__,
    venv,
    build,
    dist
```

### docker-compose.yml

Service orchestration:

```yaml
version: '3.8'

services:
  app:
    build: .
    ports:
      - "8000:8000"
    environment:
      - DATABASE_TYPE=postgresql
      - DATABASE_URL=postgresql://chatuser:chatpass@postgres:5432/chatdb
    depends_on:
      - postgres
      - redis
      - ollama

  postgres:
    image: postgres:15
    environment:
      - POSTGRES_USER=chatuser
      - POSTGRES_PASSWORD=chatpass
      - POSTGRES_DB=chatdb
    volumes:
      - postgres_data:/var/lib/postgresql/data

  redis:
    image: redis:7-alpine
    volumes:
      - redis_data:/data

  ollama:
    image: ollama/ollama:latest
    ports:
      - "11434:11434"
    volumes:
      - ollama_data:/root/.ollama

volumes:
  postgres_data:
  redis_data:
  ollama_data:
```

## Configuration by Environment

### Development Configuration

```bash
APP_ENVIRONMENT=development
APP_DEBUG=true
DATABASE_TYPE=sqlite
DATABASE_URL=sqlite:///./chat.db
LOG_LEVEL=DEBUG
RELOAD=true
```

### Staging Configuration

```bash
APP_ENVIRONMENT=staging
APP_DEBUG=false
DATABASE_TYPE=postgresql
DATABASE_URL=postgresql://user:pass@staging-db:5432/chatdb
LOG_LEVEL=INFO
RELOAD=false
WORKERS=2
```

### Production Configuration

```bash
APP_ENVIRONMENT=production
APP_DEBUG=false
DATABASE_TYPE=postgresql
DATABASE_URL=postgresql://user:pass@prod-db:5432/chatdb
LOG_LEVEL=WARNING
RELOAD=false
WORKERS=4

# Security
APP_SECRET_KEY=generated-secure-key-32-chars-min
JWT_SECRET_KEY=generated-secure-key-32-chars-min
RATE_LIMIT_ENABLED=true

# Performance
REDIS_ENABLED=true
DB_POOL_SIZE=50
WEBSOCKET_MAX_CONNECTIONS=5000
```

## Configuration Validation

The system validates configuration on startup:

```python
from config.settings import settings

# Access validated settings
print(f"App Name: {settings.APP_NAME}")
print(f"Database: {settings.DATABASE_TYPE}")
print(f"AI Enabled: {settings.AI_ENABLED}")
```

### Configuration Errors

Common errors and solutions:

**Invalid DATABASE_URL**
```bash
# Error: Could not parse database URL
# Solution: Check format matches database type
DATABASE_URL=postgresql://user:pass@host:port/database
```

**Secret Key Too Short**
```bash
# Error: Secret key must be at least 32 characters
# Solution: Generate secure key
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

**Port Already in Use**
```bash
# Error: Address already in use
# Solution: Change port or kill existing process
PORT=8080
```

## Dynamic Configuration

### Runtime Configuration

Some settings can be changed at runtime through the Settings API:

```bash
# Update AI model
curl -X PUT http://localhost:8000/api/settings/ai \
  -H "Authorization: Bearer $TOKEN" \
  -d '{"model":"llama2:13b"}'

# Update rate limits
curl -X PUT http://localhost:8000/api/settings/rate-limit \
  -H "Authorization: Bearer $TOKEN" \
  -d '{"per_minute":200}'
```

### Configuration Reloading

```bash
# Reload configuration without restart
curl -X POST http://localhost:8000/api/admin/reload-config \
  -H "Authorization: Bearer $TOKEN"
```

## Security Best Practices

### Secret Generation

Generate secure secrets:

```bash
# APP_SECRET_KEY
python -c "import secrets; print(secrets.token_urlsafe(32))"

# JWT_SECRET_KEY
python -c "import secrets; print(secrets.token_hex(32))"
```

### Configuration Encryption

Sensitive values can be encrypted:

```bash
# Install encryption support
pip install cryptography

# Encrypt value
python -m utils.encrypt "sensitive-value"
```

### Environment-Specific Secrets

Use different secrets per environment:

```bash
# Development
APP_SECRET_KEY=dev-secret-key-for-local-testing

# Production (from secrets manager)
APP_SECRET_KEY=$(aws secretsmanager get-secret-value --secret-id prod/app-secret)
```

## Troubleshooting

### Check Current Configuration

```bash
# View loaded configuration
curl http://localhost:8000/api/settings/config \
  -H "Authorization: Bearer $TOKEN"
```

### Validate Configuration

```bash
# Validate before starting
python -c "from config.settings import settings; settings.validate()"
```

### Configuration Precedence

1. Environment variables (highest priority)
2. `.env` file
3. Default values (lowest priority)

## Next Steps

- **[First Steps Tutorial](first-steps.md)** - Start using the system
- **[User Guide](../02-user-guide/README.md)** - Learn features
- **[Operations Guide](../06-operations/README.md)** - Production deployment

---

**Version:** 2.0.0  
**Last Updated:** 2025-12-06  
**Language:** English | [Deutsch](configuration.de.md)
