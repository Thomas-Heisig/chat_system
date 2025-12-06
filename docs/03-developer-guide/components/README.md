# Component Documentation

Technical documentation for all system components.

## 📋 Component Index

### Configuration
- [Config Settings](README_config-settings.md) - Configuration management
- [Config Validation](README_config-validation.md) - Settings validation

### Database Layer
- [Database Connection](README_database-connection.md) - Connection management and pooling
- [Database Models](README_database-models.md) - SQLAlchemy models and schemas
- [Database Repositories](README_database-repositories.md) - Repository pattern implementation

### API Routes
- [Chat Routes](README_routes-chat.md) - Chat and WebSocket endpoints
- [Message Routes](README_routes-messages.md) - Message API endpoints

### Services
- [Message Service](README_services-message_service.md) - Message processing and management
- [File Service](README_services-file_service.md) - File upload and management
- [Project Service](README_services-project_service.md) - Project and ticket management

### WebSocket
- [WebSocket Handlers](README_websocket-handlers.md) - WebSocket event handlers
- [WebSocket Manager](README_websocket-manager.md) - Connection management

### Frontend
- [Templates](README_templates-index.md) - Jinja2 templates
- [JavaScript Chat](README_static-js-chat.md) - Client-side chat implementation
- [CSS Styling](README_static-css-style.md) - Stylesheet documentation

### Main Application
- [Main Application](README_main.md) - Application entry point and setup

## Component Architecture

```
Application (main.py)
│
├── Routes Layer
│   ├── Chat Routes
│   ├── Message Routes
│   ├── Settings Routes
│   └── Admin Routes
│
├── Service Layer
│   ├── Message Service
│   ├── File Service
│   ├── Project Service
│   ├── AI Service
│   └── RAG Service
│
├── Database Layer
│   ├── Models (SQLAlchemy)
│   ├── Repositories
│   └── Connection Manager
│
├── WebSocket Layer
│   ├── WebSocket Manager
│   └── WebSocket Handlers
│
└── Frontend Layer
    ├── Templates (Jinja2)
    ├── Static Assets
    └── JavaScript Modules
```

## Component Dependencies

### Database Components
- **Models** → Define data structures
- **Repositories** → Access data (uses Models)
- **Connection** → Manage DB connections

### Service Components
- **Message Service** → Uses Message Repository
- **File Service** → Uses File Repository  
- **Project Service** → Uses Project and Ticket Repositories

### Route Components
- **Chat Routes** → Uses Message Service, WebSocket Manager
- **Message Routes** → Uses Message Service
- **Settings Routes** → Uses Config Service

### WebSocket Components
- **WebSocket Manager** → Manages connections
- **WebSocket Handlers** → Process events (uses Services)

## Quick Links

- **[Developer Guide](../README.md)** - Back to developer guide
- **[Testing Guide](../testing-guide.md)** - Testing these components
- **[API Reference](../../04-api-reference/README.md)** - API documentation

---

**Version:** 2.0.0  
**Last Updated:** 2025-12-06  
**Language:** English
