# Complete Configuration Guide

## Overview

This document provides a comprehensive guide to all configuration options in the Chat System. All features support graceful fallback when disabled or unavailable.

## Core Principle: Graceful Degradation

**The Chat System is designed to work out-of-the-box with minimal configuration.**

- **Default Configuration:** Works immediately with no setup
- **Fallback Mechanisms:** All optional features degrade gracefully
- **No Errors:** Disabled features don't cause errors
- **Progressive Enhancement:** Add features as needed

## Configuration Hierarchy

Configuration is loaded in this order (later sources override earlier ones):

1. **Default Values:** In `config/settings.py`
2. **Environment File:** `.env` file
3. **Environment Variables:** System environment variables
4. **Runtime:** Programmatic configuration

## Quick Start Configurations

### Development (Default)

```bash
# Minimal configuration - system works immediately
APP_ENVIRONMENT=development
APP_DEBUG=true
DATABASE_URL=chat_system.db
```

### Production (Recommended)

```bash
# Essential production settings
APP_ENVIRONMENT=production
APP_DEBUG=false
APP_SECRET_KEY=<generate-secure-random-key>

# Enable authentication
FEATURE_USER_AUTHENTICATION=true

# Enable monitoring
SENTRY_DSN=<your-sentry-dsn>
GRAFANA_ENABLED=true
TRACING_ENABLED=true
```

### Full Features (Optional)

```bash
# Enable all optional features
AI_ENABLED=true
RAG_ENABLED=true
TTS_ENABLED=true
WHISPER_ENABLED=true
ELYZA_ENABLED=true
PLUGINS_ENABLED=true
REDIS_ENABLED=true
OBJECT_STORAGE_ENABLED=true
```

## Configuration Sections

### 1. Application Settings

```bash
# Basic Application Configuration
APP_NAME=Chat System
APP_VERSION=2.0.0
APP_ENVIRONMENT=development  # development, staging, production
APP_DEBUG=true
APP_SECRET_KEY=your-secret-key-here

# Server Configuration
HOST=0.0.0.0
PORT=8000

# CORS Configuration
CORS_ORIGINS=["http://localhost:3000", "http://localhost:8000"]
```

**Fallback:** Works with defaults, no external dependencies

### 2. Database Configuration

```bash
# Database Type
DATABASE_URL=chat_system.db  # SQLite (default)
# DATABASE_URL=postgresql://user:pass@localhost/dbname  # PostgreSQL
# DATABASE_URL=mongodb://localhost:27017/dbname  # MongoDB

# Connection Pool
DATABASE_POOL_SIZE=10
DATABASE_MAX_OVERFLOW=20
DATABASE_TIMEOUT=30

# Performance Monitoring
SLOW_QUERY_THRESHOLD_MS=100.0
ENABLE_QUERY_LOGGING=true
ENABLE_POOL_MONITORING=true
```

**Fallback:** Uses SQLite with sensible defaults

### 3. AI Configuration

```bash
# AI/LLM Settings
AI_ENABLED=true  # Set to false to disable AI features
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_DEFAULT_MODEL=llama2
AI_MAX_RESPONSE_LENGTH=1000
AI_CONTEXT_MESSAGES=10

# RAG (Retrieval Augmented Generation)
RAG_ENABLED=false  # Requires vector store
VECTOR_STORE_ENABLED=false
```

**Fallback:** AI features return placeholder responses when disabled

### 4. Voice Processing Configuration

```bash
# Text-to-Speech
TTS_ENABLED=false  # Requires TTS library
TTS_ENGINE=openai  # openai, gtts, google, azure, coqui
TTS_VOICE=alloy
TTS_FORMAT=mp3
TTS_API_KEY=  # Required for some engines
TTS_SPEED=1.0

# Speech-to-Text (Whisper)
WHISPER_ENABLED=false  # Requires Whisper
WHISPER_MODEL=base  # tiny, base, small, medium, large
WHISPER_LOCAL=true  # true for local, false for API
WHISPER_API_KEY=  # Required if WHISPER_LOCAL=false
WHISPER_LANGUAGE=auto

# Audio Processing
AUDIO_PROCESSING_ENABLED=true
MAX_AUDIO_SIZE=26214400  # 25MB
```

