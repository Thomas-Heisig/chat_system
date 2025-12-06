# 🏗️ Architecture Documentation / Architektur-Dokumentation

## 📚 Complete Architecture Documentation / Vollständige Architekturdokumentation

For comprehensive architecture documentation, please see:  
Für umfassende Architekturdokumentation siehe:

**[🏗️ Complete Architecture Documentation](docs/05-architecture/README.md)**

This includes / Dies beinhaltet:
- System Architecture / Systemarchitektur
- Design Patterns and Principles / Entwurfsmuster und Prinzipien
- Technology Stack / Technologie-Stack
- Architecture Decision Records (ADRs) / Architekturentscheidungen
- Component Architecture / Komponentenarchitektur

## Quick Links / Schnellzugriff

- **[System Architecture](docs/05-architecture/system-architecture.md)** - High-level design
- **[Technology Stack](docs/05-architecture/technology-stack.md)** - Technologies used
- **[Design Principles](docs/05-architecture/design-principles.md)** - Architectural principles
- **[ADRs](docs/05-architecture/adr/README.md)** - Architecture decisions

---

## Überblick / Overview

Das Chat System ist eine modulare, skalierbare Anwendung basierend auf FastAPI mit Echtzeit-WebSocket-Kommunikation, KI-Integration und Enterprise-Features.

The Chat System is a modular, scalable application based on FastAPI with real-time WebSocket communication, AI integration, and enterprise features.

## Systemarchitektur

### High-Level Architektur

```
┌─────────────────────────────────────────────────────────────┐
│                      Client Layer                            │
│  (Web Browser, Mobile Apps, API Clients)                    │
└─────────────────────────────────────────────────────────────┘
                            │
                            ↓
┌─────────────────────────────────────────────────────────────┐
│                      API Gateway                             │
│  (FastAPI mit CORS, Rate Limiting, Authentication)          │
└─────────────────────────────────────────────────────────────┘
                            │
        ┌───────────────────┼───────────────────┐
        ↓                   ↓                   ↓
┌──────────────┐   ┌──────────────┐   ┌──────────────┐
│   Routes     │   │  WebSocket   │   │    Admin     │
│   Layer      │   │   Manager    │   │  Dashboard   │
└──────────────┘   └──────────────┘   └──────────────┘
        │                   │                   │
        └───────────────────┼───────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│                    Service Layer                             │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐      │
│  │ Message  │ │   AI     │ │   RAG    │ │  Plugin  │      │
│  │ Service  │ │ Service  │ │ Service  │ │ Manager  │      │
│  └──────────┘ └──────────┘ └──────────┘ └──────────┘      │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐      │
│  │   Wiki   │ │Dictionary│ │  Elyza   │ │   File   │      │
│  │ Service  │ │ Service  │ │ Service  │ │ Service  │      │
│  └──────────┘ └──────────┘ └──────────┘ └──────────┘      │
└─────────────────────────────────────────────────────────────┘
                            │
        ┌───────────────────┼───────────────────┐
        ↓                   ↓                   ↓
┌──────────────┐   ┌──────────────┐   ┌──────────────┐
│   Database   │   │    Redis     │   │   Vector     │
│  (SQLite/    │   │   (Cache)    │   │     DB       │
│  PostgreSQL) │   │              │   │  (ChromaDB)  │
└──────────────┘   └──────────────┘   └──────────────┘
        │                   │                   │
        └───────────────────┼───────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│              External Services (Optional)                    │
│   ┌─────────┐  ┌─────────┐  ┌─────────┐  ┌─────────┐      │
│   │ Ollama  │  │ OpenAI  │  │  Elyza  │  │  S3/    │      │
│   │   AI    │  │   API   │  │   API   │  │ Storage │      │
│   └─────────┘  └─────────┘  └─────────┘  └─────────┘      │
└─────────────────────────────────────────────────────────────┘
```

## Komponenten-Beschreibung

### 1. API Gateway (main.py)

**Verantwortlichkeiten:**
- Request Routing
- CORS-Handling
- Rate Limiting
- Authentication/Authorization
- Request/Response Logging
- Error Handling

**Technologien:**
- FastAPI
- Uvicorn ASGI Server
- SlowAPI für Rate Limiting

### 2. Routes Layer

Organisiert API-Endpunkte nach funktionalen Bereichen:

- **chat.py**: Chat-Interface und Echtzeit-Kommunikation
- **messages.py**: Nachrichten-CRUD-Operationen
- **dictionary.py**: Wörterbuch/Glossar-Funktionalität
- **wiki.py**: Wiki-System für Dokumentation
- **rag.py**: RAG (Retrieval Augmented Generation) Funktionen
- **settings.py**: System-Einstellungen
- **admin.py**: Admin-Dashboard
- **plugins.py**: Plugin-Management
- **database.py**: Datenbank-Verwaltung

