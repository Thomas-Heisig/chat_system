# Feature Flags Configuration

## Übersicht

Das Chat System verwendet Feature Flags, um Funktionen gezielt zu aktivieren oder deaktivieren. Dies ermöglicht flexible Deployments und einfacheres Testing.

## Feature Flags

### 1. FEATURE_USER_AUTHENTICATION

**Status**: Standardmäßig `False` (Development), sollte `True` sein in Production

**Beschreibung**:
- Aktiviert das vollständige User-Authentication-System
- Umfasst JWT-Token-Management, Session-Handling, bcrypt-Passwort-Hashing

**Implementation Status**: ✅ **Vollständig implementiert**
- Services: `services/auth_service.py`
- JWT-Token-Generierung und -Validierung
- Passwort-Hashing mit bcrypt
- Session-Management
- Role-based Access Control (RBAC)

**Evaluierung (2024-12-05)**: ✅ **System ist produktionsreif**
- Service vollständig implementiert
- Keine bekannten Blocker
- **Empfehlung**: Kann aktiviert werden, wenn Authentifizierung benötigt wird
- **Test Coverage**: 0% (Keine Tests vorhanden - Tests sollten vor Production geschrieben werden)

**Warum standardmäßig deaktiviert?**
- Einfachere lokale Entwicklung ohne Login-Requirement
- Schnelleres Testing ohne Auth-Overhead
- Vermeidung von Auth-Problemen bei Initial Setup

**Wann aktivieren?**
```bash
# In .env für Production:
FEATURE_USER_AUTHENTICATION=True

# Oder via Umgebungsvariable:
export FEATURE_USER_AUTHENTICATION=True
```

**Aktivierung empfohlen für**:
- ✅ Production Deployments
- ✅ Staging Environments
- ✅ Security-sensitive Deployments
- ❌ Lokale Entwicklung (optional)
- ❌ Automated Testing (optional)

**Nächste Schritte vor Production-Aktivierung**:
1. Tests für AuthService schreiben (siehe TEST_COVERAGE.md)
2. Default Admin-Passwort ändern (siehe SECURITY.md)
3. APP_SECRET_KEY auf sicheren Wert setzen
4. HTTPS in Production aktivieren

**Dependencies**:
- `python-jose[cryptography]` - JWT Token Handling
- `passlib[bcrypt]` - Password Hashing
- Konfiguriert in `config/settings.py`

**Sicherheitshinweis**:
⚠️ Wenn aktiviert, stellen Sie sicher:
- Default Admin-Passwort wurde geändert
- `APP_SECRET_KEY` ist auf einen sicheren Wert gesetzt
- HTTPS ist in Production aktiviert

---

### 2. RAG_ENABLED

**Status**: Standardmäßig `False`

**Beschreibung**:
- Aktiviert RAG (Retrieval Augmented Generation)
- Ermöglicht AI-Antworten basierend auf eigenem Knowledge Base

**Implementation Status**: ✅ **Vollständig implementiert**
- Services: `services/rag/base_rag.py`, `services/rag/chroma_rag.py`
- Vector Store Integration (ChromaDB/Qdrant)
- Document Embedding und Retrieval
- Context-aware AI Responses

**Evaluierung (2024-12-05)**: ⚠️ **Benötigt externe Dependencies**
- Services vollständig implementiert (ChromaDB, Qdrant)
- **Empfehlung**: Aktivieren sobald Vector Store verfügbar ist
- **Test Coverage**: 0% für alle RAG Services (keine Tests vorhanden)
- **Blocker**: Benötigt laufenden Vector Store (ChromaDB oder Qdrant)

**Warum standardmäßig deaktiviert?**
- Benötigt externe Vector Store (ChromaDB oder Qdrant)
- Erhöhter Memory- und CPU-Bedarf
- Optional für Basis-Chat-Funktionalität

**Wann aktivieren?**
```bash
# 1. Vector Store Setup (ChromaDB Beispiel):
docker run -d -p 8001:8000 chromadb/chroma

# 2. In .env aktivieren:
RAG_ENABLED=True
VECTOR_STORE_ENABLED=True
VECTOR_STORE_TYPE=chroma
VECTOR_STORE_HOST=localhost
VECTOR_STORE_PORT=8001
```

