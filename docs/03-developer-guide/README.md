# Developer Guide

Comprehensive documentation for developers working on the Universal Chat System.

## 📋 Table of Contents

### Getting Started
1. [Development Setup](development-setup.md) - Setting up your development environment
2. [Project Structure](project-structure.md) - Understanding the codebase
3. [Coding Standards](coding-standards.md) - Code style and best practices
4. [Testing Guide](testing-guide.md) - Writing and running tests

### Core Components
5. [Database Layer](database-layer.md) - Models, repositories, and adapters
6. [Service Layer](service-layer.md) - Business logic and services
7. [API Routes](api-routes.md) - REST endpoints and handlers
8. [WebSocket System](websocket-system.md) - Real-time communication

### Advanced Topics
9. [RAG System](rag-system.md) - Vector databases and semantic search
10. [AI Integration](ai-integration.md) - AI service providers and models
11. [Plugin Development](plugin-development.md) - Creating plugins
12. [Workflow System](workflow-system.md) - Automation and orchestration

### Integration & Extension
13. [External Integrations](external-integrations.md) - Slack, Teams, Discord
14. [Voice Processing](voice-processing-dev.md) - TTS and transcription
15. [Custom Services](custom-services.md) - Adding new services

## Development Resources

### Code Quality Tools
- **Formatter**: Black (line length: 100)
- **Import Sorter**: isort (profile: black)
- **Linter**: flake8
- **Type Checker**: mypy
- **Testing**: pytest with coverage

### Quick Commands
```bash
# Format code
black --line-length 100 .
isort --profile black .

# Check code quality
flake8 .
mypy .

# Run tests
pytest
pytest --cov=. --cov-report=html

# Run development server
python main.py
```

### Architecture Patterns

- **Repository Pattern**: Database abstraction
- **Service Layer**: Business logic separation
- **Dependency Injection**: Loose coupling
- **Event-Driven**: WebSocket and messaging
- **Modular Design**: Plugin architecture

## Component Reference

### Directory Structure
```
chat_system/
├── agents/          # Agent framework
├── config/          # Configuration management
├── database/        # Database layer
├── routes/          # API endpoints
├── services/        # Business logic
├── websocket/       # Real-time communication
├── templates/       # Frontend templates
└── main.py          # Application entry point
```

## Quick Links

- **Architecture**: [Architecture Documentation](../05-architecture/README.md)
- **API Reference**: [API Documentation](../04-api-reference/README.md)
- **Contributing**: [Contribution Guidelines](../07-contributing/README.md)
- **ADRs**: [Architecture Decision Records](../05-architecture/adr/README.md)

---

**Version:** 2.0.0  
**Last Updated:** 2025-12-06  
**Language:** English | [Deutsch](README.de.md)
