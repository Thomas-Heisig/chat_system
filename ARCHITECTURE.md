# 🏗️ Chat System - Architektur-Dokumentation

## Übersicht

Das Chat System ist ein hochmodulares, erweiterbares Echtzeit-Chat-System mit KI-Integration, RAG-Funktionalität und Enterprise-Features. Die Architektur folgt dem Layered Architecture Pattern mit klarer Trennung von Verantwortlichkeiten.

## Systemarchitektur

```
┌─────────────────────────────────────────────────────────┐
│                    Client Layer                          │
│  (Web Browser, WebSocket Clients, API Consumers)        │
└─────────────────────────────────────────────────────────┘
                         ↓
┌─────────────────────────────────────────────────────────┐
│                  API Gateway Layer                       │
│              (FastAPI, CORS, Rate Limiting)              │
└─────────────────────────────────────────────────────────┘
                         ↓
┌─────────────────────────────────────────────────────────┐
│                   Routes Layer                           │
│  /chat  /dictionary  /wiki  /plugins  /virtual_rooms    │
└─────────────────────────────────────────────────────────┘
                         ↓
┌─────────────────────────────────────────────────────────┐
│                  Services Layer                          │
│  MessageService  DictionaryService  WikiService          │
│  ElyzaService  PluginService  VirtualRoomService         │
│  AvatarService  EmotionDetection  FileService            │
└─────────────────────────────────────────────────────────┘
                         ↓
┌─────────────────────────────────────────────────────────┐
│                Core Business Logic                       │
│  Authentication  Authorization  RBAC  Validation         │
└─────────────────────────────────────────────────────────┘
                         ↓
┌─────────────────────────────────────────────────────────┐
│                  Data Layer                              │
│  PostgreSQL  Redis  Vector DB (ChromaDB/Qdrant)         │
│  File Storage (S3-compatible)                            │
└─────────────────────────────────────────────────────────┘
```

## Komponenten-Details

### 1. API Gateway Layer
- **FastAPI Framework**: Hochperformantes, async-fähiges Web-Framework
- **CORS Middleware**: Cross-Origin Resource Sharing für Web-Clients
- **Rate Limiting**: Schutz vor Überlastung und Missbrauch
- **Authentication Middleware**: JWT-basierte Authentifizierung

### 2. Routes Layer
Alle API-Endpunkte sind in separate Router-Module organisiert:

- **`routes/chat.py`**: Hauptchat-Funktionen, WebSocket-Endpunkte
- **`routes/dictionary.py`**: Wörterbuch- und Glossar-Management
- **`routes/wiki.py`**: Wiki und Dokumentations-Management
- **`routes/plugins.py`**: Plugin-System und Erweiterungen
- **`routes/virtual_rooms.py`**: Virtuelle Räume für erweiterte Zusammenarbeit

### 3. Services Layer

#### MessageService
- Nachrichtenverwaltung und -verarbeitung
- WebSocket-Verbindungsverwaltung
- AI-Integration mit Fallback-Mechanismus
- Externe AI-Services (Ollama, OpenAI) mit Elyza-Fallback

#### DictionaryService
- Begriffsverwaltung und Glossar
- Auto-Vervollständigung
- Multi-Sprach-Unterstützung
- Synonyme und verwandte Begriffe

#### WikiService
- Wiki-Seiten Erstellung und Bearbeitung
- Versionshistorie und Rollback
- Volltextsuche
- Kategorisierung und Tagging

#### ElyzaService
- Lokaler AI-Fallback Service
- Regelbasierte Konversations-Engine
- Offline-Funktionalität
- Konfigurierbar über `ENABLE_ELYZA_FALLBACK` ENV-Variable

#### PluginService
- Sandboxed Plugin-Ausführung
- Plugin-Registry und Lebenszyklus-Management
- Sicherheits-Isolation
- TODO: Container-basierte Sandbox-Implementierung

#### VirtualRoomService
- 3D/VR-Raum-Management
- Avatar-Positionierung und -Interaktion
- Raum-Persistierung
- Echtzeit-Synchronisation