**Dependencies**:
- ChromaDB oder Qdrant Vector Store
- Embedding Models (z.B. sentence-transformers)
- Ausreichend RAM (min. 4GB empfohlen)

**Nächste Schritte für Aktivierung**:
1. Vector Store (ChromaDB/Qdrant) als Docker Container starten
2. Tests für RAG Services schreiben (siehe TEST_COVERAGE.md)
3. Document-Indexierung durchführen
4. RAG_ENABLED=True in .env setzen
5. Funktionalität testen mit echten Dokumenten

---

### 3. FEATURE_PROJECT_MANAGEMENT

**Status**: Standardmäßig `True`

**Beschreibung**:
- Aktiviert das Project Management System
- Ermöglicht Erstellung und Verwaltung von Projekten

**Implementation Status**: ✅ **Vollständig implementiert**
- Models: `database/models.py` (Project Model)
- Repositories: `database/repositories.py` (ProjectRepository)
- Full CRUD Operations

**Wann deaktivieren?**
- Wenn nur Chat-Funktionalität benötigt wird
- Für minimale Deployments

```bash
# In .env:
FEATURE_PROJECT_MANAGEMENT=False
```

---

### 4. FEATURE_TICKET_SYSTEM

**Status**: Standardmäßig `True`

**Beschreibung**:
- Aktiviert das Ticket/Issue-Tracking-System
- Ermöglicht Bug-Tracking, Feature-Requests, etc.

**Implementation Status**: ✅ **Vollständig implementiert**
- Models: `database/models.py` (Ticket Model)
- Repositories: `database/repositories.py` (TicketRepository)
- Status-Management, Priority-Levels, Assignment

**Wann deaktivieren?**
- Wenn externes Ticket-System verwendet wird (Jira, GitHub Issues)
- Für minimale Deployments

```bash
# In .env:
FEATURE_TICKET_SYSTEM=False
```

---

### 5. FEATURE_FILE_UPLOAD

**Status**: Standardmäßig `True`

**Beschreibung**:
- Aktiviert File-Upload-Funktionalität
- Ermöglicht Datei-Sharing im Chat

**Implementation Status**: ✅ **Vollständig implementiert**
- Services: `services/file_service.py`
- File Type Validation
- Size Limits (konfigurierbar)
- Secure Storage