**Fallback:** Returns placeholder responses, basic file handling works

### 5. Elyza Model Configuration

```bash
# Japanese LLM Model
ELYZA_ENABLED=false
ELYZA_MODEL_PATH=elyza/ELYZA-japanese-Llama-2-7b
ELYZA_USE_GPU=false
ELYZA_MAX_LENGTH=512
ELYZA_TEMPERATURE=0.7
ELYZA_DEVICE=cpu  # cpu, cuda, mps
```

**Fallback:** Uses standard AI service when disabled

### 6. Plugin System Configuration

```bash
# Plugin System
PLUGINS_ENABLED=false
PLUGINS_DIR=plugins
PLUGINS_AUTO_LOAD=false
PLUGINS_SANDBOX_ENABLED=true  # Requires Docker
PLUGINS_TIMEOUT=30
PLUGINS_MAX_MEMORY=512m
```

**Fallback:** Plugins not loaded, core functionality unaffected

### 7. Monitoring & Observability

```bash
# Error Tracking (Sentry)
SENTRY_DSN=  # Optional error tracking

# Grafana Integration
GRAFANA_ENABLED=false
GRAFANA_URL=http://localhost:3000
GRAFANA_API_KEY=

# Distributed Tracing
TRACING_ENABLED=false
TRACING_PROVIDER=jaeger  # jaeger, zipkin, otlp
TRACING_ENDPOINT=http://localhost:14268/api/traces
TRACING_SAMPLE_RATE=0.1  # Sample 10% of requests
```

**Fallback:** System logs locally, basic monitoring via Prometheus

### 8. Testing Configuration

```bash
# Testing Features
PERFORMANCE_TESTS_ENABLED=false
SECURITY_TESTS_ENABLED=false
CONTRACT_TESTS_ENABLED=false

# Test Environment
TEST_DATABASE_URL=test_chat.db
TEST_LOG_LEVEL=WARNING
TEST_TIMEOUT=30
```

**Fallback:** Regular tests run normally, advanced tests skipped

### 9. Deployment Configuration

```bash
# CI/CD
CI_CD_ENABLED=false
CONTAINER_REGISTRY=ghcr.io
CONTAINER_REGISTRY_USER=
CONTAINER_REGISTRY_TOKEN=

# Deployment
DEPLOYMENT_ENVIRONMENT=production
AUTO_DEPLOY_ENABLED=false
DEPLOYMENT_APPROVAL_REQUIRED=true

# Release Automation
RELEASE_AUTOMATION_ENABLED=false
RELEASE_VERSION_STRATEGY=semver
```

**Fallback:** Manual deployment processes

### 10. Infrastructure Configuration

```bash
# Redis for Scaling
REDIS_ENABLED=false
REDIS_URL=redis://localhost:6379/0
REDIS_PUBSUB_ENABLED=false  # For multi-instance WebSocket

# Object Storage
OBJECT_STORAGE_ENABLED=false
OBJECT_STORAGE_PROVIDER=s3  # s3, minio, local
OBJECT_STORAGE_BUCKET=chat-system
OBJECT_STORAGE_ENDPOINT=
OBJECT_STORAGE_ACCESS_KEY=
OBJECT_STORAGE_SECRET_KEY=
```

**Fallback:** Single instance mode, local file storage

### 11. Feature Flags

```bash
# Core Features
FEATURE_PROJECT_MANAGEMENT=true
FEATURE_TICKET_SYSTEM=true
FEATURE_FILE_UPLOAD=true
FEATURE_USER_AUTHENTICATION=false  # Enable in production!
WEBSOCKET_ENABLED=true
```

**Fallback:** Features disabled when set to false

### 12. Security Configuration

```bash
# Security Settings
RATE_LIMIT_ENABLED=true
RATE_LIMIT_REQUESTS=100
RATE_LIMIT_WINDOW=60  # seconds

# File Upload Security
MAX_FILE_SIZE=10485760  # 10MB
ALLOWED_EXTENSIONS=["jpg", "jpeg", "png", "gif", "pdf", "txt"]
```

**Fallback:** Default security measures active

