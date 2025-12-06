# Reference Documentation

Additional reference materials and resources for the Universal Chat System.

## 📋 Table of Contents

### Technical Reference
1. [Configuration Reference](configuration-reference.md) - Complete config options
2. [Environment Variables](environment-variables.md) - All environment variables
3. [Command Reference](command-reference.md) - CLI commands and scripts
4. [Error Codes](error-codes.md) - Error code reference

### Feature Documentation
5. [Feature Flags](feature-flags.md) - Feature flag documentation
6. [RAG System](rag-system.md) - Vector database and RAG details
7. [Voice Processing](voice-processing.md) - TTS and transcription
8. [ELYZA Model](elyza-model.md) - Local AI model documentation
9. [Workflow Automation](workflow-automation.md) - Workflow system
10. [Plugin System](plugin-system.md) - Plugin development
11. [Integration System](integration-system.md) - External integrations

### Database Reference
12. [Database Schema](database-schema.md) - Complete database schema
13. [Models Reference](models-reference.md) - Data model documentation
14. [Repository Pattern](repository-pattern.md) - Repository implementation
15. [Migration Guide](migration-guide.md) - Database migrations

### Component Reference
16. [WebSocket Protocol](websocket-protocol.md) - WebSocket event reference
17. [Service Components](service-components.md) - Service layer details
18. [Route Handlers](route-handlers.md) - API route documentation
19. [Middleware](middleware.md) - Middleware components

### Development Resources
20. [Development Tools](development-tools.md) - Tools and utilities
21. [Testing Framework](testing-framework.md) - Test infrastructure
22. [Performance Benchmarks](performance-benchmarks.md) - Performance data
23. [Security Guidelines](security-guidelines.md) - Security best practices

### Project Information
24. [Changelog](../../CHANGES.md) - Version history
25. [Release Notes](../../RELEASE_NOTES.md) - Release information
26. [Roadmap](../../ROADMAP.md) - Future plans
27. [Migration Notes](../../MIGRATION_NOTES.md) - Version migration guide

### Planning & Status
28. [TODO List](../../TODO.md) - Current and planned tasks
29. [Known Issues](../../ISSUES.md) - Known problems
30. [Improvements](../../IMPROVEMENTS.md) - Planned improvements
31. [Test Coverage](../../TEST_COVERAGE.md) - Testing status

## Quick Reference

### Common Configuration

#### Development
```bash
APP_ENVIRONMENT=development
APP_DEBUG=true
DATABASE_TYPE=sqlite
DATABASE_URL=sqlite:///./chat.db
```

#### Production
```bash
APP_ENVIRONMENT=production
APP_DEBUG=false
DATABASE_TYPE=postgresql
DATABASE_URL=postgresql://user:pass@localhost:5432/chatdb
```

### Key Features Status

| Feature | Status | Documentation | Priority |
|---------|--------|---------------|----------|
| Real-time Chat | ✅ Available | [WebSocket Protocol](websocket-protocol.md) | - |
| Project Management | ✅ Available | [Projects](../02-user-guide/projects.md) | - |
| RAG System | ✅ Available | [RAG System](rag-system.md) | - |
| AI Integration | ✅ Available | [AI Integration](../03-developer-guide/ai-integration.md) | - |
| Voice Processing | ⏸️ Planned | [Voice Processing](voice-processing.md) | High |
| ELYZA Model | ⏸️ Planned | [ELYZA Model](elyza-model.md) | High |
| Workflow Automation | ⏸️ Planned | [Workflow Automation](workflow-automation.md) | Medium |
| External Integrations | ⏸️ Planned | [Integration System](integration-system.md) | Medium |
| Plugin System | ⏸️ Planned | [Plugin System](plugin-system.md) | Medium |

### Technology Stack

#### Backend
- **Framework**: FastAPI 0.104+
- **Language**: Python 3.9+
- **ORM**: SQLAlchemy
- **Authentication**: JWT (PyJWT)
- **WebSocket**: FastAPI WebSocket
- **Testing**: pytest

#### Database
- **Relational**: SQLite, PostgreSQL
- **Document**: MongoDB
- **Vector**: ChromaDB, Qdrant, Pinecone

#### AI & ML
- **LLM**: Ollama, OpenAI
- **RAG**: ChromaDB, Qdrant, Pinecone
- **Local Model**: ELYZA (planned)

#### Frontend
- **Templates**: Jinja2
- **CSS**: Custom + Bootstrap
- **JavaScript**: Vanilla JS
- **WebSocket Client**: Native WebSocket API

#### Infrastructure
- **Containerization**: Docker
- **Orchestration**: Kubernetes (optional)
- **Monitoring**: Prometheus, Grafana (optional)
- **Logging**: Python logging + JSON

### Directory Structure

```
chat_system/
├── agents/               # Agent framework and examples
├── analytics/            # Event tracking and A/B testing
├── config/              # Configuration management
├── core/                # Core utilities
├── database/            # Database layer (models, repos, adapters)
├── docs/                # Documentation (this directory)
│   ├── 01-getting-started/
│   ├── 02-user-guide/
│   ├── 03-developer-guide/
│   ├── 04-api-reference/
│   ├── 05-architecture/
│   ├── 06-operations/
│   ├── 07-contributing/
│   └── 08-reference/
├── elyza/               # ELYZA model integration
├── frontend/            # Frontend source (if separate)
├── integration/         # External service integrations
├── k8s/                 # Kubernetes manifests
├── memory/              # Memory and personalization
├── routes/              # API route handlers
├── services/            # Business logic services
│   └── rag/            # RAG system implementations
├── static/              # Static assets (CSS, JS, images)
├── templates/           # Jinja2 HTML templates
├── tests/               # Test suite
│   ├── unit/
│   ├── integration/
│   └── e2e/
├── utils/               # Utility functions
├── voice/               # Voice processing framework
├── websocket/           # WebSocket handlers
├── workflow/            # Workflow automation
├── workspace/           # Workspace management
├── main.py              # Application entry point
├── requirements.txt     # Python dependencies
├── pyproject.toml       # Project metadata
└── docker-compose.yml   # Docker orchestration
```

## External Resources

### Official Links
- **Repository**: https://github.com/Thomas-Heisig/chat_system
- **Issue Tracker**: https://github.com/Thomas-Heisig/chat_system/issues
- **Discussions**: https://github.com/Thomas-Heisig/chat_system/discussions

### Related Projects
- **FastAPI**: https://fastapi.tiangolo.com/
- **SQLAlchemy**: https://www.sqlalchemy.org/
- **Ollama**: https://ollama.ai/
- **ChromaDB**: https://www.trychroma.com/

### Standards & Specifications
- **OpenAPI**: https://swagger.io/specification/
- **WebSocket**: https://datatracker.ietf.org/doc/html/rfc6455
- **JWT**: https://jwt.io/
- **REST**: https://restfulapi.net/

## Quick Links

- **Main Documentation**: [Documentation Index](../README.md)
- **Getting Started**: [Installation Guide](../01-getting-started/README.md)
- **Developer Guide**: [Development Documentation](../03-developer-guide/README.md)
- **API Reference**: [API Documentation](../04-api-reference/README.md)

---

**Version:** 2.0.0  
**Last Updated:** 2025-12-06  
**Language:** English | [Deutsch](README.de.md)