**Wann deaktivieren?**
- Security-Bedenken (siehe Issue #15 - Virus Scanning TODO)
- Storage-Beschränkungen
- Wenn externe File-Sharing-Lösung verwendet wird

```bash
# In .env:
FEATURE_FILE_UPLOAD=False
```

**Sicherheitshinweis**:
⚠️ Aktuell **KEIN** Virus-Scanning implementiert (siehe Issue #15)
- In Production: Externe Malware-Scanning-Lösung empfohlen
- Alternative: Deaktivieren und externe File-Sharing-Lösung verwenden

**Konfiguration**:
```bash
UPLOAD_FOLDER=uploads
MAX_FILE_SIZE=10485760  # 10MB in Bytes
ALLOWED_EXTENSIONS=jpg,jpeg,png,gif,pdf,txt,doc,docx
```

---

### 6. AI_ENABLED

**Status**: Standardmäßig `True`

**Beschreibung**:
- Aktiviert AI-powered Chat-Responses
- Ollama Integration für lokale LLMs

**Implementation Status**: ✅ **Vollständig implementiert**
- Services: `services/ai_service.py`
- Ollama Integration
- Multiple Model Support
- Fallback-Mechanismen

**Dependencies**:
- Ollama muss installiert und laufend sein
- Mindestens ein Model muss gedownloaded sein (z.B. llama2)

```bash
# Ollama Setup:
# 1. Ollama installieren: https://ollama.ai
# 2. Model herunterladen: ollama pull llama2
# 3. Ollama starten (läuft meist automatisch)

# In .env:
AI_ENABLED=True
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_DEFAULT_MODEL=llama2
```

**Wann deaktivieren?**
- Ollama nicht verfügbar
- Nur menschliche Chat-Funktionalität gewünscht
- Resource-Constraints (AI benötigt CPU/GPU)

---

### 7. WEBSOCKET_ENABLED

**Status**: Standardmäßig `True`

**Beschreibung**:
- Aktiviert WebSocket-Support für Real-time Chat
- Ermöglicht Live-Updates ohne Polling

**Implementation Status**: ✅ **Vollständig implementiert**
- WebSocket-Handler in `websocket/`
- Connection Management
- Message Broadcasting

**Wann deaktivieren?**
- Bei Proxy-Problemen (manche Proxies blockieren WebSockets)
- Für REST-only API

```bash
# In .env:
WEBSOCKET_ENABLED=False
```

---

## Entwicklung vs. Production

### Development Setup (Default)
```bash
# .env für Development
FEATURE_USER_AUTHENTICATION=False  # Kein Login erforderlich
RAG_ENABLED=False                  # Keine Vector Store Dependencies
AI_ENABLED=True                    # Wenn Ollama läuft
FEATURE_PROJECT_MANAGEMENT=True
FEATURE_TICKET_SYSTEM=True
FEATURE_FILE_UPLOAD=True
WEBSOCKET_ENABLED=True
```

### Production Setup (Empfohlen)
```bash
# .env für Production
FEATURE_USER_AUTHENTICATION=True   # ⚠️ WICHTIG für Security!
RAG_ENABLED=True                   # Wenn Vector Store verfügbar
AI_ENABLED=True
FEATURE_PROJECT_MANAGEMENT=True
FEATURE_TICKET_SYSTEM=True
FEATURE_FILE_UPLOAD=True           # Nur mit Virus-Scanning!
WEBSOCKET_ENABLED=True

# Security-Settings
APP_SECRET_KEY=<secure-random-key>
APP_ENVIRONMENT=production
APP_DEBUG=False
RATE_LIMIT_ENABLED=True
```

---

## Feature Flag Best Practices

### 1. Environment-Specific Configuration
```bash
# .env.development
FEATURE_USER_AUTHENTICATION=False

# .env.production
FEATURE_USER_AUTHENTICATION=True
```

### 2. Runtime Feature Detection
```python
from config.settings import settings

if settings.FEATURE_USER_AUTHENTICATION:
    # Implement auth middleware
    pass
else:
    # Skip auth checks
    pass
```

### 3. Graceful Degradation
```python
# System funktioniert auch wenn Features deaktiviert sind
if settings.AI_ENABLED:
    response = await ai_service.generate_response(message)
else:
    response = "AI-Funktionalität ist deaktiviert"
```

### 4. Documentation
- Alle Feature Flags dokumentieren
- Deployment-Guide für jedes Feature
- Dependencies klar auflisten

---

## Zukünftige Features

### In Planung
- `FEATURE_2FA` - Two-Factor Authentication
- `FEATURE_OAUTH` - OAuth2 Integration (Google, GitHub)
- `FEATURE_E2E_ENCRYPTION` - End-to-End Encryption
- `FEATURE_VIDEO_CHAT` - Video Call Integration
- `FEATURE_VOICE_MESSAGES` - Voice Message Support (currently mock)

### Experimentell
- `FEATURE_PLUGIN_SYSTEM` - Plugin Architecture (partially implemented)
- `FEATURE_WORKFLOW_AUTOMATION` - Automation Pipelines (TODO)
- `FEATURE_ANALYTICS` - Advanced Analytics Dashboard

---

## Troubleshooting

### Problem: Feature Flag hat keine Wirkung
**Lösung**:
1. Server neu starten nach .env-Änderungen
2. Prüfen ob .env-Datei gelesen wird: `python -c "from config.settings import settings; print(settings.FEATURE_USER_AUTHENTICATION)"`
3. Environment-Variable könnte .env überschreiben

### Problem: Authentication aktiviert, aber Login funktioniert nicht
**Lösung**:
1. Default Admin-User existiert: `admin` / `admin123`
2. JWT-Dependencies installiert: `pip install python-jose[cryptography] passlib[bcrypt]`
3. APP_SECRET_KEY gesetzt in .env

### Problem: RAG aktiviert, aber Vector Store nicht erreichbar
**Lösung**:
1. Vector Store läuft: `docker ps | grep chroma` oder `docker ps | grep qdrant`
2. Konfiguration korrekt: VECTOR_STORE_HOST, VECTOR_STORE_PORT
3. Network-Zugriff überprüfen

---

**Zuletzt aktualisiert**: 2024-12-05  
**Version**: 2.0.0

Für weitere Informationen siehe:
- `SECURITY.md` - Security Guidelines
- `SETUP.md` - Installation und Setup
- `config/settings.py` - Komplette Konfiguration