### 3. Service Layer

Geschäftslogik und Datenverarbeitung:

#### MessageService
- Nachrichtenverarbeitung
- AI-Integration
- Kontext-Management
- Error Handling mit ExternalAIUnavailableError

#### AIService
- Integration mit Ollama/OpenAI
- Prompt-Engineering
- Response-Verarbeitung
- Token-Management

#### ElyzaService
- Fallback-Mechanismus für AI-Ausfälle
- Feature Flag: ENABLE_ELYZA_FALLBACK
- Einfache regelbasierte Antworten
- Keine externen API-Abhängigkeiten

#### RAGService
- Dokument-Verarbeitung
- Embedding-Generierung
- Semantische Suche
- Vector Store Management

#### DictionaryService
- Begriffsverwaltung
- Auto-Completion
- Synonyme und Kategorien

#### WikiService
- Seiten-Verwaltung
- Versionshistorie
- Volltext-Suche

### 4. Data Layer

#### Database Adapters
Pluggable Architektur für verschiedene Datenbanken:

- **SQLiteAdapter**: Lokale Entwicklung, kleine Deployments
- **PostgresAdapter**: Produktions-Deployment, horizontal skalierbar
- **MongoDBAdapter**: Dokumenten-basierte Daten, flexible Schemas

#### Vector Database
- **ChromaDB**: Primäre Vector Store
- **Qdrant**: Alternative für größere Deployments
- **Pinecone**: Cloud-basierte Option

### 5. WebSocket Manager

**Features:**
- Bidirektionale Echtzeit-Kommunikation
- Connection Pool Management
- Message Broadcasting
- Room-basierte Kommunikation
- Auto-Reconnect Handling

## Datenfluss

### Nachricht Senden (mit AI)

```
Client
  │
  ├─→ POST /api/messages
  │     │
  │     ↓
  │   MessageRoute
  │     │
  │     ↓
  │   MessageService
  │     │
  │     ├─→ Repository.save(message)
  │     │     │
  │     │     ↓
  │     │   Database
  │     │
  │     ├─→ AIService.generate_response()
  │     │     │
  │     │     ├─→ Ollama (primär)
  │     │     │     │
  │     │     │     ↓ (bei Fehler)
  │     │     │   throw ExternalAIUnavailableError
  │     │     │
  │     │     └─→ ElyzaService (fallback, wenn ENABLE_ELYZA_FALLBACK=true)
  │     │
  │     └─→ WebSocketManager.broadcast()
  │           │
  │           ↓
  │         Connected Clients
```

### RAG Query

```
Client
  │
  ├─→ POST /api/rag/query
  │     │
  │     ↓
  │   RAGRoute
  │     │
  │     ↓
  │   RAGService
  │     │
  │     ├─→ EmbeddingModel.encode(query)
  │     │     │
  │     │     ↓
  │     │   Query Embedding
  │     │
  │     ├─→ VectorDB.search(embedding)
  │     │     │
  │     │     ↓
  │     │   Relevant Documents
  │     │
  │     └─→ AIService.generate(context + query)
  │           │
  │           ↓
  │         Contextualized Response
```

## Sicherheitsarchitektur

### Authentifizierung
- JWT-basierte Token-Authentifizierung
- bcrypt Passwort-Hashing
- Token-Refresh-Mechanismus
- Session-Management

### Autorisierung
- Role-Based Access Control (RBAC)
- Resource-basierte Permissions
- Admin vs. User Rollen

### Datenschutz
- Verschlüsselte Passwörter
- Sichere Session-Tokens
- CORS-Konfiguration
- Rate Limiting gegen DDoS

### API-Sicherheit
- Input-Validierung mit Pydantic
- SQL-Injection-Schutz durch ORM
- XSS-Schutz durch Template-Engine
- CSRF-Token für State-Changing Operations

## Skalierbarkeit

### Horizontal Scaling
- Stateless API Server (mehrere Instanzen möglich)
- Load Balancer vor API-Servern
- Shared Database und Redis
- WebSocket-Sticky-Sessions

### Vertical Scaling
- Database Connection Pooling
- Async I/O für hohe Concurrency
- Caching-Layer mit Redis
- Background Task Queue mit Celery

### Performance-Optimierungen
- Lazy Loading von Ressourcen
- Database Indexing
- Query-Optimierung
- Response-Compression
- Static Asset CDN

## Deployment-Optionen

### 1. Docker Compose (Entwicklung)
```yaml
services:
  - app (FastAPI)
  - db (PostgreSQL)
  - redis (Cache)
  - ollama (AI)
```