## Configuration Access Patterns

### In Python Code

```python
from config.settings import (
    settings,
    ai_config,
    voice_config,
    plugin_config,
    monitoring_config,
    infrastructure_config
)

# Access settings
if settings.AI_ENABLED:
    model = ai_config.default_model

# Check feature flags
if voice_config.tts_enabled:
    # TTS functionality
    pass

# Infrastructure checks
if infrastructure_config.redis_enabled:
    # Use Redis
    pass
```

### Service-Level Configuration

```python
from services.storage_service import get_storage_service

storage = get_storage_service()

# Check if using fallback
if storage.get_status()["fallback_mode"]:
    print("Using local storage (fallback)")
else:
    print(f"Using {storage.provider} object storage")
```

## Configuration Validation

### Startup Validation

The system automatically validates configuration at startup:

```python
from config.settings import validate_environment

# Validates configuration and logs warnings
is_valid = validate_environment()
```

### Runtime Health Checks

```python
# Check service health
from services.health_service import get_health_status

health = await get_health_status()
# Returns status of all configured services
```

## Environment-Specific Configurations

### Development

```bash
# .env.development
APP_ENVIRONMENT=development
APP_DEBUG=true
FEATURE_USER_AUTHENTICATION=false
AI_ENABLED=true
TRACING_SAMPLE_RATE=1.0  # 100% sampling
```

### Staging

```bash
# .env.staging
APP_ENVIRONMENT=staging
APP_DEBUG=false
FEATURE_USER_AUTHENTICATION=true
GRAFANA_ENABLED=true
TRACING_ENABLED=true
TRACING_SAMPLE_RATE=0.5  # 50% sampling
```

### Production

```bash
# .env.production
APP_ENVIRONMENT=production
APP_DEBUG=false
FEATURE_USER_AUTHENTICATION=true
SENTRY_DSN=<your-sentry-dsn>
GRAFANA_ENABLED=true
TRACING_ENABLED=true
TRACING_SAMPLE_RATE=0.01  # 1% sampling
REDIS_ENABLED=true
OBJECT_STORAGE_ENABLED=true
```

## Configuration Best Practices

1. **Start Simple:** Use defaults for development
2. **Environment Files:** Keep `.env` out of version control
3. **Secure Secrets:** Never commit secrets to git
4. **Document Changes:** Document why configuration changed
5. **Test Fallbacks:** Verify system works with features disabled
6. **Monitor Configuration:** Log configuration at startup
7. **Validate Early:** Fail fast on invalid configuration

## Troubleshooting

### Configuration Not Applied

**Check:**
1. Restart application after .env changes
2. Environment variables override .env file
3. Check for typos in variable names
4. Verify .env file location

### Feature Not Working

**Check:**
1. Feature enabled in configuration
2. Dependencies installed
3. External services running
4. Check application logs
5. Verify fallback mode status

### Performance Issues

**Check:**
1. Database pool size
2. Redis connection pool
3. Tracing sample rate (lower if high)
4. Query logging enabled (disable in prod if slow)

## Related Documentation

- [.env.example](../.env.example) - Complete configuration template
- [Settings Source](../config/settings.py) - Configuration implementation
- [Feature Flags](../FEATURE_FLAGS.md) - Feature flag documentation
- Individual feature guides in `docs/` directory

## Quick Reference

### Check Current Configuration

```python
from config.settings import settings

# Print all settings
print(settings.dict())

# Check specific setting
print(f"AI Enabled: {settings.AI_ENABLED}")
```

### Generate Secure Secret

```bash
# Python
python -c "import secrets; print(secrets.token_urlsafe(32))"

# OpenSSL
openssl rand -base64 32
```

### Validate Configuration

```bash
# Run configuration check
python -c "from config.settings import validate_environment; validate_environment()"
```

## Summary

**Key Points:**
- ✅ All features optional and configurable
- ✅ Graceful fallback for all services
- ✅ Works out-of-the-box with minimal config
- ✅ Progressive enhancement as you add features
- ✅ No errors when features disabled
- ✅ Centralized configuration management

**Remember:** The system is designed to work with minimal configuration. Add features incrementally as needed.