#### AvatarService
- Avatar-Erstellung und -Verwaltung
- Anpassungen und Skins
- Animations-Management
- TODO: Integration mit 3D-Rendering-Engine

#### EmotionDetection
- Emotionserkennung aus Text
- Sentiment-Analyse
- Stimmungsbasierte Reaktionen
- TODO: ML-Modell-Integration

#### GestureRecognition
- Gesten-Erkennung für VR-Interaktionen
- TODO: Kamera-basierte Gestenerkennung
- TODO: Integration mit WebRTC

#### FileService
- Datei-Upload und -Download
- Speicher-Management (lokal/S3-kompatibel)
- Virus-Scanning
- Metadaten-Extraktion

### 4. Core Layer

#### Authentication (`core/auth.py`)
- JWT Token-Generierung und -Validierung
- Passwort-Hashing mit bcrypt
- Role-Based Access Control (RBAC)
- Permission Management
- TODO: OAuth2-Provider-Integration

#### Configuration
- Environment-basierte Konfiguration
- Feature Flags
- Dynamische Einstellungen

### 5. Data Layer

#### Primary Database (PostgreSQL)
- Hauptdatenbank für strukturierte Daten
- Benutzer, Nachrichten, Projekte, Tickets
- Transaktionale Integrität
- TODO: Migration von SQLite zu PostgreSQL

#### Cache Layer (Redis)
- Session-Management
- Rate-Limiting-Counter
- Pub/Sub für Echtzeit-Events
- WebSocket-Connection-Registry
- TODO: Redis-Integration implementieren

#### Vector Database (ChromaDB/Qdrant)
- RAG-System für Dokumenten-Embeddings
- Semantische Suche
- Ähnlichkeitssuche
- TODO: Produktions-ready Vector DB (Qdrant/Pinecone)

#### Object Storage
- Datei-Uploads
- Avatar-Assets
- Plugin-Bundles
- TODO: S3-kompatible Storage-Integration

## Datenfluss

### Chat-Nachricht Fluss
```
Client → WebSocket Connection → WebSocketHandler → MessageService
                                                    ↓
                                    [AI Processing Optional]
                                    ↓              ↓
                            ElyzaService     External AI (Ollama)
                                    ↓              ↓
                                    └──────┬───────┘
                                           ↓
                                    MessageRepository
                                           ↓
                                    Database (Persist)
                                           ↓
                            Broadcast to Connected Clients
```

### RAG Query Fluss
```
User Query → RAG Endpoint → RAG Service
                                ↓
                    Generate Embedding (OpenAI/Local)
                                ↓
                    Vector Database Query (ChromaDB)
                                ↓
                    Retrieve Relevant Documents
                                ↓
                    Context Augmentation
                                ↓
                    AI Model (with Context)
                                ↓
                    Response to User
```

## Sicherheitsarchitektur

### Authentication Flow
```
1. User Login → Credentials
2. Verify Password (bcrypt)
3. Generate JWT Token
4. Return Token to Client
5. Client includes Token in subsequent requests
6. Middleware validates Token
7. Extract User & Permissions
8. Allow/Deny based on RBAC
```

### RBAC Model
- **Roles**: admin, moderator, user, guest
- **Permissions**: read, write, delete, manage
- **Resource-Level**: Per-resource permission checks

### API Security
- Rate Limiting: 100 requests/minute default
- CORS: Configurable origin whitelist
- Input Validation: Pydantic models
- XSS Protection: Content sanitization
- SQL Injection: ORM-basierte Queries

## Skalierbarkeit

### Horizontal Scaling
- Stateless Application Design
- Session-State in Redis
- Load Balancer (nginx/Kubernetes Ingress)
- Multiple App Instances

### WebSocket Scaling
- Redis Pub/Sub für Cross-Instance Communication
- Sticky Sessions für WebSocket Connections
- Connection Registry in Redis

### Database Scaling
- Read Replicas für PostgreSQL
- Connection Pooling
- Query Optimization
- Caching Strategy

## Deployment-Strategie