### 2. Kubernetes (Produktion)
```
Deployments:
  - chat-system-api (3 replicas)
  - postgres (StatefulSet)
  - redis (StatefulSet)
  - ollama (optional)

Services:
  - API Service (LoadBalancer)
  - Internal Services (ClusterIP)

ConfigMaps & Secrets:
  - app-config
  - db-credentials
  - api-keys
```

### 3. Serverless (optional)
- AWS Lambda + API Gateway
- Google Cloud Run
- Azure Functions

## Monitoring & Observability

### Logging
- Strukturierte Logs mit structlog
- Log Levels: DEBUG, INFO, WARNING, ERROR, CRITICAL
- Zentralisiertes Logging (z.B. ELK Stack)

### Metriken
- Prometheus-Metriken exportieren
- Grafana-Dashboards
- Custom Metrics:
  - Request Rate
  - Response Time
  - Error Rate
  - AI Response Time
  - Database Query Time

### Tracing
- Distributed Tracing mit Jaeger/Zipkin
- Request-ID Propagation
- Performance Bottleneck-Identifikation

### Health Checks
- `/health` - Basis Health Check
- `/health/ready` - Readiness Check
- `/health/live` - Liveness Check
- Dependency Checks (DB, Redis, AI)

## Feature Flags

Feature Flags ermöglichen schrittweise Rollouts und A/B-Testing:

- `ENABLE_ELYZA_FALLBACK`: Aktiviert Elyza-Fallback bei AI-Ausfall
- `AI_ENABLED`: Schaltet AI-Features ein/aus
- `RAG_ENABLED`: RAG-Funktionalität
- `FEATURE_PROJECT_MANAGEMENT`: Projekt-Management
- `FEATURE_TICKET_SYSTEM`: Ticket-System
- `FEATURE_USER_AUTHENTICATION`: Benutzer-Authentifizierung

## Migration & Upgrades

### Datenbank-Migrationen
- Alembic für Schema-Migrationen
- Versionierte Migrations-Skripte
- Rollback-Fähigkeit

### Zero-Downtime Deployment
1. Blue-Green Deployment
2. Rolling Updates in Kubernetes
3. Database-First Migration Strategy
4. Backward-Compatible API Changes

## Technologie-Stack

### Backend
- **Framework**: FastAPI 0.104+
- **ASGI Server**: Uvicorn
- **Python**: 3.10+
- **Async**: asyncio, aiofiles, httpx

### Database
- **Relational**: PostgreSQL / SQLite
- **NoSQL**: MongoDB (optional)
- **Vector DB**: ChromaDB, Qdrant
- **Cache**: Redis

### AI/ML
- **LLM**: Ollama (llama2, mistral, etc.)
- **Embeddings**: sentence-transformers
- **Fallback**: Elyza (regelbasiert)

### Frontend (außerhalb dieses Docs)
- HTML/CSS/JavaScript
- WebSocket-Client
- Jinja2 Templates

### DevOps
- **Container**: Docker
- **Orchestration**: Kubernetes
- **CI/CD**: GitHub Actions
- **Monitoring**: Prometheus + Grafana
- **Logging**: ELK Stack

## Best Practices

### Code-Organisation
- Klare Trennung von Routes, Services, Models
- Dependency Injection für Services
- Type Hints überall
- Docstrings für alle Public APIs

### Testing
- Unit Tests für Services
- Integration Tests für API-Endpunkte
- E2E Tests für kritische User Flows
- Mocking externer Abhängigkeiten

### Error Handling
- Custom Exceptions für Domänen-Fehler
- Globaler Exception Handler
- Detaillierte Error-Responses
- Logging aller Errors

### Performance
- Async/Await für I/O-Operationen
- Connection Pooling
- Query-Optimierung
- Caching häufiger Requests

## Erweiterbarkeit

### Plugin-System
- Dynamisches Laden von Plugins
- Plugin-Registry
- Lifecycle Hooks
- Isolated Plugin Execution

### API-Versionierung
- URL-basierte Versionierung (/api/v1/, /api/v2/)
- Header-basierte Versionierung (Accept: application/vnd.api+json;version=1)
- Deprecation-Prozess

### Integration-Punkte
- Webhooks für Events
- REST API für externe Systeme
- GraphQL-Gateway (optional)
- Message Queue für Async Processing

## Glossar

- **RAG**: Retrieval Augmented Generation - AI-Technik mit Kontext-Suche
- **Vector DB**: Datenbank für hochdimensionale Vektoren
- **Embedding**: Numerische Repräsentation von Text
- **WebSocket**: Bidirektionales Kommunikationsprotokoll
- **ASGI**: Asynchronous Server Gateway Interface
- **JWT**: JSON Web Token für Authentifizierung
