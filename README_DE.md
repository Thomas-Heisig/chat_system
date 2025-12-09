# Universal Chat System - Deutsche Dokumentation

[![Python](https://img.shields.io/badge/Python-3.9%2B-blue.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.104%2B-009688.svg)](https://fastapi.tiangolo.com/)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

Ein modernes, modulares Enterprise-Chat-System mit KI-Integration, RAG-Funktionen (Retrieval-Augmented Generation), Echtzeit-WebSocket-Kommunikation und umfassenden Projektmanagement-Features.

**🌍 Andere Sprachen:** [English](README.md)

---

## 🎯 Überblick

Das Universal Chat System ist eine vollwertige Enterprise-Kommunikationsplattform, die Echtzeit-Chat mit fortschrittlichen KI-Funktionen, Dokumenten-Intelligence durch RAG-Systeme und robusten Projektmanagement-Tools kombiniert. Mit FastAPI entwickelt und für Skalierbarkeit konzipiert, bietet es eine vollständige Lösung für Teams, die intelligente, kontextbewusste Kommunikation benötigen.

### Wichtige Highlights

- 🚀 **Echtzeit-Kommunikation** - WebSocket-basierter Chat mit niedriger Latenz
- 🤖 **KI-Integration** - Unterstützung für Ollama, OpenAI und benutzerdefinierte KI-Modelle
- 📚 **RAG-System** - Semantische Suche mit ChromaDB, Qdrant und Pinecone
- 🔐 **Enterprise-Sicherheit** - JWT-Authentifizierung, bcrypt-Passwort-Hashing, Rate Limiting
- 🗄️ **Flexible Speicherung** - Unterstützung für SQLite, PostgreSQL und MongoDB
- 📊 **Projektmanagement** - Integriertes Ticketing-System mit Dateianhängen
- 🎨 **Moderne UI** - Tab-basiertes Admin-Dashboard mit Dunkel-/Hell-Themes
- 🐳 **Produktionsbereit** - Docker-Unterstützung, umfassendes Monitoring und Logging

---

## 📋 Inhaltsverzeichnis

- [Features](#-features)
- [Neuigkeiten](#-neuigkeiten)
- [Architektur](#-architektur)
- [Voraussetzungen](#-voraussetzungen)
- [Installation](#-installation)
- [Konfiguration](#️-konfiguration)
- [Verwendung](#-verwendung)
- [API-Dokumentation](#-api-dokumentation)
- [Entwicklung](#-entwicklung)
- [Tests](#-tests)
- [Deployment](#-deployment)
- [Sicherheit](#-sicherheit)
- [Dokumentation](#-dokumentation)
- [Beitragen](#-beitragen)
- [Lizenz](#-lizenz)
- [Support](#-support)

---

## ✨ Features

### Kern-Kommunikation
- **Echtzeit-Chat**: WebSocket-basiertes Messaging mit Connection-State-Management
- **Nachrichten-Typen**: Unterstützung für Benutzer-, KI-, System-, Befehls- und Benachrichtigungs-Nachrichten
- **Nachrichten-Kompression**: Automatische Kompression für große Nachrichten
- **Dateianhänge**: Upload und Teilen von Dokumenten, Bildern und anderen Dateien
- **Benutzerpräsenz**: Echtzeit-Online/Offline-Status-Tracking

### KI & Intelligence
- **Mehrere KI-Anbieter**: Nahtlose Integration mit Ollama, OpenAI und benutzerdefinierten Modellen
- **RAG (Retrieval-Augmented Generation)**: 
  - Mehrere Vektor-Datenbanken (ChromaDB, Qdrant, Pinecone)
  - Dokumentenverarbeitung mit konfigurierbarem Chunking
  - Semantische Suche mit Cosinus-Ähnlichkeit
  - Unterstützung für PDF, DOCX, TXT und Markdown-Dateien
- **Kontextbewusste Antworten**: KI nutzt Gesprächsverlauf und hochgeladene Dokumente
- **Modellauswahl**: Dynamisches Wechseln zwischen verschiedenen KI-Modellen

### Projekt- & Ticket-Management
- **Projektorganisation**: Erstellen und Verwalten mehrerer Projekte
- **Ticket-System**: 
  - Mehrere Ticket-Typen (Task, Bug, Feature, Question, Incident)
  - Prioritätsstufen (Low, Medium, High, Critical)
  - Status-Tracking (Open, In Progress, Resolved, Closed)
  - Zuweisung und Fälligkeitsdaten
- **Dateiverwaltung**: Anhängen von Dateien an Tickets und Projekte
- **Aktivitätsverfolgung**: Audit-Trail für alle Projektänderungen

### Sicherheit & Authentifizierung
- **JWT-Authentifizierung**: Sichere Token-basierte Authentifizierung
- **Passwort-Sicherheit**: bcrypt-Hashing mit konfigurierbaren Runden
- **Erzwungene Passwortänderung**: Administratoren müssen Standard-Passwörter bei der ersten Anmeldung ändern
- **Rollenbasierte Zugriffskontrolle**: Benutzer-, Moderator-, Manager- und Admin-Rollen
- **Rate Limiting**: Konfigurierbare API-Rate-Limitierung zur Missbrauchsprävention
- **CORS-Unterstützung**: Flexible Cross-Origin-Resource-Sharing-Konfiguration
- **Umfassende Security-Header**:
  - Content Security Policy mit Nonce-Unterstützung
  - X-Frame-Options, X-Content-Type-Options
  - Strict-Transport-Security (HSTS)
  - Referrer-Policy, Permissions-Policy
  - Entwicklungs- vs. Produktionskonfigurationen

### Admin-Dashboard
- **Tab-Interface**: 
  - Chat - Haupt-Kommunikationsschnittstelle
  - Einstellungen - Systemkonfiguration
  - RAG-System - Dokument- und Vektor-Datenbank-Management
  - Datenbank - Administration und Optimierung
  - Projekte - Projekt- und Ticket-Management
  - Dateien - Dateibrowser und -verwaltung
  - Benutzer - Benutzerverwaltung
  - Monitoring - Systemgesundheit und Protokolle
  - Integrationen - Externe Service-Verbindungen
- **Dunkel/Hell-Themes**: Benutzereinstellungsbasierte Themes
- **Echtzeit-Updates**: Live-Systemmetriken und Benachrichtigungen

---

## 🆕 Neuigkeiten

### Version 2.2.0 (Dezember 2025)

#### 🎉 Große Erfolge
- **Code-Qualität:** 99.4% Verbesserung (2825 → 16 Warnungen)
- **Test-Coverage:** Von 0% auf 11% (118 neue Tests)
- **Dokumentation:** 50+ neue Dokumente (~500KB)
- **Issues gelöst:** 20 von 24 (83%)

#### ✨ Neue Features
- **Voice Processing** - Vollständiges TTS, STT und Audio-Processing
- **ELYZA Model** - Integration für japanische Sprachmodelle
- **Workflow Automation** - 11 Step-Typen, sequentielle/parallele Ausführung
- **Slack Integration** - Vollständige API-Integration
- **Plugin System** - Docker-basiertes Plugin-Management

#### 🔧 Verbesserungen
- **Security Headers** - Vollständige CSP-Implementation
- **Performance** - 14 Database-Indexes, Query-Monitoring, Compression
- **Monitoring** - Prometheus Metrics, Grafana Dashboards, Distributed Tracing
- **Authentication** - Database-backed mit Last-Login-Tracking

#### 📚 Dokumentation
- 9 ADR-Dokumente (Architecture Decision Records)
- Umfassende Tutorial-Dokumentation (96KB)
- System-Dokumentation (72KB)
- Beispiel-Scripts (55KB)
- Technische Guides (50+ Dokumente)

Siehe [CHANGELOG.md](CHANGELOG.md) für vollständige Details.

---

## 🏗️ Architektur

### Technologie-Stack

**Backend:**
- **Framework:** FastAPI 0.104+
- **Python:** 3.9+
- **WebSocket:** Native FastAPI WebSocket-Unterstützung
- **Datenbank:** SQLite (Standard), PostgreSQL, MongoDB
- **ORM:** SQLAlchemy (für relationale DBs)
- **Authentifizierung:** JWT (python-jose), bcrypt
- **Caching:** Redis (optional)

**KI & RAG:**
- **LLM-Anbieter:** Ollama (Standard), OpenAI API
- **Vektor-Datenbanken:** ChromaDB (Standard), Qdrant, Pinecone
- **Embedding-Modelle:** OpenAI, Sentence Transformers
- **Dokumentenverarbeitung:** PyPDF2, python-docx, langchain

**Frontend:**
- **Template-Engine:** Jinja2
- **UI:** HTML5, CSS3, Vanilla JavaScript
- **WebSocket-Client:** Native Browser-WebSocket-API
- **Styling:** Benutzerdefinierte CSS mit Dunkel/Hell-Theme-Unterstützung

**DevOps:**
- **Container:** Docker, Docker Compose
- **Orchestrierung:** Kubernetes (optional)
- **CI/CD:** GitHub Actions
- **Monitoring:** Prometheus, Grafana, Sentry
- **Logging:** Python logging, strukturierte Logs

### System-Architektur

```
┌─────────────────────────────────────────────────────────────┐
│                    Frontend (Browser)                       │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐      │
│  │   Chat   │ │ Settings │ │    RAG   │ │ Projects │      │
│  └────┬─────┘ └────┬─────┘ └────┬─────┘ └────┬─────┘      │
└───────┼───────────┼────────────┼────────────┼─────────────┘
        │           │            │            │
        │  REST API │  WebSocket │  REST API  │
        ▼           ▼            ▼            ▼
┌─────────────────────────────────────────────────────────────┐
│                   FastAPI Application                        │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐      │
│  │  Routes  │ │WebSocket │ │ Services │ │   Core   │      │
│  │  Layer   │ │ Handlers │ │  Layer   │ │  Utils   │      │
│  └────┬─────┘ └────┬─────┘ └────┬─────┘ └────┬─────┘      │
└───────┼───────────┼────────────┼────────────┼─────────────┘
        │           │            │            │
        ▼           ▼            ▼            ▼
┌─────────────────────────────────────────────────────────────┐
│                   Persistence Layer                          │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐      │
│  │ Database │ │  Vector  │ │   Redis  │ │   File   │      │
│  │(SQLite)  │ │  Store   │ │  Cache   │ │ Storage  │      │
│  └──────────┘ └──────────┘ └──────────┘ └──────────┘      │
└─────────────────────────────────────────────────────────────┘
        │           │            │            │
        ▼           ▼            ▼            ▼
┌─────────────────────────────────────────────────────────────┐
│                  External Services                           │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐      │
│  │  Ollama  │ │  OpenAI  │ │   Slack  │ │ Prometheus│     │
│  │   LLM    │ │   API    │ │   API    │ │  Metrics │      │
│  └──────────┘ └──────────┘ └──────────┘ └──────────┘      │
└─────────────────────────────────────────────────────────────┘
```

Siehe [ARCHITECTURE.md](ARCHITECTURE.md) für detaillierte Informationen.

---

## 📦 Voraussetzungen

### Erforderlich
- **Python:** 3.9 oder höher
- **pip:** Python Package Manager
- **Git:** Für das Klonen des Repositories

### Optional (für erweiterte Features)
- **Docker:** Für Container-basiertes Deployment
- **Docker Compose:** Für Multi-Container-Orchestrierung
- **PostgreSQL:** Für Produktions-Datenbank (statt SQLite)
- **Redis:** Für Caching und Session-Management
- **Ollama:** Für lokale LLM-Ausführung
- **Node.js:** Für Frontend-Build-Tools (falls benötigt)

### Systemanforderungen

**Minimal (Entwicklung):**
- CPU: 2 Cores
- RAM: 4 GB
- Storage: 10 GB

**Empfohlen (Produktion):**
- CPU: 4+ Cores
- RAM: 8+ GB
- Storage: 50+ GB SSD
- Optional: GPU für lokale LLM-Inferenz

---

## 🚀 Installation

### Schnellstart

```bash
# Repository klonen
git clone https://github.com/Thomas-Heisig/chat_system.git
cd chat_system

# Virtuelle Umgebung erstellen
python -m venv venv
source venv/bin/activate  # Linux/Mac
# oder
venv\Scripts\activate  # Windows

# Abhängigkeiten installieren
pip install -r requirements.txt

# Umgebungsvariablen konfigurieren
cp .env.example .env
# .env-Datei bearbeiten und anpassen

# Datenbank initialisieren
python -m database.init_db

# Server starten
python main.py
```

Der Server läuft nun auf `http://localhost:8000`

### Docker Installation

```bash
# Repository klonen
git clone https://github.com/Thomas-Heisig/chat_system.git
cd chat_system

# Mit Docker Compose starten
docker-compose up -d

# Logs anzeigen
docker-compose logs -f
```

Siehe [SETUP.md](SETUP.md) für detaillierte Installationsanleitungen.

---

## ⚙️ Konfiguration

### Umgebungsvariablen

Die wichtigsten Konfigurationsoptionen in der `.env`-Datei:

```bash
# Server-Konfiguration
HOST=0.0.0.0
PORT=8000
DEBUG=false

# Datenbank
DATABASE_TYPE=sqlite  # sqlite, postgresql, mongodb
DATABASE_URL=sqlite:///./chat_system.db

# Authentifizierung
SECRET_KEY=your-secret-key-here
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=1440

# KI-Konfiguration
AI_PROVIDER=ollama  # ollama, openai
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=llama2

# RAG-System
RAG_ENABLED=true
VECTOR_DB_TYPE=chromadb  # chromadb, qdrant, pinecone
CHROMA_PERSIST_DIR=./chroma_db

# Voice Processing
TTS_ENGINE=openai  # openai, gtts, pyttsx3
STT_ENGINE=whisper  # whisper, whisper_api

# Monitoring
PROMETHEUS_ENABLED=true
SENTRY_DSN=your-sentry-dsn

# Sicherheit
RATE_LIMIT_ENABLED=true
RATE_LIMIT_REQUESTS=100
RATE_LIMIT_PERIOD=60
```

Siehe [CONFIGURATION_GUIDE.md](docs/CONFIGURATION_GUIDE.md) für alle Optionen.

---

## 📖 Verwendung

### Erste Schritte

1. **Server starten:**
   ```bash
   python main.py
   ```

2. **Browser öffnen:** Navigieren Sie zu `http://localhost:8000`

3. **Als Admin anmelden:**
   - Benutzername: `admin`
   - Passwort: `admin123` (beim ersten Login ändern!)

4. **Chat starten:** Wechseln Sie zum Chat-Tab und senden Sie Ihre erste Nachricht

### Grundlegende Workflows

#### Chat mit KI
```python
# Über Web-UI oder API
POST /api/messages
{
  "content": "Hallo, kannst du mir bei Python helfen?",
  "type": "user"
}
```

#### Dokument hochladen für RAG
```python
# Dokument hochladen
POST /api/rag/documents
Files: document.pdf

# Semantische Suche
POST /api/rag/search
{
  "query": "Was steht im Dokument über Python?",
  "top_k": 5
}
```

#### Projekt erstellen
```python
POST /api/projects
{
  "name": "Mein Projekt",
  "description": "Projektbeschreibung",
  "status": "active"
}
```

Siehe [BASIC_USAGE.md](BASIC_USAGE.md) für detaillierte Anleitungen.

---

## 📚 API-Dokumentation

### Interaktive API-Dokumentation

Nach dem Start des Servers ist die interaktive API-Dokumentation verfügbar unter:

- **Swagger UI:** `http://localhost:8000/docs`
- **ReDoc:** `http://localhost:8000/redoc`

### API-Übersicht

**Authentifizierung:**
- `POST /api/auth/login` - Benutzeranmeldung
- `POST /api/auth/register` - Benutzerregistrierung
- `POST /api/auth/refresh` - Token aktualisieren

**Nachrichten:**
- `GET /api/messages` - Nachrichten abrufen
- `POST /api/messages` - Nachricht senden
- `DELETE /api/messages/{id}` - Nachricht löschen

**RAG-System:**
- `POST /api/rag/documents` - Dokument hochladen
- `GET /api/rag/documents` - Dokumente auflisten
- `POST /api/rag/search` - Semantische Suche

**Projekte:**
- `GET /api/projects` - Projekte auflisten
- `POST /api/projects` - Projekt erstellen
- `GET /api/projects/{id}` - Projekt abrufen
- `PUT /api/projects/{id}` - Projekt aktualisieren

**WebSocket:**
- `WS /ws` - WebSocket-Verbindung für Echtzeit-Chat

Siehe [API_EXAMPLES.md](docs/API_EXAMPLES.md) für Code-Beispiele.

---

## 🛠️ Entwicklung

### Entwicklungsumgebung einrichten

```bash
# Repository klonen
git clone https://github.com/Thomas-Heisig/chat_system.git
cd chat_system

# Entwicklungs-Dependencies installieren
pip install -r requirements.txt

# Pre-commit Hooks installieren
pip install pre-commit
pre-commit install

# Tests ausführen
pytest

# Code-Qualität prüfen
flake8 .
black --check .
isort --check .
```

### Projektstruktur

```
chat_system/
├── main.py                 # Haupt-Anwendungseinstiegspunkt
├── config/                 # Konfigurationsdateien
├── core/                   # Kern-Funktionalität
│   ├── auth.py            # Authentifizierung
│   ├── dependencies.py    # Dependency Injection
│   └── error_handlers.py  # Error-Handling
├── routes/                 # API-Routen
│   ├── chat.py           # Chat-Endpoints
│   ├── auth.py           # Auth-Endpoints
│   └── rag.py            # RAG-Endpoints
├── services/              # Business-Logik
│   ├── ai_service.py     # AI-Integration
│   ├── rag_service.py    # RAG-System
│   └── project_service.py # Projektmanagement
├── database/              # Datenbankschicht
│   ├── models.py         # Datenmodelle
│   └── connection.py     # DB-Verbindung
├── websocket/            # WebSocket-Handler
├── tests/                # Unit- und Integrationstests
├── docs/                 # Dokumentation
└── templates/            # Frontend-Templates
```

Siehe [CONTRIBUTING.md](CONTRIBUTING.md) für Contribution-Richtlinien.

---

## 🧪 Tests

### Tests ausführen

```bash
# Alle Tests ausführen
pytest

# Mit Coverage-Report
pytest --cov=. --cov-report=html

# Spezifische Test-Suite
pytest tests/unit/
pytest tests/integration/

# Bestimmte Test-Datei
pytest tests/unit/test_auth.py

# Mit verbose Output
pytest -v
```

### Test-Coverage

Aktueller Status: **11% Overall Coverage** (118 Tests)

```bash
# Coverage-Report generieren
pytest --cov=. --cov-report=term --cov-report=html

# Report öffnen
open htmlcov/index.html
```

Siehe [TEST_COVERAGE.md](TEST_COVERAGE.md) und [Testing Guide](docs/TESTING_GUIDE.md).

---

## 🚢 Deployment

### Docker Deployment

```bash
# Image bauen
docker build -t chat-system:latest .

# Container starten
docker run -d \
  -p 8000:8000 \
  -v $(pwd)/data:/app/data \
  -e SECRET_KEY=your-secret-key \
  chat-system:latest

# Mit Docker Compose
docker-compose up -d
```

### Kubernetes Deployment

```bash
# Kubernetes-Manifests anwenden
kubectl apply -f k8s/

# Status prüfen
kubectl get pods
kubectl get services

# Logs anzeigen
kubectl logs -f deployment/chat-system
```

### Produktions-Checkliste

- [ ] Sicheren `SECRET_KEY` setzen
- [ ] Admin-Passwort ändern
- [ ] PostgreSQL für Produktion nutzen
- [ ] Redis für Caching konfigurieren
- [ ] HTTPS mit SSL/TLS aktivieren
- [ ] Rate Limiting aktivieren
- [ ] Monitoring einrichten (Prometheus/Grafana)
- [ ] Error Tracking konfigurieren (Sentry)
- [ ] Backup-Strategie implementieren
- [ ] Security Headers aktivieren

Siehe [DEPLOYMENT.md](DEPLOYMENT.md) für detaillierte Anleitungen.

---

## 🔒 Sicherheit

### Sicherheits-Features

- **JWT-Authentifizierung** mit sicherer Token-Verwaltung
- **bcrypt Password Hashing** (12 Runden)
- **Erzwungene Passwort-Änderung** für Standard-Admins
- **Rate Limiting** zur Missbrauchsprävention
- **CORS-Konfiguration** für sichere Cross-Origin-Requests
- **Security Headers:**
  - Content Security Policy (CSP)
  - X-Frame-Options: DENY
  - X-Content-Type-Options: nosniff
  - Strict-Transport-Security (HSTS)
  - Referrer-Policy
  - Permissions-Policy
- **Input-Validierung** mit Pydantic
- **SQL Injection Prevention** durch SQLAlchemy ORM
- **XSS-Schutz** durch Template-Escaping

### Sicherheits-Best-Practices

1. **Immer Standard-Passwörter ändern**
2. **HTTPS in Produktion verwenden**
3. **Regelmäßige Security-Updates**
4. **Starke Passwort-Richtlinien**
5. **Rate Limiting aktivieren**
6. **Logs überwachen**
7. **Backup-Strategie implementieren**

### Sicherheitsprobleme melden

Wenn Sie ein Sicherheitsproblem finden:
1. **NICHT** öffentlich als GitHub Issue melden
2. E-Mail an: security@example.com (vertraulich)
3. PGP-verschlüsselte Kommunikation bevorzugt

Siehe [SECURITY.md](SECURITY.md) für detaillierte Informationen.

---

## 📚 Dokumentation

### Haupt-Dokumentation

**Erste Schritte:**
- [GETTING_STARTED.md](GETTING_STARTED.md) - Schnellstart-Anleitung
- [BASIC_USAGE.md](BASIC_USAGE.md) - Grundlegende Verwendung
- [SETUP.md](SETUP.md) - Detaillierte Installation

**Features:**
- [AI_INTEGRATION.md](AI_INTEGRATION.md) - KI und RAG-System
- [ADVANCED_FEATURES.md](ADVANCED_FEATURES.md) - Erweiterte Funktionen
- [TASK_SYSTEM.md](TASK_SYSTEM.md) - Projektmanagement

**Entwicklung:**
- [ARCHITECTURE.md](ARCHITECTURE.md) - System-Architektur
- [CONTRIBUTING.md](CONTRIBUTING.md) - Contribution-Richtlinien
- [docs/README.md](docs/README.md) - Dokumentations-Index

**Technische Guides:**
- [docs/VOICE_PROCESSING.md](docs/VOICE_PROCESSING.md) - Voice Processing
- [docs/PLUGIN_SYSTEM.md](docs/PLUGIN_SYSTEM.md) - Plugin-Entwicklung
- [docs/WORKFLOW_AUTOMATION.md](docs/WORKFLOW_AUTOMATION.md) - Workflows
- [docs/PERFORMANCE.md](docs/PERFORMANCE.md) - Performance-Optimierung
- [docs/MONITORING.md](docs/MONITORING.md) - Monitoring & Observability

**Architecture Decision Records (ADRs):**
- [docs/adr/](docs/adr/) - Architektur-Entscheidungen dokumentiert

### Beispiele

- [examples/ai_chat_example.py](examples/ai_chat_example.py) - KI-Chat-Integration
- [examples/rag_document_example.py](examples/rag_document_example.py) - RAG-System
- [examples/websocket_client_example.py](examples/websocket_client_example.py) - WebSocket-Client

---

## 🤝 Beitragen

Wir freuen uns über Beiträge! Hier ist wie Sie helfen können:

### Contribution-Prozess

1. **Fork** das Repository
2. **Clone** Ihren Fork
3. **Branch** erstellen für Ihr Feature
4. **Changes** implementieren mit Tests
5. **Commit** mit beschreibender Nachricht
6. **Push** zu Ihrem Fork
7. **Pull Request** erstellen

### Entwicklungs-Workflow

```bash
# Fork klonen
git clone https://github.com/IHR-USERNAME/chat_system.git
cd chat_system

# Branch erstellen
git checkout -b feature/mein-neues-feature

# Änderungen machen und testen
# ...

# Committen
git add .
git commit -m "feat: Neues Feature hinzugefügt"

# Pushen
git push origin feature/mein-neues-feature

# Pull Request auf GitHub erstellen
```

### Code-Standards

- **Code-Style:** Black (line length 100)
- **Import-Organisation:** isort
- **Linting:** flake8
- **Type Hints:** Verwenden Sie Type Hints wo möglich
- **Docstrings:** Google-Style Docstrings
- **Tests:** Mindestens 80% Coverage für neue Features

### Commit-Nachrichten

Folgen Sie den [Conventional Commits](https://www.conventionalcommits.org/):

```
feat: Neue Funktion hinzufügen
fix: Bug beheben
docs: Dokumentation aktualisieren
style: Code-Formatierung
refactor: Code-Refactoring
test: Tests hinzufügen
chore: Build-Prozess, Dependencies
```

Siehe [CONTRIBUTING.md](CONTRIBUTING.md) für detaillierte Richtlinien.

---

## 📄 Lizenz

Dieses Projekt ist unter der MIT-Lizenz lizenziert - siehe [LICENSE](LICENSE) Datei für Details.

---

## 💬 Support

### Community-Support

- **GitHub Issues:** [Issue Tracker](https://github.com/Thomas-Heisig/chat_system/issues)
- **Discussions:** [GitHub Discussions](https://github.com/Thomas-Heisig/chat_system/discussions)
- **Documentation:** [docs/](docs/)

### Problemberichterstattung

Wenn Sie ein Problem finden:

1. **Suchen** Sie nach existierenden Issues
2. **Sammeln** Sie Informationen:
   - System-Details (OS, Python-Version)
   - Fehler-Logs
   - Reproduktionsschritte
3. **Erstellen** Sie ein detailliertes Issue
4. **Markieren** Sie mit passenden Labels

### Feature-Anfragen

Neue Feature-Ideen?

1. **Diskutieren** Sie in GitHub Discussions
2. **Erstellen** Sie ein Feature Request Issue
3. **Beschreiben** Sie Ihren Use Case
4. **Vorschlagen** Sie eine Implementation

---

## 🙏 Danksagungen

### Haupttechnologien
- [FastAPI](https://fastapi.tiangolo.com/) - Modern Web Framework
- [SQLAlchemy](https://www.sqlalchemy.org/) - SQL Toolkit
- [LangChain](https://python.langchain.com/) - LLM Framework
- [ChromaDB](https://www.trychroma.com/) - Vector Database

### Contributors
Danke an alle Contributors, die dieses Projekt möglich gemacht haben!

---

## 📊 Projekt-Status

### Aktuelle Version: 2.2.0

**Code-Qualität:** ⭐⭐⭐⭐⭐ (99.4% Verbesserung)  
**Test-Coverage:** ⭐⭐⭐☆☆ (11% - In Entwicklung)  
**Dokumentation:** ⭐⭐⭐⭐⭐ (50+ Dokumente)  
**Security:** ⭐⭐⭐⭐⭐ (Enterprise-Ready)  
**Performance:** ⭐⭐⭐⭐☆ (Optimiert)

### Roadmap

Siehe [ROADMAP.md](ROADMAP.md) für zukünftige Pläne:
- [ ] Database Read Replicas
- [ ] GraphQL API Gateway
- [ ] gRPC Service-to-Service Communication
- [ ] Event Sourcing
- [ ] Multi-Tenancy Support
- [ ] Mobile App (React Native/Flutter)
- [ ] Desktop App (Electron)

---

## 🌟 Star-History

Wenn Ihnen dieses Projekt gefällt, geben Sie ihm einen ⭐ auf GitHub!

---

**Gebaut mit ❤️ für die Developer-Community**

[⬆ Zurück nach oben](#universal-chat-system---deutsche-dokumentation)