### Container-basiert (Docker)
```
- App Container: Python/FastAPI
- Database Container: PostgreSQL
- Cache Container: Redis
- Vector DB Container: ChromaDB/Qdrant
- Nginx/Traefik: Reverse Proxy
```

### Kubernetes (Production)
```
- Deployment: App Pods (3+ replicas)
- StatefulSet: Database
- Service: Internal networking
- Ingress: External access
- ConfigMaps: Configuration
- Secrets: Credentials
```

## Monitoring & Observability

### Logging
- Structured Logging (structlog)
- Log Levels: DEBUG, INFO, WARNING, ERROR
- Correlation IDs für Request-Tracking

### Metrics (TODO)
- Prometheus Metrics Export
- Request Rate, Latency, Error Rate
- Custom Business Metrics

### Tracing (TODO)
- Distributed Tracing (OpenTelemetry)
- End-to-End Request Tracing

### Health Checks
- `/health` - Basic health
- `/health/detailed` - Component health
- Database connectivity
- External service availability

## Erweiterbarkeit

### Plugin-System
- Sandboxed Execution
- Plugin API
- Lifecycle Hooks
- Event System

### Webhook-Integration (TODO)
- Outgoing Webhooks für Events
- Incoming Webhooks für Integrationen

### API Versioning (TODO)
- `/api/v1/...`, `/api/v2/...`
- Backward Compatibility

## Technologie-Stack

### Backend
- **Framework**: FastAPI 0.104+
- **Language**: Python 3.10+
- **ASGI Server**: Uvicorn
- **ORM**: SQLAlchemy 2.0+

### Database
- **Primary**: PostgreSQL 15+ (aktuell SQLite für Dev)
- **Cache**: Redis 7+
- **Vector**: ChromaDB / Qdrant

### AI/ML
- **LLM**: Ollama (lokal), OpenAI API
- **Embeddings**: sentence-transformers
- **Fallback**: Elyza (regelbasiert)

### Frontend (nicht im aktuellen Scope)
- Static HTML/CSS/JS
- WebSocket Client

### DevOps
- **Container**: Docker
- **Orchestration**: Kubernetes
- **CI/CD**: GitHub Actions
- **Monitoring**: Prometheus + Grafana (geplant)

## Umgebungsvariablen

### Erforderlich
```bash
DATABASE_URL=postgresql://user:pass@host:5432/chatdb
REDIS_URL=redis://localhost:6379/0
SECRET_KEY=your-secret-key-here
```

### Optional
```bash
ENABLE_ELYZA_FALLBACK=true
AI_ENABLED=true
OLLAMA_BASE_URL=http://localhost:11434
STORAGE_REGION=eu-central-1
VECTOR_DB_TYPE=chromadb
```

## Entwicklungs-Roadmap

### Phase 1: Core Chat (✅ Completed)
- Basic Chat-Funktionalität
- WebSocket Support
- Datenbank-Integration

### Phase 2: AI Integration (🚧 In Progress)
- Ollama Integration
- RAG System
- Elyza Fallback

### Phase 3: Enterprise Features (📋 Planned)
- RBAC Implementation
- PostgreSQL Migration
- Redis Integration
- Audit Logging

### Phase 4: Advanced Features (📋 Planned)
- Virtual Rooms (3D/VR)
- Plugin System
- Emotion Detection
- Gesture Recognition

### Phase 5: Production Hardening (📋 Planned)
- Kubernetes Deployment
- Monitoring & Alerting
- Performance Optimization
- Security Audit

## Bekannte Einschränkungen

1. **SQLite als Development DB**: Migration zu PostgreSQL erforderlich für Production
2. **In-Memory WebSocket Registry**: Benötigt Redis für Multi-Instance Deployment
3. **Lokale Datei-Speicherung**: S3-kompatible Storage erforderlich für Production
4. **Keine Persistente Vector DB**: ChromaDB-Daten gehen bei Container-Neustart verloren
5. **Einfache Authentication**: OAuth2/SSO-Integration fehlt noch

## Lizenz & Support

Siehe LICENSE-Datei für Details.

---
*Letzte Aktualisierung: 2025-12-02*
