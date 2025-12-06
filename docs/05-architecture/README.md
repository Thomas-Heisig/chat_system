# Architecture Documentation

Comprehensive architectural documentation for the Universal Chat System.

## 📋 Table of Contents

### Overview
1. [System Architecture](system-architecture.md) - High-level system design
2. [Technology Stack](technology-stack.md) - Technologies and frameworks
3. [Design Principles](design-principles.md) - Architectural principles and patterns

### Core Architecture
4. [Application Layer](application-layer.md) - FastAPI application structure
5. [Data Layer](data-layer.md) - Database architecture and patterns
6. [Service Layer](service-layer.md) - Business logic organization
7. [Presentation Layer](presentation-layer.md) - UI and API design

### Components
8. [WebSocket Architecture](websocket-architecture.md) - Real-time communication design
9. [RAG System Architecture](rag-architecture.md) - Vector databases and semantic search
10. [Authentication System](authentication-architecture.md) - Security and auth design
11. [Plugin System](plugin-architecture.md) - Extensibility architecture

### Integration
12. [External Systems](external-systems.md) - Integration patterns
13. [Messaging Bridge](messaging-bridge.md) - Multi-platform messaging
14. [AI Integration](ai-integration-arch.md) - AI service architecture

### Data & Storage
15. [Database Strategy](database-strategy.md) - Multi-database support
16. [Caching Strategy](caching-strategy.md) - Performance optimization
17. [File Storage](file-storage.md) - File management architecture

### Architecture Decision Records
18. [ADR Index](adr/README.md) - All architectural decisions
    - [ADR-001: FastAPI Framework](adr/ADR-001-fastapi-framework.md)
    - [ADR-002: SQLAlchemy ORM](adr/ADR-002-sqlalchemy-orm.md)
    - [ADR-003: JWT Authentication](adr/ADR-003-jwt-authentication.md)
    - [ADR-004: WebSocket Real-time](adr/ADR-004-websocket-realtime.md)
    - [ADR-005: Vector Database Choice](adr/ADR-005-vector-database-choice.md)
    - [ADR-006: Plugin Sandbox](adr/ADR-006-plugin-sandbox-architecture.md)
    - [ADR-007: Multi-Database Support](adr/ADR-007-multi-database-support.md)
    - [ADR-008: Performance Optimization](adr/ADR-008-performance-optimization-strategy.md)
    - [ADR-009: Security Enhancement](adr/ADR-009-security-enhancement-strategy.md)

## System Overview

### High-Level Architecture

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

### Key Design Patterns

- **Repository Pattern**: Database abstraction and data access
- **Service Layer Pattern**: Business logic separation
- **Dependency Injection**: Loose coupling between components
- **Factory Pattern**: Database adapter creation
- **Observer Pattern**: WebSocket event handling
- **Strategy Pattern**: Multiple AI providers and vector databases

### Technology Choices

| Component | Technology | ADR |
|-----------|-----------|-----|
| Web Framework | FastAPI | [ADR-001](adr/ADR-001-fastapi-framework.md) |
| ORM | SQLAlchemy | [ADR-002](adr/ADR-002-sqlalchemy-orm.md) |
| Authentication | JWT | [ADR-003](adr/ADR-003-jwt-authentication.md) |
| Real-time | WebSocket | [ADR-004](adr/ADR-004-websocket-realtime.md) |
| Vector DB | ChromaDB/Qdrant/Pinecone | [ADR-005](adr/ADR-005-vector-database-choice.md) |
| Plugin Isolation | Docker | [ADR-006](adr/ADR-006-plugin-sandbox-architecture.md) |
| Multi-DB | Adapter Pattern | [ADR-007](adr/ADR-007-multi-database-support.md) |

## Quick Links

- **Developer Guide**: [Development Documentation](../03-developer-guide/README.md)
- **API Reference**: [API Documentation](../04-api-reference/README.md)
- **Operations**: [Deployment & Operations](../06-operations/README.md)

---

**Version:** 2.0.0  
**Last Updated:** 2025-12-06  
**Language:** English | [Deutsch](README.de.md)
