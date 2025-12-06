# API Reference

Complete API documentation for the Universal Chat System.

## 📋 Table of Contents

### API Overview
1. [API Introduction](api-intro.md) - Getting started with the API
2. [Authentication](authentication.md) - JWT authentication and authorization
3. [Rate Limiting](rate-limiting.md) - API rate limits and quotas
4. [Error Handling](error-handling.md) - Error responses and status codes

### Endpoints

#### Core APIs
5. [Chat API](chat-api.md) - Real-time chat endpoints
6. [Messages API](messages-api.md) - Message management
7. [Files API](files-api.md) - File upload and management
8. [Users API](users-api.md) - User management

#### Project Management
9. [Projects API](projects-api.md) - Project operations
10. [Tickets API](tickets-api.md) - Ticket system
11. [Comments API](comments-api.md) - Comments and discussions

#### AI & Intelligence
12. [RAG API](rag-api.md) - Retrieval-augmented generation
13. [AI Models API](ai-models-api.md) - AI model selection and configuration
14. [Voice API](voice-api.md) - Text-to-speech and transcription

#### Administration
15. [Settings API](settings-api.md) - System configuration
16. [Database API](database-api.md) - Database operations
17. [Monitoring API](monitoring-api.md) - Health checks and metrics

### WebSocket Protocol
18. [WebSocket Events](websocket-events.md) - Real-time event protocol
19. [Connection Management](connection-management.md) - WebSocket lifecycle

### Code Examples
20. [API Examples](api-examples.md) - Usage examples in multiple languages

## Interactive Documentation

When running the application in development mode, interactive API documentation is available at:

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **OpenAPI Schema**: http://localhost:8000/openapi.json

## Base URL

Development: `http://localhost:8000`  
Production: `https://your-domain.com`

## Authentication

All protected endpoints require JWT authentication via the `Authorization` header:

```
Authorization: Bearer <your-jwt-token>
```

Get a token by calling the login endpoint:
```bash
POST /api/auth/login
{
  "username": "your-username",
  "password": "your-password"
}
```

## Response Format

### Success Response
```json
{
  "success": true,
  "data": { ... },
  "message": "Operation completed successfully"
}
```

### Error Response
```json
{
  "error": true,
  "message": "Error description",
  "status_code": 400,
  "details": { ... }
}
```

## Rate Limits

| Endpoint Type | Rate Limit | Window |
|--------------|------------|--------|
| Authentication | 5 requests | 1 minute |
| General API | 100 requests | 1 minute |
| WebSocket | 1000 messages | 1 minute |
| File Upload | 10 uploads | 1 hour |

## Quick Links

- **Getting Started**: [Installation Guide](../01-getting-started/README.md)
- **User Guide**: [User Documentation](../02-user-guide/README.md)
- **Developer Guide**: [Developer Documentation](../03-developer-guide/README.md)

---

**Version:** 2.0.0  
**Last Updated:** 2025-12-06  
**Language:** English | [Deutsch](README.de.md)
